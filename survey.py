
from common import *


class Survey:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

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
        try:
            # S_1-1 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            survey_info = spreadsheet.worksheet_by_title('問卷資訊') \
                .get_values(start='C2', end='C9', include_all=True)

            survey_info_dict = {
                'surveyId': gsid,
                'surveyName': survey_info[0][0],
                'customSurveyId': survey_info[1][0],
                'customProjectId': survey_info[2][0],
                'customUnitId': survey_info[3][0],
                'customInHouseSamplingId': survey_info[6][0],
                'customVisitAddressId': survey_info[7][0],
                'surveyType': 'main',
                'module': {}
            }
            survey_worksheet_name = survey_info[4][0]
            respondent_worksheet_name = survey_info[5][0]

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            skip_keys = ['customInHouseSamplingId', 'customVisitAddressId', 'module']
            for k, v in survey_info_dict.items():
                if k not in skip_keys and not v:
                    return '問卷資訊不能為空!'

            if not survey_worksheet_name or not respondent_worksheet_name:
                return '問卷資訊不能為空!'

            # S_1-3-2 檢查連結的單位 ID、專案 ID、問卷模組 ID 是否存在
            unit_query = self.db.collection('unit') \
                .where('customUnitId', '==', survey_info_dict['customUnitId'])
            unit_dict = unit_query.query_to_dict(first=True)

            if unit_dict:
                unit_gsid = unit_dict['unitId']
                survey_info_dict['unitId'] = unit_gsid
                survey_info_dict.pop('customUnitId')
            else:
                return '找不到連結的單位 ID！'

            project_query = self.db.collection('project') \
                .where('customProjectId', '==', survey_info_dict['customProjectId'])\
                .where('unitId', '==', unit_gsid)
            project_query_dict = project_query.query_to_dict(first=True)

            if project_query_dict:
                project_gsid = project_query_dict['projectId']
                survey_info_dict['projectId'] = project_gsid
                survey_info_dict.pop('customProjectId')
            else:
                return '找不到連結的專案 ID！'

            if survey_info_dict['customVisitAddressId']:
                survey_module_query = self.db.collection('survey') \
                    .where('customSurveyId', '==', survey_info_dict['customVisitAddressId']) \
                    .where('projectId', '==', project_gsid)
                survey_module_query_dict = survey_module_query.query_to_dict(first=True)

                if survey_module_query_dict:
                    survey_info_dict['module']['visitAddressId'] = survey_module_query_dict['surveyId']
                    survey_info_dict.pop('customVisitAddressId')
                else:
                    return '找不到連結的查址問卷模組 ID！'

            if survey_info_dict['customInHouseSamplingId']:
                survey_module_query = self.db.collection('survey') \
                    .where('customSurveyId', '==', survey_info_dict['customInHouseSamplingId']) \
                    .where('projectId', '==', project_gsid)
                survey_module_query_dict = survey_module_query.query_to_dict(first=True)

                if survey_module_query_dict:
                    survey_info_dict['module']['inHouseSamplingId'] = survey_module_query_dict['surveyId']
                    survey_info_dict.pop('customInHouseSamplingId')
                else:
                    return '找不到連結的戶中抽樣問卷模組 ID！'

            # S_1-3-3 檢查是否為重複的問卷 ID 或名稱
            survey_query = self.db.collection('survey') \
                .where('projectId', '==', project_gsid) \
                .where('unitId', '==', unit_gsid)\
                .where('surveyName', '==', survey_info_dict['surveyName'])
            survey_query_dict = survey_query.query_to_dict(first=True)

            if survey_query_dict:
                return '同專案下，問卷名稱重複，請輸入其他名稱！'

            survey_query = self.db.collection('survey') \
                .where('projectId', '==', project_gsid) \
                .where('unitId', '==', unit_gsid) \
                .where('customSurveyId', '==', survey_info_dict['customSurveyId'])
            survey_query_dict = survey_query.query_to_dict(first=True)

            if survey_query_dict:
                return '同專案下，自訂問卷 ID 重複，請輸入其他 ID！'

            # S_2 更新 Firestore
            batch = self.db.batch()

            # S_2-1 更新 Firestore: survey/{surveyId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            survey / {surveyId} / {
                surveyId: '17t0kixc-0AJy2YBFUtNcKiCJafmck5BZ1TGaIxTTPNU',
                customSurveyId: 'demo_survey_id',
                surveyName: '範例問卷名稱',
                projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                unitId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8',
                surveyType: 'main',
                module: {
                    visitAddressId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                    inHouseSamplingId: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                }
            }
            '''
            survey_ref = self.db.document('survey', gsid)
            batch.set(survey_ref, survey_info_dict)

            # S_2-2 更新 Firestore: interviewerSurveyList/{interviewerId_projectId}
            # S_2-3 更新 Firestore: interviewerRespondentList/{interviewerId_surveyId}
            # TAG Firestore UPDATE
            survey_list_dict = {
                'projectId': project_gsid,
                'unitId': unit_gsid,
                'surveyList': {
                    gsid: {
                        'surveyId': gsid,
                        'surveyName': survey_info_dict['surveyName'],
                    }
                }
            }

            respondent_list_dict = {
                'surveyId': gsid,
                'projectId': project_gsid,
                'unitId': unit_gsid,
                'respondentList': {}
            }

            respondent_list_df = get_worksheet_df(spreadsheet, worksheet_title=respondent_worksheet_name, end='E')
            respondent_list_df.columns = ['interviewerId', 'respondentId', 'countyTown', 'village', 'remainAddress']
            interviewer_list = respondent_list_df.interviewerId.unique()
            respondent_list_df.index = respondent_list_df['respondentId']

            for interviewer_id in interviewer_list:
                survey_list_dict['interviewerId'] = interviewer_id

                survey_list_ref = self.db.document('interviewerSurveyList', f'{interviewer_id}_{project_gsid}')
                batch.set(survey_list_ref, survey_list_dict, merge=True)

                interviewer_respondent_df = respondent_list_df[respondent_list_df.interviewerId == interviewer_id]
                interviewer_respondent_df.drop(columns='interviewerId', inplace=True)
                respondent_list_dict['interviewerId'] = interviewer_id
                respondent_list_dict['respondentList'] = interviewer_respondent_df.to_dict(orient='index')

                respondent_list_ref = self.db.document('interviewerRespondentList', f'{interviewer_id}_{gsid}')
                batch.set(respondent_list_ref, respondent_list_dict, merge=True)

            # S_2-4 更新 Firestore: surveyQuestionList/{surveyId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            surveyQuestionList / {surveyId} / {
                {questionId}: {
                    questionId: '1',
                    questionBody: 'Question 1',
                    answer: 'O'
                }
            }
            '''
            translate_spreadsheet = self.gsheets.open_by_key('1nmZ2OVD3tfPoJSVjJK_jlHRrY3NYADCi7yv2GY0VV28')
            survey_question_dict = get_survey_question_dict(spreadsheet, survey_worksheet_name, translate_spreadsheet)
            survey_question_ref = self.db.document('surveyQuestionList', gsid)
            batch.set(survey_question_ref, survey_question_dict)

            batch.commit()

        except:
            return '更新問卷設定失敗!'

        return '更新問卷設定成功!'


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

    choice_df['asNote'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_note'])), 'asNote'] = True

    choice_df['asSingle'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_single'])), 'asSingle'] = True

    choice_df['choiceGroup'] = ''
    choice_df['upperChoiceId'] = ''

    return choice_df


def choice_import_to_df(choice_import, spreadsheet, translate_df):
    choice_import_df = get_worksheet_df(spreadsheet, worksheet_title=choice_import)

    choice_import_df.columns = translate_cols(choice_import_df.columns,
                                              translate_df[translate_df.appear == 'choice_cols'])

    choice_import_df['serialNumber'] = choice_import_df.index

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


def get_survey_question_dict(spreadsheet, survey_worksheet_name, translate_spreadsheet):
    translate_df = get_worksheet_df(translate_spreadsheet, worksheet_title='命名對照')
    translate_df = translate_df.iloc[:, 0:3]
    translate_df.columns = ['appear', 'chinese', 'english']
    translate_df['re'] = translate_df.chinese.str.match('.+_$')

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

    # NOTE
    # TODO question_layer
    survey_question_dict = {}
    for i, row in question_list_df.iterrows():
        survey_question_dict[i] = row.filter(regex='^((?!_).)*$').to_dict()

        if row['questionType'] in ['single', 'multiple', 'popupSingle', 'popupMultiple']:

            if row['choice_import']:
                choice_import_df = choice_import_to_df(row['choice_import'], spreadsheet, translate_df)
                survey_question_dict[i]['choiceList'] = choice_import_df.to_dict(orient='index')

            else:
                choice_df = choice_row_to_df(row, regex='choice_id_')
                survey_question_dict[i]['choiceList'] = choice_df.to_dict(orient='index')

        # NOTE special answer
        special_answer_df = choice_row_to_df(row, regex='special_answer_')

        if not special_answer_df.empty:
            survey_question_dict[i]['specialAnswerList'] = special_answer_df.to_dict(orient='index')
            survey_question_dict[i]['hasSpecialAnswer'] = True
        else:
            survey_question_dict[i]['hasSpecialAnswer'] = False

    return survey_question_dict
