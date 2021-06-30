
from common.common import *


class SurveyModule:
    def __init__(self, gsheets, db, module=''):
        self.gsheets = gsheets
        self.db = db
        self.module = module

    def create(self, email):
        # try:
        # S_1-1 連接模板
        template_id = '1wK5BmSYdzb8Rsju4SKYWJHQSw8Iij8-nHYmfE0lFjSI'
        module_str = ''
        if self.module == 'recode':
            template_id = '11AXqaKcnjuPHmU5IsFkq-VY4svFTJLO8BHwf9yIlgck'
            module_str = 'recode_'
        elif self.module == 'samplingWithinHousehold':
            template_id = '1C1BGmmUvCH0TsZ5sFT5UqG21TKaXX2pkUuPPKCzf8C0'
            module_str = 'samplingWithinHousehold_'

        template_spreadsheet = self.gsheets.open_by_key(template_id)

        # S_1-2 創立新的 spreadsheet
        spreadsheet = self.gsheets.create('新建立之問卷模組設定檔(可自訂名稱)')
        gsid = spreadsheet.id

        # S_1-3 從模板複製到新創立的 spreadsheet
        for template_worksheet in template_spreadsheet.worksheets():
            worksheet = template_worksheet.copy_to(gsid)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # S_1-4 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # S_1-5 '更新此問卷模組設定' 連結
        worksheet = spreadsheet.worksheet_by_title('說明')
        update_url = f'{main_url}?action=update&on={module_str}module&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "連結此問卷模組至專案")')

        # S_1-7 '刪除此問卷模組設定' 連結
        delete_url = f'{main_url}?action=delete&on={module_str}module&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "取消連結此問卷模組至專案")')

        # S_1-9 設定分享權限
        email_message = '新建立之問卷模組設定檔'
        spreadsheet.share(email, 'writer', emailMessage=email_message)
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
        # NOTE 轉移所有權
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        # except:
        #     return '建立問卷模組失敗!'

        return f'新建立之問卷模組設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'

    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            gsheets = self.gsheets
            db = self.db
            spreadsheet = gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            survey_module_info = spreadsheet.worksheet_by_title('問卷模組資訊') \
                .get_values(start='C2', end='C8', include_all=True)
            survey_module_info = [v[0] for v in survey_module_info]
            survey_module_info.insert(0, gsid)

            keys = ['surveyModuleId', 'surveyModuleName', 'customSurveyModuleId',
                    'customProjectId', 'customTeamId', 'surveyModuleWorksheetName']

            if self.module == 'samplingWithinHousehold':
                keys.append('sampling_rule')

            survey_module_info_dict = dict(zip(keys, survey_module_info))

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in survey_module_info_dict.items():
                if not v:
                    return '問卷模組資訊不能為空!'

            # S_1-3-2 檢查連結的單位 ID、專案 ID、問卷模組模組 ID 是否存在
            team_query = db.collection('team') \
                .where('customTeamId', '==', survey_module_info_dict['customTeamId'])
            team_dict = team_query.query_to_dict(first=True)

            if team_dict:
                team_gsid = team_dict['teamId']
                survey_module_info_dict['teamId'] = team_gsid
                survey_module_info_dict.pop('customTeamId')
            else:
                return '找不到連結的單位 ID！'

            project_query = db.collection('project') \
                .where('customProjectId', '==', survey_module_info_dict['customProjectId'])\
                .where('teamId', '==', team_gsid)
            project_query_dict = project_query.query_to_dict(first=True)

            if project_query_dict:
                project_gsid = project_query_dict['projectId']
                survey_module_info_dict['projectId'] = project_gsid
                survey_module_info_dict.pop('customProjectId')
            else:
                return '找不到連結的專案 ID！'

            # S_1-3-3 檢查是否為重複的問卷模組 ID 或名稱
            survey_module_query = db.collection('surveyModule') \
                .where('projectId', '==', project_gsid) \
                .where('teamId', '==', team_gsid)\
                .where('surveyModuleName', '==', survey_module_info_dict['surveyModuleName'])
            survey_module_query_dict = survey_module_query.query_to_dict(first=True)

            if survey_module_query_dict and survey_module_query_dict['surveyModuleId'] != gsid:
                return '同專案下，問卷模組名稱重複，請輸入其他名稱！'

            survey_module_query = db.collection('surveyModule') \
                .where('projectId', '==', project_gsid) \
                .where('teamId', '==', team_gsid) \
                .where('customSurveyModuleId', '==', survey_module_info_dict['customSurveyModuleId'])
            survey_module_query_dict = survey_module_query.query_to_dict(first=True)

            if survey_module_query_dict and survey_module_query_dict['surveyModuleId'] != gsid:
                return '同專案下，自訂問卷模組 ID 重複，請輸入其他 ID！'

            # S_2 更新 Firestore
            batch = db.batch()

            # S_2-1 更新 Firestore: survey/{surveyId}
            # TAG Firestore SET
            # EXAMPLE
            survey_module_ref = db.document('surveyModule', gsid)
            batch.set(survey_module_ref, survey_module_info_dict)

            batch.commit()
        except:
            return '連結問卷模組失敗!'

        return '連結問卷模組成功!'
