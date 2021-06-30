
from common.common import *


class Project:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db
        self.batch = self.db.batch()
        self.template_id = '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ'
        self.team_gsid = ''
        self.gsid = ''
        self.info_dict = {}
        self.response_list = []
        self.type = 'project'

    from common.create import create, link_url
    from common.db_operation import get_team_dict, get_project_dict_from_field, batch_set_response
    from common.check_valid import check_project_valid, check_project_field_value_not_occupied
    from common.translate import get_translate_df, translate
    from .update_subprocess import update_response_list

    def update(self, gsid):
        # try:
        # S_1 連接 spreadsheet
        gsheets = self.gsheets
        self.gsid = gsid
        spreadsheet = gsheets.open_by_key(gsid)
        self.spreadsheet = spreadsheet
        # NOTE 欄位翻譯表
        self.get_translate_df()

        # S_2 提取資訊
        project_info = spreadsheet.worksheet_by_title('專案資訊') \
            .get_values(start='C2', end='C5', include_all=True)
        project_info = [v[0] for v in project_info]
        project_info.insert(0, gsid)

        keys = ['projectId', 'customProjectId', 'projectName', 'customTeamId', 'responseImportWorksheetName']

        self.info_dict = dict(zip(keys, project_info))

        # S_3 檢查輸入的內容是否符合格式
        check_result = self.check_project_valid()
        if check_result:
            return check_result

        # S_4 更新匯入歷史作答
        self.update_response_list()

        # S_5 更新 project
        # NOTE Firestore SET
        project_ref = self.db.document('project', gsid)
        self.batch.set(project_ref, self.info_dict)

        # S_6 確認沒問題再一起 commit
        self.batch.commit()

        # except:
        #     return '更新專案設定失敗!'

        return '更新專案設定成功!'

    def delete(self, gsid):
        try:
            # S_1 刪除 Firestore: project 本身的資料
            db = self.db
            batch = db.batch()

            # S_1-1 刪除 Firestore: project/{projectId}
            # TAG Firestore DELETE
            project_ref = db.document('project', gsid)
            project_dict = project_ref.doc_to_dict()
            team_gsid = project_dict['teamId']
            batch.delete(project_ref)

            # S_1-2 刪除 Firestore: projectList/{teamId}
            # TAG Firestore UPDATE
            project_list_ref = db.document('projectList', team_gsid)
            batch.set(project_list_ref, {
                gsid: firestore.DELETE_FIELD
            }, merge=True)

            # S_2 刪除 Firestore: 相關聯的資料
            # S_2-1 刪除 Firestore: quizList/{teamId}
            # TAG Firestore UPDATE
            quiz_list_ref = db.document('quizList', team_gsid)
            batch.set(quiz_list_ref, {
                gsid: firestore.DELETE_FIELD
            }, merge=True)

            # S_2-2 刪除 Firestore: quiz/{quizId}
            # TAG Firestore DELETE
            quiz_docs = db.collection('quiz') \
                .where('projectId', '==', gsid) \
                .stream()

            for doc in quiz_docs:
                batch.delete(doc.reference)

            # S_2-3 刪除 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore DELETE
            interviewer_quiz_docs = db.collection('interviewerQuiz') \
                .where('projectId', '==', gsid) \
                .stream()

            for doc in interviewer_quiz_docs:
                batch.delete(doc.reference)

            batch.commit()

        except:
            return '刪除專案失敗!'

        return '刪除專案成功!'
