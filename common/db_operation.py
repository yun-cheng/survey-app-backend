from .common import *


def get_team_dict(self, custom_team_id):
    query = self.db.collection('team') \
        .where('customTeamId', '==', custom_team_id)
    result_dict = query.query_to_dict(first=True)

    return result_dict


def get_project_dict(self, custom_project_id):
    query = self.db.collection('project') \
        .where('customProjectId', '==', custom_project_id) \
        .where('teamId', '==', self.team_gsid)
    result_dict = query.query_to_dict(first=True)

    return result_dict


def get_survey_module_dict(self, custom_survey_module_id):
    query = self.db.collection('surveyModule') \
        .where('customSurveyModuleId', '==', custom_survey_module_id) \
        .where('projectId', '==', self.project_gsid)
    result_dict = query.query_to_dict(first=True)

    return result_dict


def get_survey_dict(self, custom_survey_id):
    query = self.db.collection('survey') \
        .where('customSurveyId', '==', custom_survey_id) \
        .where('projectId', '==', self.project_gsid)
    result_dict = query.query_to_dict(first=True)

    return result_dict


# def get_survey_gsid(self, custom_survey_id):
#     result_dict = self.get_survey_dict(custom_survey_id)
#
#     if result_dict:
#         return result_dict['surveyId']
#     else:
#         return ''


def get_response_dict(self, survey_id, module_type):
    query = self.db.collection('surveyResponse') \
        .where('projectId', '==', self.project_gsid) \
        .where('surveyId', '==', survey_id) \
        .where('responseStatus', '==', 'finished') \
        .where('moduleType', '==', module_type)
    result_dict = query.query_to_dict()

    return result_dict


def get_all_responses_dict(self):
    query = self.db.collection('surveyResponse') \
        .where('surveyId', '==', self.gsid) \
        .where('responseStatus', '==', 'finished') \
        .where('isDeleted', '==', False)
    result_dict = query.query_to_dict()

    query = self.db.collection('surveyResponse') \
        .where('surveyId', '==', self.gsid) \
        .where('moduleType', '==', 'main') \
        .where('responseStatus', '==', 'answering') \
        .where('editFinished', '==', True) \
        .where('isDeleted', '==', False)
    result_dict_1 = query.query_to_dict()

    result_dict.update(result_dict_1)

    return result_dict


def get_respondent_response_dict(self, respondent_id, interviewer_id):
    query = self.db.collection('surveyResponse') \
        .where('projectId', '==', self.project_gsid) \
        .where('surveyId', '==', self.gsid) \
        .where('respondentId', '==', respondent_id) \
        .where('interviewerId', '==', interviewer_id) \
        .where('isDeleted', '==', False)
    result_dict = query.query_to_dict()

    return result_dict


def get_survey_dict_from_field(self, field, field_value):
    query = self.db.collection('survey') \
        .where('projectId', '==', self.project_gsid) \
        .where(field, '==', field_value)
    result_dict = query.query_to_dict(first=True)

    return result_dict


def get_project_dict_from_field(self, field, field_value):
    query = self.db.collection('project') \
        .where('teamId', '==', self.team_gsid) \
        .where(field, '==', field_value)
    result_dict = query.query_to_dict(first=True)

    return result_dict


def batch_set_by_interviewer(self, df, document, type='list'):
    result_dict = {
        'surveyId': self.gsid,
        'projectId': self.project_gsid,
        'teamId': self.team_gsid,
    }

    for interviewer_id in self.interviewer_list:
        subset_df = df[df.interviewerId == interviewer_id]

        if len(subset_df):
            subset_df.drop(columns='interviewerId', inplace=True)
            result_dict['interviewerId'] = interviewer_id
            if type == 'list':
                result_dict['list'] = subset_df.to_dict('records')
            elif type == 'map':
                result_dict['map'] = subset_df.to_dict('index')

            doc_ref = self.db.document(document, f'{interviewer_id}_{self.gsid}')
            self.batch.set(doc_ref, result_dict)


def batch_set_response(self, df):
    result_dict = {
        'projectId': self.gsid,
        'teamId': self.team_gsid,
        'responseStatus': 'finished',
        'isPastData': True,
    }

    for response in self.response_list:
        subset_df = df[(df.surveyId == response['surveyId']) &
                       (df.moduleType == response['moduleType']) &
                       (df.respondentId == response['respondentId'])]

        if len(subset_df):
            subset_df.index = subset_df.questionId
            answer_dict = subset_df.answer.to_dict()
            result_dict['answerMap'] = answer_dict
            result_dict['surveyId'] = response['surveyId']
            result_dict['moduleType'] = response['moduleType']
            result_dict['respondentId'] = response['respondentId']

            doc_ref = self.db.collection('surveyResponse').document()
            self.batch.set(doc_ref, result_dict)


def set_survey(self):
    self.bucket.dict_to_storage(self.survey_dict, f'survey/{self.gsid}/try.json')
    self.bucket.dict_to_storage(self.survey_dict, f'survey/{self.gsid}/{self.gsid}.json')


def batch_delete_responses(self):
    remove_docs_list = self.db.collection('surveyResponse') \
        .where('surveyId', '==', self.gsid) \
        .where('isDeleted', '==', False).stream()

    for doc in remove_docs_list:
        self.batch.delete(doc.reference)
