from common.common import *


def transfer_respondents(self):
    self.set_where(0, '轉出入受訪者')

    self.set_where(1, '提取受訪者分頁中的資料表')
    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'])
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    last_cell = f'G{len(respondent_df) + 1}'

    # S_
    worksheet = self.spreadsheet.worksheet_by_title(self.info_dict['respondentWorksheetName'])

    # S_ 排序並集中須轉出入的 cases
    worksheet.sort_range('A2', last_cell, basecolumnindex=6)

    # S_ 重新提取
    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'])
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    respondent_df = respondent_df[respondent_df.transferToId != '']

    # S_ 轉移 responses
    for i, row in respondent_df.iterrows():
        response_dict = self.get_respondent_response_dict(row['respondentId'], row['interviewerId'])

        # new_response_dict = {}
        for k, response in response_dict.items():
            response_id = str(uuid.uuid4())
            response['responseId'] = response_id
            response['tempResponseId'] = response_id
            response['ticketId'] = response_id
            response['interviewerId'] = row['transferToId']
            if 'originalInterviewerId' not in response or not response['originalInterviewerId']:
                response['originalInterviewerId'] = row['interviewerId']

            # new_response_dict[response_id] = response
            doc_ref = self.db.document('surveyResponse', response_id)
            self.batch.set(doc_ref, response)

    self.batch.commit()

    # S_
    last_transfer_row = len(respondent_df) + 1
    transfer_to_id_list = respondent_df[['transferToId']].values.tolist()

    # S_ 取代訪員 ID
    worksheet.update_values(f'A2:A{last_transfer_row}', transfer_to_id_list)

    # S_ 清空轉出至訪員 ID
    worksheet.clear('G2', f'G{last_transfer_row}', fields='*')

    # S_ 照受訪者 ID 排序
    worksheet.sort_range('A2', last_cell, basecolumnindex=1)

def update_respondent_list(self):
    self.set_where(0, '處理受訪者分頁內容')

    # NOTE interviewerRespondentList/{interviewerId_surveyId}
    # S_ 先移除所有之前新增至資料庫中的受訪者
    self.set_where(1, '先移除所有之前新增至資料庫中的受訪者')

    query_docs = self.db.collection('interviewerRespondentList') \
        .where('surveyId', '==', self.gsid).stream()
    self.batch.delete_docs(query_docs)

    # S_ 新增此問卷的受訪者列表
    self.set_where(1, '提取受訪者分頁中的資料表')

    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'],
                                     end='F')
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    self.interviewer_list = respondent_df.interviewerId.unique()
    respondent_df.index = respondent_df['respondentId']
    self.respondent_df = respondent_df
    self.survey_dict['interviewerList'] = list(self.interviewer_list)

    self.set_where(1, '新增受訪者至資料庫中')
    self.batch_set_by_interviewer(respondent_df, 'interviewerRespondentList', type='map')


def update_survey_question(self):
    # H_ 更新 Firestore: survey/{surveyId}
    # NOTE SET operation
    self.set_where(0, '處理各個問卷模組資料表')

    # S_1 提取問卷
    self.set_where(1, f'提取{self.info_dict["surveyWorksheetName"]}分頁資料表')

    self.survey_dict['module']['main'] = \
        self.get_survey_question_list(self.spreadsheet, self.info_dict['surveyWorksheetName'], 'main')

    # S_2 提取問卷模組
    for module in self.module_dict:
        self.survey_dict['module'][module] = \
            self.get_survey_module_question_list(self.module_dict[module]['surveyModuleId'], module)

    survey_ref = self.db.document('survey', self.gsid)
    mini_survey_dict = self.survey_dict.copy()
    mini_survey_dict.pop('module')
    mini_survey_dict['random'] = str(uuid.uuid4())
    self.batch.set(survey_ref, mini_survey_dict)


def update_reference_list(self):
    # NOTE 事先會在 to_formatted_text_list 將 customSurveyId 轉 surveyId 等等
    # H_ 更新 Firestore: interviewerReferenceList/{interviewerId_surveyId}
    # S_1 整理 reference_key_list
    if self.reference_key_list:
        reference_dict = pd.DataFrame(self.reference_key_list) \
            .groupby(['surveyId', 'moduleType'])['questionId'] \
            .apply(list).to_dict()

        # S_2 提取 reference，整理成 reference_df
        reference_df = pd.DataFrame()

        for reference_key, question_id_list in reference_dict.items():
            # S_ 從資料庫篩出所有這個 reference_key 所對應的 responses
            response_dict = {}
            # NOTE 不能是當前 surveyId
            if reference_key[0] != self.gsid:
                response_dict = self.get_module_response_dict(reference_key[0], reference_key[1])

            for k, response in response_dict.items():
                # S_ 篩出需要的 respondentId 資料
                respondent_row = self.respondent_df[self.respondent_df.respondentId == response['respondentId']]
                if len(respondent_row):
                    respondent_row = respondent_row.iloc[0]
                    answer_dict = response['answerMap']

                    answer_df = pd.DataFrame({
                        'questionId': list(answer_dict.keys()),
                        'answer': list(answer_dict.values()),
                    })

                    # S_ 再篩出需要的 questionId 作答
                    answer_df = answer_df[answer_df.questionId.isin(question_id_list)]

                    answer_df[['surveyId', 'moduleType', 'respondentId', 'interviewerId']] = \
                        reference_key[0], reference_key[1], respondent_row.respondentId, respondent_row.interviewerId

                    reference_df = reference_df.append(answer_df, ignore_index=True)

        # TODO 插入預設作答，這邊先專門處理
        if '抽樣規則類型' in self.respondent_df.keys():
            init_answer_df = self.respondent_df[['interviewerId', 'respondentId', '抽樣規則類型']]
            init_answer_df['surveyId'] = self.gsid
            # init_answer_df['surveyId'] = self.info_dict['customSurveyId']
            init_answer_df['moduleType'] = 'samplingWithinHousehold'
            init_answer_df['questionId'] = '抽樣規則類型'
            init_answer_df['answer'] = init_answer_df['抽樣規則類型'].apply(lambda x: {
                'type': 'string',
                'withNote': False,
                'stringValue': x
            })
            init_answer_df.drop(columns='抽樣規則類型', inplace=True)

            reference_df = reference_df.append(init_answer_df, ignore_index=True)

        # S_3 移除此問卷的所有參考作答列表
        query_docs = self.db.collection('interviewerReferenceList') \
            .where('surveyId', '==', self.gsid).stream()
        self.batch.delete_docs(query_docs)

        # S_4 以訪員區分，批次上傳
        if len(reference_df):
            self.batch_set_by_interviewer(reference_df, 'interviewerReferenceList')
