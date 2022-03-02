from common.db_operation import Batch

class Team:
    def __init__(self, gsheets, db, bucket):
        self.gsheets = gsheets
        self.db = db
        self.bucket = bucket
        self.batch = Batch(self.db)
        self.gsid = ''
        self.type = 'team'
        self.template_id = '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'
        self.where = [''] * 5
        self.where_list = []

    # NOTE common
    from common.common import try_run_process, set_where, where_to_str, where_list_to_str
    from common.create import create, link_url
    from common.update import get_info_dict
    from common.translate import get_translate_df, translate
    from common.check_valid import check_team_valid, check_team_field_value_not_occupied
    from common.db_operation import get_team_dict_from_field

    # NOTE process
    from .team_process import init_process, update_team_process, delete_team_process

    # NOTE subprocess
    from .update_subprocess import update_interviewer_list

    def update(self, gsid):
        return self.try_run_process('更新單位設定', self.update_team_process, gsid)

    def delete(self, gsid):
        return self.try_run_process('刪除單位及底下所有設定與資料', self.delete_team_process, gsid)
