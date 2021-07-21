from common.common import *


def get_info_dict(self, worksheet_title):
    info_df = get_worksheet_df(self.spreadsheet, worksheet_title=worksheet_title, end='C')
    info_df.columns = self.translate(info_df.columns.to_series(), '資訊頁面欄位')
    info_df['info_key'] = self.translate(info_df.info_key, '資訊頁面')
    info_df = info_df[info_df.info_key != '']

    info_dict = dict(zip(info_df.info_key, info_df.info_value))

    self.info_dict = info_dict
