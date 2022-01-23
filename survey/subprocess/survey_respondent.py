from common.common import *


def get_respondent_and_interviewer_data(self, log_layer=0):
    self.set_where(log_layer, '提取受訪者分頁資料')

    respondent_df = self.get_respondent_df()
    self.interviewer_list = respondent_df.interviewerId.unique()
    self.survey_dict['interviewerList'] = list(self.interviewer_list)


def update_interviewer_respondent_list(self):
    self.set_where(0, '處理受訪者分頁內容')

    # S_ 移除所有之前新增至資料庫中的受訪者
    self.set_where(1, '移除所有之前新增至資料庫中的受訪者')

    query_docs = self.db.collection('interviewerRespondentList') \
        .where('surveyId', '==', self.gsid).stream()
    self.batch.delete_docs(query_docs)

    # S_ 提取受訪者分頁資料
    self.get_respondent_and_interviewer_data(log_layer=1)

    # S_ 新增受訪者至資料庫中
    self.set_where(1, '新增受訪者至資料庫中')
    self.batch_set_by_interviewer(self.respondent_df, 'interviewerRespondentList', type='map')


def transfer_respondents(self):
    self.set_where(0, '轉出入受訪者')

    # S_ 集中須轉出入的受訪者
    self.set_where(1, '集中需轉出入的受訪者 (直接編輯 Google Sheets)')
    respondent_df = self.get_respondent_df()

    # NOTE 找出最後一個 cell
    last_cell = f'G{len(respondent_df) + 1}'

    worksheet = self.spreadsheet.worksheet_by_title(self.info_dict['respondentWorksheetName'])
    worksheet.sort_range('A2', last_cell, basecolumnindex=6)

    # S_ 轉移需轉出入受訪者的所有回覆
    self.set_where(1, '轉移需轉出入受訪者的所有回覆')

    # NOTE 提取需轉出入的受訪者
    respondent_df = self.get_respondent_df()
    respondent_df = respondent_df[respondent_df.transferToId != '']

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

    # NOTE 最後一筆轉出入在 worksheet 上的 row id
    last_transfer_row = len(respondent_df) + 1
    transfer_to_id_list = respondent_df[['transferToId']].values.tolist()

    # S_ 更新受訪者分頁
    self.set_where(1, '更新受訪者分頁 (直接編輯 Google Sheets)')
    worksheet.update_values(f'A2:A{last_transfer_row}', transfer_to_id_list)

    # NOTE 清空轉出至訪員 ID
    worksheet.clear('G2', f'G{last_transfer_row}', fields='*')

    # NOTE 照受訪者 ID 重新排序
    worksheet.sort_range('A2', last_cell, basecolumnindex=1)
