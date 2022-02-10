from common.common import *


def init_process(self, gsid):
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

    # S_ survey_dict
    self.survey_dict = {
        'teamId': self.team_gsid,
        'projectId': self.project_gsid,
        'surveyId': gsid,
        'customSurveyId': self.info_dict['customSurveyId'],
        'surveyName': self.info_dict['surveyName'],
        'module': defaultdict(dict),
        'moduleInfo': self.module_dict,
        'version': survey_version,
    }


def update_survey_process(self):
    # S_ 提取受訪者分頁資料
    self.get_respondent_and_interviewer_data()

    # S_ 處理各個問卷模組資料表
    self.get_survey_module()

    # S_ 更新精簡問卷設定
    self.update_mini_survey()

    # S_ 更新參考作答列表
    self.update_reference_list()

    # S_ 批次同步
    self.batch_commit()

    # S_ 更新完整問卷設定
    self.update_full_survey()


def update_respondents_process(self):
    # S_ 處理受訪者分頁內容
    self.update_interviewer_respondent_list()

    # S_ 更新精簡問卷設定，主要是更新 interviewerList
    self.update_mini_survey(full_update=False)

    # S_ 更新參考作答列表
    self.update_reference_list()

    # S_ 批次同步
    self.batch_commit()


def transfer_respondents_process(self):
    # S_ 轉出入受訪者
    self.transfer_respondents()

    # S_ 更新受訪者
    self.update_respondents_process()


def update_download_files_process(self):
    # S_ 從資料庫下載所有回覆
    self.get_survey_response_dict()

    # S_ 處理模組回覆資料
    self.process_response_df()

    # S_ 處理回覆資訊資料
    self.process_info_df()

    # S_ 處理受訪者進度資料
    self.process_progress_df()

    # S_ 轉成受訪者回覆資料
    self.process_wide_df()

    # FIXME recode module answer value

    # S_ 上傳並更新下載連結
    self.process_download_link()


def delete_all_responses_process(self):
    # S_
    self.batch_delete_response()

    # S_ 批次同步
    self.batch_commit()
