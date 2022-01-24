from common.db_operation import Batch

class Survey:
    def __init__(self, gsheets, db, bucket):
        self.gsheets = gsheets
        self.db = db
        self.bucket = bucket
        self.batch = Batch(self.db.batch())
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
        #
        self.response_dict = {}
        #
        self.where = [''] * 5
        self.where_list = []
        self.type = 'survey'

    # NOTE common
    from common.common import try_run_process, batch_commit, set_where, where_to_str, where_list_to_str
    from common.create import create, link_url
    from common.update import get_info_dict
    from common.check_valid import check_survey_valid, check_survey_field_value_not_occupied
    from common.translate import get_translate_df, translate
    from common.db_operation import get_team_dict, get_project_dict, get_survey_module_dict, \
        get_survey_dict, get_module_response_dict, get_survey_response_dict, \
        get_respondent_response_dict, batch_set_by_interviewer, get_survey_dict_from_field, \
        set_survey, batch_delete_response

    # NOTE process
    from .survey_process import init_process, update_survey_process, update_respondents_process, \
        transfer_respondents_process, update_download_files_process, delete_all_responses_process

    # NOTE subprocess
    from .subprocess.survey_survey import update_mini_survey, get_survey_module
    from .subprocess.survey_respondent import get_respondent_and_interviewer_data, \
        update_interviewer_respondent_list, transfer_respondents
    from .subprocess.survey_reference import update_reference_list
    from .subprocess.survey_download_files import process_response_df, process_info_df, \
        process_progress_df, process_wide_df, process_download_link

    # NOTE task
    from .task.question import get_question_list, get_recode_question_list, \
        get_survey_module_question_list, to_formatted_text_list
    from .task.choice import create_choice_list, choice_import_to_df
    from .task.expression import reformat_expression
    from .task.table import process_table_question
    from .task.respondent import get_respondent_df
    from .task.download_files import public_audio_link

    def update(self, gsid):
        return self.try_run_process('更新問卷設定', self.update_survey_process, gsid)

    def update_respondents(self, gsid):
        return self.try_run_process('更新受訪者', self.update_respondents_process, gsid)

    def transfer(self, gsid):
        return self.try_run_process('轉出入', self.transfer_respondents_process, gsid)

    def update_download_files(self, gsid):
        return self.try_run_process('更新下載資料', self.update_download_files_process, gsid)

    def delete_all_responses(self, gsid):
        return self.try_run_process('清除資料庫所有回覆', self.delete_all_responses_process, gsid)
