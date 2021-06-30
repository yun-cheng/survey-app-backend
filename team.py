from common.common import *


class Team:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db
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
            # TAG Firestore SET
            # EXAMPLE
            '''
            team / {teamId} / {
                teamId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8',
                customTeamId: 'demo_team_id',
                teamName: '範例單位名稱'
            }
            '''
            team_ref = db.document('team', gsid)
            batch.set(team_ref, team_info_dict)

            # S_2-1-3 更新 Firestore: interviewerList/{teamId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            interviewerList / {teamId} / {
                {interviewerId}: {
                    interviewerId: 'id001',
                    interviewerPassword: 'password001',
                    interviewerName: 'AAA'
                }
            }
            '''
            interviewer_list_df = get_worksheet_df(spreadsheet, worksheet_title='訪員帳號', end='C')
            interviewer_map = df_to_dict(interviewer_list_df,
                                         new_column_names=['interviewerId', 'interviewerPassword', 'interviewerName'],
                                         index_column='interviewerId')

            interviewer_list = [v for k, v in interviewer_map.items()]

            interviewer_map_ref = db.document('interviewerMap', gsid)
            # NOTE 後面要使用
            old_interviewer_map = {}
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
            # TAG Firestore SET
            quiz_list_ref = db.document('quizList', gsid)
            quiz_list_dict = quiz_list_ref.doc_to_dict()

            for interviewer_id in add_interviewer_id_list:
                if quiz_list_dict:
                    for project_gsid, interviewer_quiz_dict in quiz_list_dict.items():
                        interviewer_quiz_dict['interviewerId'] = interviewer_id
                        interviewer_quiz_ref = db.document('interviewerQuiz', f'{interviewer_id}_{project_gsid}')
                        batch.set(interviewer_quiz_ref, interviewer_quiz_dict)

            # S_2-2-1-3 刪除的 interviewer
            # TAG Firestore DELETE
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
            batch = self.db.batch()

            # S_1 刪除 Firestore: team 本身的資料
            # S_1-1 刪除 Firestore: team/{teamId}
            # TAG Firestore DELETE
            team_ref = self.db.document('team', gsid)
            batch.delete(team_ref)

            # S_1-2 刪除 Firestore: teamList/teamList
            # TAG Firestore UPDATE
            team_list_ref = self.db.document('teamList', 'teamList')
            batch.set(team_list_ref, {
                gsid: firestore.DELETE_FIELD
            }, merge=True)

            # S_1-3 刪除 Firestore: interviewerList/{teamId}
            # TAG Firestore DELETE
            interviewer_list_ref = self.db.document('interviewerList', gsid)
            batch.delete(interviewer_list_ref)

            # S_2 刪除 Firestore: 相關聯的資料
            # S_2-1 刪除 Firestore: project/{projectId}
            # TAG Firestore DELETE
            project_docs = self.db.collection('project') \
                .where('teamId', '==', gsid) \
                .stream()

            for doc in project_docs:
                batch.delete(doc.reference)

            # S_2-2 刪除 Firestore: projectList/{teamId}
            # TAG Firestore DELETE
            project_list_ref = self.db.document('projectList', gsid)
            batch.delete(project_list_ref)

            # S_2-3 刪除 Firestore: quiz/{quizId}
            # TAG Firestore DELETE
            quiz_docs = self.db.collection('quiz') \
                .where('teamId', '==', gsid) \
                .stream()

            for doc in quiz_docs:
                batch.delete(doc.reference)

            # S_2-4 刪除 Firestore: quizList/{teamId}
            # TAG Firestore DELETE
            quiz_list_ref = self.db.document('quizList', gsid)
            batch.delete(quiz_list_ref)

            # S_2-5 刪除 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore DELETE
            interviewer_quiz_docs = self.db.collection('interviewerQuiz') \
                .where('teamId', '==', gsid) \
                .stream()

            for doc in interviewer_quiz_docs:
                batch.delete(doc.reference)

            batch.commit()
        except:
            return '刪除單位失敗!'

        return '刪除單位成功!'
