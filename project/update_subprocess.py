from common.common import *


def update_response_list(self):
    # S_1 移除此專案所有匯入的歷史作答
    remove_docs_list = self.db.collection('surveyResponse') \
        .where('projectId', '==', self.gsid) \
        .where('isPastData', '==', True).stream()

    for doc in remove_docs_list:
        self.batch.delete(doc.reference)

    if self.info_dict['responseImportWorksheetName']:
        # S_2 新增此專案的匯入歷史作答
        response_df = get_worksheet_df(self.spreadsheet,
                                       worksheet_title=self.info_dict['responseImportWorksheetName'],
                                       end='E')
        response_df.columns = self.translate(response_df.columns.to_series(), '歷史作答')
        response_df['moduleType'] = self.translate(response_df.moduleType, '模組類型')

        response_df['answer'] = response_df.answerValue.apply(lambda x: {
            'type': 'string',
            'withNote': False,
            'stringValue': x
        })

        self.response_list = response_df[['surveyId', 'moduleType', 'respondentId']].drop_duplicates().to_dict('records')

        self.batch_set_response(response_df)
