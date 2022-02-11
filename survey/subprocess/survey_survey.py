from common.common import *


def update_mini_survey(self, full_update=True):
    self.set_where(0, '更新精簡問卷設定')
    survey_ref = self.db.document('survey', self.gsid)

    # S_ 因非完整更新，要從舊設定提取資訊
    if not full_update:
        old_survey_dict = survey_ref.doc_to_dict()
        self.reference_key_list = old_survey_dict['referenceKeyList']
        self.survey_dict['version'] = old_survey_dict.get('version', '')
        self.survey_dict['lastUpdatedTimeStamp'] = old_survey_dict.get('lastUpdatedTimeStamp', 0)

    mini_survey_dict = self.survey_dict.copy()
    mini_survey_dict.pop('module')
    mini_survey_dict['random'] = str(uuid.uuid4())
    mini_survey_dict['referenceKeyList'] = self.reference_key_list
    self.batch.set(survey_ref, mini_survey_dict)


def get_survey_module(self):
    self.set_where(0, '處理各個問卷模組資料表')

    # S_ 提取主問卷
    self.set_where(1, f'提取{self.info_dict["surveyWorksheetName"]}分頁資料表')

    self.survey_dict['module']['main'] = \
        self.get_question_list(self.spreadsheet, self.info_dict['surveyWorksheetName'], 'main')

    # S_ 提取問卷模組
    for module in self.module_dict:
        self.survey_dict['module'][module] = \
            self.get_survey_module_question_list(self.module_dict[module]['surveyModuleId'], module)


def update_full_survey(self):
    # S_ 問卷資料另存至 storage
    self.set_survey()

    worksheet = self.spreadsheet.worksheet_by_title('說明')
    set_cell(worksheet, f'A19', f'問卷設定使用之格式版本：{survey_version}')
    set_cell(worksheet, f'A20', f'問卷設定最後更新時間：{now_str}')
