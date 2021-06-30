from common.common import *


def update_respondent_list(self):
    # H_ 更新 Firestore: interviewerRespondentList/{interviewerId_surveyId}
    # NOTE DELETE, SET operation
    # S_1 移除此問卷的所有受訪者列表
    remove_docs_list = self.db.collection('interviewerRespondentList') \
        .where('surveyId', '==', self.gsid).stream()

    for doc in remove_docs_list:
        self.batch.delete(doc.reference)

    # S_2 新增此問卷的受訪者列表
    respondent_df = get_worksheet_df(self.spreadsheet,
                                     worksheet_title=self.info_dict['respondentWorksheetName'],
                                     end='F')
    respondent_df.columns = self.translate(respondent_df.columns.to_series(), '受訪地址')

    self.interviewer_list = respondent_df.interviewerId.unique()
    respondent_df.index = respondent_df['respondentId']
    self.respondent_df = respondent_df
    self.survey_dict['interviewerList'] = list(self.interviewer_list)

    self.batch_set_by_interviewer(respondent_df, 'interviewerRespondentList')


def update_survey_question(self):
    # H_ 更新 Firestore: survey/{surveyId}
    # NOTE SET operation
    # S_1 提取問卷
    self.survey_dict['module']['main'] = \
        self.get_survey_question_list(self.spreadsheet, self.info_dict['surveyWorksheetName'])

    # S_2 提取問卷模組
    for module in self.module_dict:
        self.survey_dict['module'][module] = \
            self.get_survey_module_question_list(self.module_dict[module]['surveyModuleId'], module)

    survey_ref = self.db.document('survey', self.gsid)
    self.batch.set(survey_ref, self.survey_dict)


def update_reference_list(self):
    # NOTE 事先會在 to_formatted_text_list 將 customSurveyId 轉 surveyId 等等
    # H_ 更新 Firestore: interviewerReferenceList/{interviewerId_surveyId}
    # S_1 整理 reference_key_list
    reference_dict = pd.DataFrame(self.reference_key_list).groupby(['surveyId', 'moduleType'])['questionId'].apply(
        list).to_dict()

    # S_2 提取 reference，整理成 reference_df
    reference_df = pd.DataFrame()

    for reference_key, question_id_list in reference_dict.items():
        response_dict = self.get_response_dict(reference_key[0], reference_key[1])

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

    # S_3 移除此問卷的所有參考作答列表
    remove_docs_list = self.db.collection('interviewerReferenceList') \
        .where('surveyId', '==', self.gsid).stream()

    for doc in remove_docs_list:
        self.batch.delete(doc.reference)

    # S_4 以訪員區分，批次上傳
    if len(reference_df):
        self.batch_set_by_interviewer(reference_df, 'interviewerReferenceList')
