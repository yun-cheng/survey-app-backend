
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
        self.where = [''] * 5
        self.where_list = []
        self.type = 'survey'

    from common.common import set_where, where_to_str, where_list_to_str
    from common.create import create, link_url
    from common.update import get_info_dict
    from common.check_valid import check_survey_valid, check_survey_field_value_not_occupied
    from common.translate import get_translate_df, translate
    from common.db_operation import get_team_dict, get_project_dict, get_survey_module_dict, get_survey_dict, \
        get_response_dict, batch_set_by_interviewer, get_survey_dict_from_field
    from .choice import create_choice_list, choice_import_to_df
    from .expression import reformat_expression
    from .question import get_survey_question_list, get_recode_question_list, get_survey_module_question_list, \
        to_formatted_text_list
    from .update_subprocess import update_respondent_list, update_survey_question, update_reference_list

    def update(self, gsid):
        try:
            # S_ 連接 spreadsheet
            self.set_where(0, '連接 spreadsheet')
            gsheets = self.gsheets
            self.gsid = gsid
            spreadsheet = gsheets.open_by_key(gsid)
            self.spreadsheet = spreadsheet

            # S_ 更新說明頁
            self.set_where(0, '更新說明頁')
            self.link_url()

            # S_ 取得翻譯表
            self.set_where(0, '取得翻譯表')
            self.get_translate_df()

            # S_ 提取資訊頁內容
            self.set_where(0, '提取資訊頁內容')
            self.get_info_dict('問卷資訊')
            self.info_dict['surveyId'] = gsid

            # S_ 檢查資訊頁內容是否正確
            self.check_survey_valid()

            # S_ survey_dict 架構
            self.survey_dict = {
                'teamId': self.team_gsid,
                'projectId': self.project_gsid,
                'surveyId': gsid,
                'customSurveyId': self.info_dict['customSurveyId'],
                'surveyName': self.info_dict['surveyName'],
                'module': defaultdict(dict),
                'moduleInfo': self.module_dict,
            }

            # S_ 處理受訪者分頁內容
            self.update_respondent_list()

            # S_ 處理各個問卷模組資料表
            self.update_survey_question()

            # S_ 更新參考作答列表
            self.set_where(0, '更新參考作答列表')
            self.update_reference_list()

            # S_ 確認沒問題再一起 commit
            self.batch.commit()

            return f'更新問卷設定成功！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

        except:
            return f'更新問卷設定失敗！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'錯誤出現在：<br/>{self.where_to_str()}<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'
