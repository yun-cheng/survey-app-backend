from common.common import *
from common.db_operation import delete_docs


class Team:
    def __init__(self, gsheets, db, bucket):
        self.gsheets = gsheets
        self.db = db
        self.bucket = bucket
        self.batch = self.db.batch()
        self.gsid = ''
        self.type = 'team'
        self.template_id = '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'

    from common.create import create, link_url


    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            gsheets = self.gsheets
            db = self.db
            spreadsheet = gsheets.open_by_key(gsid)
            self.spreadsheet = spreadsheet
            self.gsid = gsid

            # S_ 更新說明頁
            self.link_url()

            # S_1-2 提取資訊
            team_info = spreadsheet.worksheet_by_title('單位資訊') \
                .get_values(start='C2', end='C3', include_all=True)

            team_info_dict = {
                'teamId': gsid,
                'customTeamId': team_info[0][0],
                'teamName': team_info[1][0]
            }

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in team_info_dict.items():
                if not v:
                    return '單位資訊不能為空!'

            # S_1-3-2 檢查是否為重複的單位 ID 或名稱
            team_query = db.collection('team') \
                .where('teamId', '==', team_info_dict['teamId']) \
                .limit(1)
            team_query_dict = team_query.query_to_dict(first=True)

            if team_query_dict and team_query_dict['teamId'] != gsid:
                return '自訂單位 ID 重複，請輸入其他 ID！'

            team_query = db.collection('team') \
                .where('teamName', '==', team_info_dict['teamName']) \
                .limit(1)
            team_query_dict = team_query.query_to_dict(first=True)

            if team_query_dict and team_query_dict['teamId'] != gsid:
                return '自訂單位名稱重複，請輸入其他名稱！'

            # S_2 更新 Firestore
            batch = db.batch()

            # S_2-1 更新 Firestore: team 本身的資料
            # S_2-1-1 更新 Firestore: team/{teamId}
            team_ref = db.document('team', gsid)
            batch.set(team_ref, team_info_dict)

            # S_2-1-3 更新 Firestore: interviewerList/{teamId}
            interviewer_list_df = get_worksheet_df(spreadsheet, worksheet_title='訪員帳號', end='C')
            interviewer_map = df_to_dict(interviewer_list_df,
                                         new_column_names=['interviewerId', 'interviewerPassword', 'interviewerName'],
                                         index_column='interviewerId')

            interviewer_list = [v for k, v in interviewer_map.items()]

            interviewer_map_ref = db.document('interviewerMap', gsid)
            # NOTE 後面要使用
            old_interviewer_map = interviewer_map_ref.doc_to_dict()
            batch.set(interviewer_map_ref, interviewer_map)

            interviewer_list_ref = db.document('interviewerList', gsid)
            batch.set(interviewer_list_ref, {'list': interviewer_list})

            # S_2-2 更新 Firestore: 相關聯的資料
            # S_2-2-1 更新 Firestore: interviewerQuiz/{interviewerId_projectId}
            # S_2-2-1-1 interviewer_id 的增減
            new_interviewer_id_list = list(interviewer_map.keys())

            if old_interviewer_map:
                old_interviewer_id_list = list(old_interviewer_map.keys())
                add_interviewer_id_list = list(set(new_interviewer_id_list) - set(old_interviewer_id_list))
                delete_interviewer_id_list = list(set(old_interviewer_id_list) - set(new_interviewer_id_list))
            else:
                add_interviewer_id_list = new_interviewer_id_list
                delete_interviewer_id_list = []

            # S_2-2-1-2 新增的 interviewer
            # NOTE Firestore SET
            quiz_list_ref = db.document('quizList', gsid)
            quiz_list_dict = quiz_list_ref.doc_to_dict()

            for interviewer_id in add_interviewer_id_list:
                if quiz_list_dict:
                    for project_gsid, interviewer_quiz_dict in quiz_list_dict.items():
                        interviewer_quiz_dict['interviewerId'] = interviewer_id
                        interviewer_quiz_ref = db.document('interviewerQuiz', f'{interviewer_id}_{project_gsid}')
                        batch.set(interviewer_quiz_ref, interviewer_quiz_dict)

            # S_2-2-1-3 刪除的 interviewer
            # NOTE Firestore DELETE
            interviewer_quiz_docs = db.collection('interviewerQuiz') \
                .where('teamId', '==', gsid) \
                .stream()

            for doc in interviewer_quiz_docs:
                doc_dict = doc.to_dict()
                if doc_dict['interviewerId'] in delete_interviewer_id_list:
                    batch.delete(doc.reference)

            batch.commit()

        except:
            return '更新單位設定失敗!'

        return '更新單位設定成功!'

    def delete(self, gsid):
        try:
            # S_ 刪除 team 本身的資料
            # NOTE team/{teamId}
            self.db.document('team', gsid).delete()

            # S_ 刪除底下的訪員帳號
            # NOTE interviewerList/{teamId}
            # NOTE interviewerMap/{teamId}
            self.db.document('interviewerList', gsid).delete()
            self.db.document('interviewerMap', gsid).delete()

            # S_ 刪除底下的 project
            # NOTE project/{projectId}
            query_docs = self.db.collection('project') \
                .where('teamId', '==', gsid) \
                .stream()
            delete_docs(query_docs)

            # S_ 刪除底下的 survey
            # NOTE survey/{surveyId}
            query_docs = self.db.collection('survey') \
                .where('teamId', '==', gsid) \
                .stream()

            for doc in query_docs:
                doc.reference.delete()

                # S_ 刪除 storage 中的 survey
                self.bucket.delete_file(f'survey/{doc.id}/try.json')
                self.bucket.delete_file(f'survey/{doc.id}/{doc.id}.json')

            # S_ 刪除底下的 survey module
            # NOTE surveyModule/{surveyModuleId}
            query_docs = self.db.collection('surveyModule') \
                .where('teamId', '==', gsid) \
                .stream()
            delete_docs(query_docs)

            # S_ 刪除相關 referenceList
            # NOTE interviewerReferenceList/{interviewerId_surveyId}
            query_docs = self.db.collection('interviewerReferenceList') \
                .where('teamId', '==', gsid) \
                .stream()
            delete_docs(query_docs)

            # S_ 刪除相關 respondentList
            # NOTE interviewerRespondentList/{interviewerId_surveyId}
            query_docs = self.db.collection('interviewerRespondentList') \
                .where('teamId', '==', gsid) \
                .stream()
            delete_docs(query_docs)

            # S_ 刪除 response
            # NOTE surveyResponse
            query_docs = self.db.collection('surveyResponse') \
                .where('teamId', '==', gsid) \
                .stream()
            delete_docs(query_docs)

            # TODO 刪除 audio

        except:
            return '刪除單位失敗!'

        return '刪除單位成功!'
