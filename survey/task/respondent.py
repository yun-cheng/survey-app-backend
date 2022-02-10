from common.common import *


def get_respondent_df(self):
    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'],
                                     end='G')
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')
    respondent_df.index = respondent_df.respondentId
    self.respondent_df = respondent_df

    return respondent_df
