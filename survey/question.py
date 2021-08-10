from common.common import *


def get_survey_question_list(self, spreadsheet, survey_worksheet_name, module):
    question_list_df = get_worksheet_df(spreadsheet, worksheet_title=survey_worksheet_name)

    self.set_where(2, '翻譯欄位名稱與題目類型')
    question_list_df.columns = self.translate(question_list_df.columns.to_series(), '問卷')
    question_list_df['questionType'] = self.translate(question_list_df.questionType, '題目類型')

    # S_ 處理表格題組
    if 'tableId' in question_list_df.columns:
        self.set_where(2, '初步處理表格題組')
        question_list_df = self.process_table_question(question_list_df)
        question_list_df['rowId'] = question_list_df.rowId.fillna(-1).astype(int)
    else:
        question_list_df['tableId'] = ''
        question_list_df['rowId'] = -1

    # S_ questionBody
    self.set_where(2, '處理題目內容')
    question_list_df['questionBody'] = question_list_df.apply(
        self.to_formatted_text_list,
        current_module_type=module, axis=1)

    # S_ choiceList, hasSpecialAnswer, answerStatusType
    # TODO question_layer
    # TODO 驗證 choiceId 唯一
    # HIGHLIGHT 用 pd.DataFrame(結果.to_list()) 可避免當 question_list_df 只有 1 row 時會出錯
    self.set_where(2, '處理選項與特殊作答')
    question_list_df[['choiceList', 'hasSpecialAnswer', 'answerStatusType']] = \
        pd.DataFrame(question_list_df.apply(
            self.create_choice_list, spreadsheet=spreadsheet, axis=1).to_list())

    # S_ showQuestion, validateAnswer
    self.set_where(2, '處理題目出現條件')
    question_list_df['showQuestion'] = question_list_df.apply(
        self.reformat_expression, column='showQuestion', axis=1)
    self.set_where(2, '處理檢驗答案')
    question_list_df['validateAnswer'] = question_list_df.apply(
        self.reformat_expression, column='validateAnswer', axis=1)

    # S_ pageNumber
    self.set_where(2, '提取頁數')
    question_list_df['pageNumber'] = question_list_df.pageNumber.map(int)

    # S_ other columns
    self.set_where(2, '處理其他')
    question_list_df['stringBody'] = ''
    question_list_df['hideQuestionId'] = question_list_df.hideQuestionId == '1'
    question_list_df['serialNumber'] = question_list_df.index
    question_list_df['recodeNeeded'] = False

    # S_ assert
    if all(question_list_df.pageNumber != 0):
        self.set_where(2, '檢查頁數有第 0 頁', error=True)
    if any(question_list_df.questionId == ''):
        self.set_where(2, '檢查題號不為空', error=True)
    if len(question_list_df.questionId) != question_list_df.questionId.nunique():
        self.set_where(2, '檢查題號不重複', error=True)

    # S_
    question_list_df = question_list_df.filter(regex='^(?!choiceId_|specialAnswer_|choice_).*', axis=1)

    survey_question_list = question_list_df.drop(['answerStatusType'], axis=1).to_dict('records')

    question_list_df.index = question_list_df.questionId
    answer_list = {questionId: {} for questionId in question_list_df.questionId}
    answer_status_list = question_list_df[['answerStatusType']].to_dict('index')

    # S_ 查址模組若有設定中止訪問題號，需新增預設答案
    if module == 'visitReport':
        answer_list['break_interview'] = {
            'type': 'string',
            'withNote': False,
            'stringValue': '0',
        }

    return {
        'questionList': survey_question_list,
        'initialAnswerList': answer_list,
        'initialAnswerStatusList': answer_status_list,
    }


def get_recode_question_list(self, spreadsheet, survey_worksheet_name):
    question_list_df = get_worksheet_df(spreadsheet, worksheet_title=survey_worksheet_name)

    self.set_where(2, '翻譯欄位名稱與題目類型')
    question_list_df.columns = self.translate(question_list_df.columns.to_series(), '問卷')

    # S_ pageNumber
    self.set_where(2, '提取頁數')
    question_list_df['pageNumber'] = question_list_df.pageNumber.map(int)

    # S_ validateAnswer
    self.set_where(2, '處理檢驗答案')
    question_list_df['validateAnswer'] = question_list_df.apply(
        self.reformat_expression, column='validateAnswer', axis=1)

    # S_ other columns
    self.set_where(2, '提取一般欄位')
    question_list_df[['questionNote', 'upperQuestionId']] = '', ''
    question_list_df['tableId'] = ''
    question_list_df['rowId'] = -1
    question_list_df['questionBody'] = [[{'type': 'string', 'stringBody': ''}]] * len(question_list_df)
    question_list_df['stringBody'] = ''
    question_list_df[['hideQuestionId', 'hasSpecialAnswer']] = False, False
    question_list_df['serialNumber'] = question_list_df.index
    question_list_df['recodeNeeded'] = question_list_df.recodeNeeded == '1'
    question_list_df['questionType'] = question_list_df.recodeNeeded.apply(
        lambda x: 'number' if x else 'description')
    question_list_df['answerStatusType'] = question_list_df.recodeNeeded.apply(
        lambda x: 'unanswered' if x else 'answered')
    question_list_df['choiceList'] = [[]] * len(question_list_df)
    question_list_df['showQuestion'] = [{'fullExpressionBody': '', 'expressionMap': {}}] * len(question_list_df)

    # S_ assert
    if any(question_list_df.questionId == ''):
        self.set_where(2, '檢查題目編號不為空', error=True)
    if len(question_list_df.questionId) != question_list_df.questionId.nunique():
        self.set_where(2, '檢查題目編號不重複', error=True)

    # S_
    survey_question_list = question_list_df.to_dict('records')

    question_list_df.index = question_list_df.questionId
    answer_list = {questionId: {} for questionId in question_list_df.questionId}
    answer_status_list = question_list_df[['answerStatusType']].to_dict('index')

    return {
        'questionList': survey_question_list,
        'initialAnswerList': answer_list,
        'initialAnswerStatusList': answer_status_list,
    }


def get_survey_module_question_list(self, gsid, module):
    spreadsheet = self.gsheets.open_by_key(gsid)

    survey_worksheet_name = self.module_dict[module]['surveyModuleWorksheetName']

    self.set_where(1, f'提取{survey_worksheet_name}分頁資料表')

    if module == 'recode':
        return self.get_recode_question_list(spreadsheet, survey_worksheet_name)
    else:
        return self.get_survey_question_list(spreadsheet, survey_worksheet_name, module)


def to_formatted_text_list(self, row, current_module_type):
    try:
        pattern = '(\\$\\{.+\\})'
        split_list = re.split(pattern, row['questionBody'])

        keys = ['questionId', 'moduleType', 'surveyId']

        text_list = []
        for x in split_list:
            extract_str = re.findall('(?<=^\\${).+(?=}$)', x)
            if extract_str:
                extract_list = extract_str[0].split('.')
                ref_dict = dict(zip(keys, extract_list[::-1]))
                result_dict = {
                    'questionId': ref_dict['questionId']
                }

                # H_ surveyId
                # S_ 如果有出現 surveyId
                if 'surveyId' in ref_dict:
                    # S_ 如果和當前 survey 的 customSurveyId 一樣
                    if ref_dict['surveyId'] == self.survey_dict['customSurveyId']:
                        survey_dict = self.survey_dict
                    else:
                        survey_dict = self.get_survey_dict(ref_dict['surveyId'])
                else:
                    survey_dict = self.survey_dict

                # S_ 若找不到則直接當成 surveyId
                result_dict['surveyId'] = survey_dict.get('surveyId', ref_dict.get('surveyId', ''))

                # H_ moduleType
                # S_ 如果有出現 moduleType
                if 'moduleType' in ref_dict:
                    result_dict['moduleType'] = self.translate(ref_dict['moduleType'], '模組類型')
                else:
                    result_dict['moduleType'] = current_module_type

                text_list.append({
                    'type': 'referenceKey',
                    'referenceKey': result_dict
                })
                self.reference_key_list.append(result_dict)

            else:
                text_list.append({
                    'type': 'string',
                    'stringBody': x
                })

        return text_list

    except:
        self.set_where(3, f'題號 {row["questionId"]} 的 {row["questionBody"]}', error=True)
