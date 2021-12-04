from common.common import *


def transfer_respondents(self):
    self.set_where(0, '轉出入受訪者')

    self.set_where(1, '提取受訪者分頁中的資料表')

    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'])
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    # S_ 找出最後一個 cell
    last_cell = f'G{len(respondent_df) + 1}'

    # S_
    worksheet = self.spreadsheet.worksheet_by_title(self.info_dict['respondentWorksheetName'])

    # S_ 集中須轉出入的受訪者
    self.set_where(1, '集中須轉出入的受訪者 (直接編輯 Google 表單)')
    worksheet.sort_range('A2', last_cell, basecolumnindex=6)

    # S_ 提取需轉出入的 respondent
    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'])
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    respondent_df = respondent_df[respondent_df.transferToId != '']

    # S_ 轉移 responses
    self.set_where(1, '轉移轉出入受訪者的所有回覆')
    for i, row in respondent_df.iterrows():
        response_dict = self.get_respondent_response_dict(row['respondentId'], row['interviewerId'])

        for k, response in response_dict.items():
            response_id = str(uuid.uuid4())
            response['responseId'] = response_id
            response['tempResponseId'] = response_id
            response['ticketId'] = response_id
            response['interviewerId'] = row['transferToId']
            if 'originalInterviewerId' not in response or not response['originalInterviewerId']:
                response['originalInterviewerId'] = row['interviewerId']

            doc_ref = self.db.document('surveyResponse', response_id)
            self.batch.set(doc_ref, response)

    # NOTE 在這邊就要 commit，確認成功後，後面才會繼續編輯 Google 表單
    self.batch.commit()

    # S_ 最後一筆轉出入在 worksheet 上的 row id
    last_transfer_row = len(respondent_df) + 1
    transfer_to_id_list = respondent_df[['transferToId']].values.tolist()

    # S_ 取代訪員 ID
    self.set_where(1, '編輯並重新排序受訪者分頁 (直接編輯 Google 表單)')
    worksheet.update_values(f'A2:A{last_transfer_row}', transfer_to_id_list)

    # S_ 清空轉出至訪員 ID
    worksheet.clear('G2', f'G{last_transfer_row}', fields='*')

    # S_ 照受訪者 ID 重新排序
    worksheet.sort_range('A2', last_cell, basecolumnindex=1)
