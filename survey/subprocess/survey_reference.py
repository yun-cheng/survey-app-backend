from common.common import *


def update_reference_list(self):
    self.set_where(0, '更新參考作答列表')

    # NOTE 事先會在 to_formatted_text_list 將 customSurveyId 轉 surveyId 等等
    # H_ 更新 Firestore: interviewerReferenceList/{interviewerId_surveyId}
    if self.reference_key_list:
        # S_1 整理 reference_key_list
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
