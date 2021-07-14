
from common.common import *


class Survey:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db
        self.batch = self.db.batch()
        self.team_gsid = ''
        self.project_gsid = ''
        self.gsid = ''
        self.translate_df = None
        self.respondent_df = None
        self.spreadsheet = None
        self.template_id = '17t0kixc-0AJy2YBFUtNcKiCJafmck5BZ1TGaIxTTPNU'
        self.info_dict = {}
        self.survey_dict = {}
        self.module_dict = {}
        self.reference_key_list = []
        self.interviewer_list = []
        self.type = 'survey'

    from common.create import create, link_url
    from .choice import create_choice_list, choice_import_to_df
    from common.db_operation import get_team_dict, get_project_dict, get_survey_module_dict, get_survey_dict, \
        get_response_dict, batch_set_by_interviewer, get_survey_dict_from_field
    from .expression import reformat_expression
    from .question import get_survey_question_list, get_recode_question_list, get_survey_module_question_list, \
        to_formatted_text_list
    from common.check_valid import check_survey_valid, check_survey_field_value_not_occupied
    from common.translate import get_translate_df, translate
    from .update_subprocess import update_respondent_list, update_survey_question, update_reference_list

    def update(self, gsid):
        try:
            # S_ 連接 spreadsheet
            gsheets = self.gsheets
            self.gsid = gsid
            spreadsheet = gsheets.open_by_key(gsid)
            self.spreadsheet = spreadsheet

            # S_ 更新說明頁
            self.link_url()

            # S_ 取得翻譯表
            self.get_translate_df()

            # S_ 提取資訊頁
            survey_info = spreadsheet.worksheet_by_title('問卷資訊') \
                .get_values(start='C2', end='C12', include_all=True)
            survey_info = [v[0] for v in survey_info]
            survey_info.insert(0, gsid)

            keys = ['surveyId', 'surveyName', 'customSurveyId',
                    'customProjectId', 'customTeamId', 'surveyWorksheetName', 'respondentWorksheetName',
                    'samplingWithinHousehold', 'visitReport', 'housingType', 'interviewReport', 'recode']

            info_dict = dict(zip(keys, survey_info))
            self.info_dict = info_dict

            # S_ 檢查輸入的內容是否符合格式
            check_result = self.check_survey_valid()
            if check_result:
                return check_result

            # S_ survey_dict 架構
            self.survey_dict = {
                'teamId': self.team_gsid,
                'projectId': self.project_gsid,
                'surveyId': gsid,
                'customSurveyId': info_dict['customSurveyId'],
                'surveyName': info_dict['surveyName'],
                'module': defaultdict(dict),
                'moduleInfo': self.module_dict,
            }

            # S_ 更新受訪者列表
            self.update_respondent_list()

            # S_ 更新所有問卷相關題目
            self.update_survey_question()

            # S_ 更新參考作答列表
            self.update_reference_list()

            # S_ 確認沒問題再一起 commit
            self.batch.commit()

        except:
            return '更新問卷設定失敗!'

        return '更新問卷設定成功!'
