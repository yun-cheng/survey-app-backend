
from common import *


class Survey:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db
        self.team_gsid = ''
        self.project_gsid = ''
        self.gsid = ''
        self.translate_df = None
        self.spreadsheet = None

    def create(self, email):
        # try:
        # S_1-1 連接模板
        template_id = '17t0kixc-0AJy2YBFUtNcKiCJafmck5BZ1TGaIxTTPNU'
        template_spreadsheet = self.gsheets.open_by_key(template_id)

        # S_1-2 創立新的 spreadsheet
        spreadsheet = self.gsheets.create('新建立之問卷設定檔(可自訂名稱)')
        gsid = spreadsheet.id

        # S_1-3 從模板複製到新創立的 spreadsheet
        for i in range(8):
            worksheet = template_spreadsheet.worksheet('index', i).copy_to(gsid)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # S_1-4 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # S_1-5 '更新此問卷設定' 連結
        worksheet = spreadsheet.worksheet_by_title('說明')
        update_url = f'{main_url}?action=update&on=survey&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此問卷設定")')

        # S_1-6 '更新此問卷紀錄' 連結
        update_result_url = f'{main_url}?action=update&on=survey_response&gsid={gsid}'
        worksheet.update_value('A4', f'=HYPERLINK("{update_result_url}", "更新此問卷紀錄")')

        # S_1-7 '刪除此問卷設定' 連結
        delete_url = f'{main_url}?action=delete&on=survey&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "刪除此問卷設定")')

        # S_1-8 '刪除此問卷紀錄' 連結
        delete_result_url = f'{main_url}?action=delete&on=survey_response&gsid={gsid}'
        worksheet.update_value('A6', f'=HYPERLINK("{delete_result_url}", "刪除此問卷紀錄")')

        # S_1-9 設定分享權限
        email_message = '新建立之問卷設定檔'
        spreadsheet.share(email, 'writer', emailMessage=email_message)
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
        # NOTE 轉移所有權
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        # except:
        #     return '建立問卷失敗!'

        return f'新建立之問卷設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'

    def update(self, gsid):
        # try:
        # S_1-1 連接 spreadsheet
        gsheets = self.gsheets
        db = self.db
        self.gsid = gsid
        spreadsheet = gsheets.open_by_key(gsid)
        self.spreadsheet = spreadsheet

        # S_1-2 提取資訊
        survey_info = spreadsheet.worksheet_by_title('問卷資訊') \
            .get_values(start='C2', end='C9', include_all=True)

        survey_info_dict = {
            'surveyId': gsid,
            'surveyName': survey_info[0][0],
            'customSurveyId': survey_info[1][0],
            'customProjectId': survey_info[2][0],
            'customTeamId': survey_info[3][0],
            'surveyWorksheetName': survey_info[4][0],
            'respondentWorksheetName': survey_info[5][0],
            'customInHouseSamplingId': survey_info[6][0],
            'customVisitAddressId': survey_info[7][0]
        }

        survey_dict = {}
        survey_dict['surveyId'] = gsid
        survey_dict['customSurveyId'] = survey_info_dict['customSurveyId']
        survey_dict['surveyName'] = survey_info_dict['surveyName']
        survey_dict['module'] = defaultdict(dict)

        # S_1-3 檢查輸入的內容是否符合格式
        # S_1-3-1 檢查是否為空
        skip_keys = ['customInHouseSamplingId', 'customVisitAddressId']
        for k, v in survey_info_dict.items():
            if k not in skip_keys and not v:
                return '問卷資訊不能為空!'

        # S_1-3-2 檢查連結的單位 ID、專案 ID、問卷模組 ID 是否存在
        team_gsid, team_missing = self.translate_custom_team_id(survey_info_dict['customTeamId'])
        project_gsid, project_missing = self.translate_custom_project_id(survey_info_dict['customProjectId'])
        visit_address_gsid, visit_address_missing = \
            self.translate_custom_survey_module_id(survey_info_dict['customVisitAddressId'])
        in_house_sampling_gsid, in_house_sampling_missing = \
            self.translate_custom_survey_module_id(survey_info_dict['customInHouseSamplingId'])

        if team_gsid and project_gsid:
            survey_dict['teamId'] = team_gsid
            survey_dict['projectId'] = project_gsid
        else:
            return f'{team_missing}{project_missing}'

        if survey_info_dict['customVisitAddressId'] and visit_address_missing:
            return visit_address_missing
        if survey_info_dict['customInHouseSamplingId'] and in_house_sampling_missing:
            return in_house_sampling_missing

        # S_1-3-3 檢查是否為重複的問卷 ID 或名稱
        id_occupied = self.check_field_value_not_occupied('customSurveyId', survey_info_dict['customSurveyId'])
        name_occupied = self.check_field_value_not_occupied('surveyName', survey_info_dict['surveyName'])

        if id_occupied or name_occupied:
            return f'{id_occupied}{name_occupied}'

        # S_3 更新 Firestore
        batch = db.batch()

        # S_3-1 更新 Firestore: interviewerRespondentList/{interviewerId_surveyId}
        # TAG Firestore DELETE, SET
        # S_3-1-1 移除此問卷的所有受訪者列表
        remove_respondent_list_docs = self.db.collection('interviewerRespondentList') \
            .where('surveyId', '==', gsid).stream()

        for doc in remove_respondent_list_docs:
            batch.delete(doc.reference)

        # S_3-1-2 新增此問卷的受訪者列表
        # EXAMPLE
        respondent_list_dict = {
            'surveyId': gsid,
            'projectId': project_gsid,
            'teamId': team_gsid,
            'respondentList': []
        }

        respondent_list_df = get_worksheet_df(spreadsheet, worksheet_title=survey_info_dict['respondentWorksheetName'], end='E')
        respondent_list_df.columns = ['interviewerId', 'respondentId', 'countyTown', 'village', 'remainAddress']
        interviewer_list = respondent_list_df.interviewerId.unique()
        respondent_list_df.index = respondent_list_df['respondentId']
        survey_dict['interviewerList'] = list(interviewer_list)

        for interviewer_id in interviewer_list:
            interviewer_respondent_df = respondent_list_df[respondent_list_df.interviewerId == interviewer_id]
            interviewer_respondent_df = interviewer_respondent_df.drop(columns='interviewerId')
            respondent_list_dict['interviewerId'] = interviewer_id
            respondent_list_dict['respondentList'] = interviewer_respondent_df.to_dict('records')

            respondent_list_ref = db.document('interviewerRespondentList', f'{interviewer_id}_{gsid}')
            batch.set(respondent_list_ref, respondent_list_dict)

        # S_3-2 更新 Firestore: survey/{surveyId}
        # TAG Firestore SET
        # EXAMPLE
        '''
        survey / {surveyId} / {
            surveyId: '17t0kixc-0AJy2YBFUtNcKiCJafmck5BZ1TGaIxTTPNU',
            customSurveyId: 'demo_survey_id',
            surveyName: '範例問卷名稱',
            projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
            teamId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8',
            module: {
                visitAddressId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                inHouseSamplingId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
            },
            interviewerList: ['interviewer001', 'interviewer002', ...],
            questionList: [{
                serialNumber: 0,
                questionId : 'A1',
                questionBody: 'Question 1',
                questionNote: '',
                questionType: 'single',
                ...
            }, ...]
        }
        '''
        # S_3-2-1 提取問卷、問卷模組
        # NOTE
        self.get_translate_df()

        survey_dict['questionList'], \
        survey_dict['initialAnswerList'], \
        survey_dict['initialAnswerStatusList'] = \
            self.get_survey_question_list(spreadsheet, survey_info_dict['surveyWorksheetName'])

        if visit_address_gsid:
            survey_dict['module']['visitAddress']['questionList'], \
            survey_dict['module']['visitAddress']['initialAnswerList'], \
            survey_dict['module']['visitAddress']['initialAnswerStatusList'] = \
                self.get_survey_module_question_list(visit_address_gsid)

        if in_house_sampling_gsid:
            survey_dict['module']['inHouseSampling']['questionList'], \
            survey_dict['module']['inHouseSampling']['initialAnswerList'], \
            survey_dict['module']['inHouseSampling']['initialAnswerStatusList'] = \
                self.get_survey_module_question_list(in_house_sampling_gsid)

        # S_3-2-2 更新
        survey_ref = db.document('survey', gsid)
        batch.set(survey_ref, survey_dict)

        batch.commit()

        # except:
        #     return '更新問卷設定失敗!'

        return '更新問卷設定成功!'

    def translate_custom_team_id(self, custom_team_id):
        team_query = self.db.collection('team') \
            .where('customTeamId', '==', custom_team_id)
        team_dict = team_query.query_to_dict(first=True)

        if team_dict:
            self.team_gsid = team_dict['teamId']
            return self.team_gsid, ''
        else:
            return '', f'找不到連結的單位 ID: {custom_team_id}！'

    def translate_custom_project_id(self, custom_project_id):
        project_query = self.db.collection('project') \
            .where('customProjectId', '==', custom_project_id) \
            .where('teamId', '==', self.team_gsid)
        project_dict = project_query.query_to_dict(first=True)

        if project_dict:
            self.project_gsid = project_dict['projectId']
            return self.project_gsid, ''
        else:
            return '', f'找不到連結的專案 ID: {custom_project_id}！'

    def translate_custom_survey_module_id(self, custom_survey_module_id):
        survey_module_query = self.db.collection('surveyModule') \
            .where('customSurveyModuleId', '==', custom_survey_module_id) \
            .where('projectId', '==', self.project_gsid)
        survey_module_dict = survey_module_query.query_to_dict(first=True)

        if survey_module_dict:
            return survey_module_dict['surveyModuleId'], ''
        else:
            return '', f'找不到連結的問卷模組 ID: {custom_survey_module_id}！'

    def check_field_value_not_occupied(self, field, field_value):
        check_query = self.db.collection('survey') \
            .where('projectId', '==', self.project_gsid) \
            .where(field, '==', field_value)
        check_dict = check_query.query_to_dict(first=True)

        if check_dict and check_dict['surveyId'] != self.gsid:
            return f'同專案下，已有 {field_value}，請更換名稱！'
        else:
            return ''

    def get_translate_df(self):
        spreadsheet = self.gsheets.open_by_key('1nmZ2OVD3tfPoJSVjJK_jlHRrY3NYADCi7yv2GY0VV28')
        translate_df = get_worksheet_df(spreadsheet, worksheet_title='命名對照')
        translate_df = translate_df.iloc[:, 0:3]
        translate_df.columns = ['appear', 'chinese', 'english']
        translate_df['re'] = translate_df.chinese.str.match('.+_$')

        self.translate_df = translate_df

    def get_survey_question_list(self, spreadsheet, survey_worksheet_name):
        translate_df = self.translate_df

        question_list_df = get_worksheet_df(spreadsheet, worksheet_title=survey_worksheet_name)

        question_list_df.columns = translate_cols(question_list_df.columns,
                                                  translate_df[translate_df.appear == 'survey_cols'])

        # NOTE recode
        question_type_recoder = {
            '單選': 'single',
            '多選': 'multiple',
            '下拉單選': 'popupSingle',
            '下拉多選': 'popupMultiple',
            '文字': 'text',
            '數字': 'number',
            '日期': 'date',
            '時間': 'time',
            '純說明': 'description',
        }
        question_list_df['questionType'] = question_list_df.questionType.map(question_type_recoder)

        question_list_df['hideQuestionId'] = question_list_df.hideQuestionId == '1'
        question_list_df['pageNumber'] = question_list_df.pageNumber.map(int)
        question_list_df['serialNumber'] = question_list_df.index

        # S_ 驗證 questionId 唯一
        assert(all(question_list_df.questionId != ''))
        assert(len(question_list_df.questionId) == question_list_df.questionId.nunique())

        # NOTE
        # TODO question_layer
        # TODO 驗證 choiceId 唯一
        question_list_df['choiceList'], \
        question_list_df['hasSpecialAnswer'], \
        question_list_df['specialAnswerList'], \
        initialAnswerList, initialAnswerStatusList = zip(*question_list_df.apply(
            self.create_choice_list, spreadsheet=spreadsheet, axis=1))

        survey_question_list = question_list_df.to_dict('records')
        initialAnswerList = {i['questionId']: i for i in initialAnswerList}
        initialAnswerStatusList = {i['questionId']: i for i in initialAnswerStatusList}

        # S_ showQuestion, validateAnswer
        question_list_df['showQuestion'] = question_list_df.apply(reformat_expression, column='showQuestion', axis=1)
        question_list_df['validateAnswer'] = question_list_df.apply(reformat_expression, column='validateAnswer', axis=1)

        return survey_question_list, initialAnswerList, initialAnswerStatusList

    def choice_import_to_df(self, spreadsheet, choice_import):
        translate_df = self.translate_df

        choice_import_df = get_worksheet_df(spreadsheet, worksheet_title=choice_import)

        choice_import_df.columns = translate_cols(choice_import_df.columns,
                                                  translate_df[translate_df.appear == 'choice_cols'])

        choice_import_df['serialNumber'] = choice_import_df.index
        choice_import_df.index = choice_import_df.index.map(str)

        if 'asNote' in choice_import_df.columns:
            choice_import_df['asNote'] = choice_import_df.asNote == '1'
        else:
            choice_import_df['asNote'] = False

        if 'asSingle' in choice_import_df.columns:
            choice_import_df['asSingle'] = choice_import_df.asSingle == '1'
        else:
            choice_import_df['asSingle'] = False

        if 'choiceGroup' not in choice_import_df.columns:
            choice_import_df['choiceGroup'] = ''

        if 'upperChoiceId' not in choice_import_df.columns:
            choice_import_df['upperChoiceId'] = ''

        return choice_import_df

    def get_survey_module_question_list(self, gsid):
        spreadsheet = self.gsheets.open_by_key(gsid)

        survey_worksheet_name = spreadsheet.worksheet_by_title('問卷模組資訊').get_value('C6')

        return self.get_survey_question_list(spreadsheet, survey_worksheet_name)

    def create_choice_list(self, row, spreadsheet):
        if row['questionType'] in ['single', 'multiple', 'popupSingle', 'popupMultiple']:

            if row['choice_import']:
                choice_import_df = self.choice_import_to_df(spreadsheet, row['choice_import'])
                choiceList = choice_import_df.to_dict('records')

            else:
                choice_df = choice_row_to_df(row, regex='choice_id_')
                choiceList = choice_df.to_dict('records')

        else:
            choiceList = []

        # H_ special answer
        special_answer_df = choice_row_to_df(row, regex='special_answer_')

        if not special_answer_df.empty:
            specialAnswerList = special_answer_df.to_dict('records')
            hasSpecialAnswer = True
        else:
            hasSpecialAnswer = False
            specialAnswerList = []

        # H_ answer, answerStatus
        if row['showQuestion'] == '':
            answerStatusType = 'unanswered'
        else:
            answerStatusType = 'hidden'

        answer = {
            'questionId': row['questionId'],
            'serialNumber': row['serialNumber'],
            'answerBody': '',
            'noteMap': {}
        }

        answer_status = {
            'questionId': row['questionId'],
            'serialNumber': row['serialNumber'],
            'answerStatusType': answerStatusType,
            'noteMap': {}
        }

        return choiceList, hasSpecialAnswer, specialAnswerList, answer, answer_status


def translate_cols(cols, translate_df):
    new_cols = []
    for col in cols:
        match_translate = translate_df.loc[translate_df.chinese == col, 'english']
        if len(match_translate) > 0:
            new_cols.append(match_translate.iloc[0])
            continue

        match_replace_df = translate_df[translate_df.re]

        for i, row in match_replace_df.iterrows():
            col = re.sub(f'^{row.chinese}', row.english, col)

        new_cols.append(col)

    return new_cols


def force_to_str_list(string):
    if string:
        possible_list = ast.literal_eval(string)
        if type(possible_list) == int:
            possible_list = [possible_list]
        str_list = [str(e) for e in possible_list]

        return str_list
    else:
        return []


def choice_row_to_df(row, regex):
    choice_series = row.filter(regex=regex)
    choice_df = pd.DataFrame({
        'choiceId': choice_series.index,
        'choiceBody': choice_series,
    })

    choice_df['choiceId'] = choice_df.choiceId.str.replace(regex, '')

    choice_df.drop(choice_df[choice_df.choiceBody == ''].index, inplace=True)

    choice_df.reset_index(drop=True, inplace=True)

    choice_df['serialNumber'] = choice_df.index
    choice_df.index = choice_df.index.map(str)

    choice_df['asNote'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_note'])), 'asNote'] = True

    choice_df['asSingle'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_single'])), 'asSingle'] = True

    choice_df['choiceGroup'] = ''
    choice_df['upperChoiceId'] = ''

    return choice_df


def reformat_expression(row, column):
    full_expression = row[column]
    # S_1 去空格
    full_expression = full_expression.replace(' ', '')
    # S_2 切開並保留分隔符號
    full_expression = re.split('(\||\&|\(|\))', full_expression)
    element_list = [i for i in full_expression if i != '']

    full_expression_body = ''
    expression_dict = {}
    letters = string.ascii_uppercase
    i = 0

    for element in element_list:
        if element in ['(', ')']:
            full_expression_body += element
        elif element in ['|', '&']:
            full_expression_body += element * 2
        else:
            split_element = re.split('(!=|==|>=|<=|>|<|notin|in|notcontainsany|containsany|'
                                     'notcontainsall|containsall|notcontains|contains|istype)', element)

            expression_id = letters[i]
            question_id = split_element[0]
            operator = split_element[1]
            value = split_element[2]

            if question_id == 'ANS':
                question_id = row['questionId']

            recorder = {
                '==': 'isEqualTo',
                '!=':'notEqualTo',
                '>=':'isGreaterThanOrEqualTo',
                '<=':'isLessThanOrEqualTo',
                '>':'isGreaterThan',
                '<':'isLessThan',
                'in':'isIn',
                'notin':'notIn',
                'contains':'contains',
                'notcontains':'notContains',
                'containsany':'containsAny',
                'notcontainsany':'notContainsAny',
                'containsall':'containsAll',
                'notcontainsall':'notContainsAll',
                'istype': 'isType'
            }
            operator = recorder.get(operator, '')

            full_expression_body += expression_id
            i += 1

            expression_dict[expression_id] = {
                'field': question_id,
                operator: ast.literal_eval(value)  # TODO try catch
            }

    result = {
        'fullExpressionBody': full_expression_body,
        'expressionMap': expression_dict
    }

    return result


