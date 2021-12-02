from common.common import *


def update_interviewer_list(self):
    self.set_where(0, '更新訪員帳號')

    interviewer_df = get_worksheet_df(self.spreadsheet, worksheet_title='訪員帳號', end='C')
    interviewer_df.columns = self.translate(interviewer_df.columns.to_series(), '訪員帳號')

    interviewer_df.index = interviewer_df.interviewerId
    interviewer_dict = interviewer_df.to_dict(orient='index')
    interviewer_list = [v for k, v in interviewer_dict.items()]

    # NOTE interviewerList/{teamId}
    interviewer_list_ref = self.db.document('interviewerList', self.gsid)
    self.batch.set(interviewer_list_ref, {'list': interviewer_list})
