
from common import *


class Project:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

    def create(self, email):
        try:
            # S_1 創立並設定新的 spreadsheet
            # S_1-1 連接模板
            # HIGHLIGHT 需開啟 Google Sheets API
            template_id = '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ'
            template_spreadsheet = self.gsheets.open_by_key(template_id)

            # S_1-2 創立新的 spreadsheet
            spreadsheet = self.gsheets.create('新建立之專案設定檔(可自訂名稱)')
            gsid = spreadsheet.id

            # S_1-3 從模板複製到新創立的 spreadsheet
            for i in range(2):
                worksheet = template_spreadsheet.worksheet('index', i).copy_to(gsid)
                worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

            # S_1-4 刪除初始 worksheet
            sheet1 = spreadsheet.worksheet_by_title('Sheet1')
            spreadsheet.del_worksheet(sheet1)

            # S_1-5 '更新此專案設定' 連結
            worksheet = spreadsheet.worksheet_by_title('說明')
            update_url = f'{main_url}?action=update&on=project&gsid={gsid}'
            worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此專案設定")')

            # S_1-6 '刪除此專案' 連結
            delete_url = f'{main_url}?action=delete&on=team&gsid={gsid}'
            worksheet.update_value('A4', f'=HYPERLINK("{delete_url}", "刪除此專案")')

            # S_1-7 設定分享權限
            email_message = '新建立之專案設定檔'
            spreadsheet.share(email, 'writer', emailMessage=email_message)
            # TODO 到時我的權限可拿掉
            spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
            # NOTE 轉移所有權
            # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        except:
            return '建立專案失敗!'

        return f'新建立之專案設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'

    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            gsheets = self.gsheets
            db = self.db
            spreadsheet = gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            project_info = spreadsheet.worksheet_by_title('專案資訊') \
                .get_values(start='C2', end='C4', include_all=True)

            project_info_dict = {
                'projectId': gsid,
                'customProjectId': project_info[0][0],
                'projectName': project_info[1][0],
                'customTeamId': project_info[2][0],
            }

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in project_info_dict.items():
                if not v:
                    return '專案資訊不能為空!'

            # S_1-3-2 檢查連結的單位 ID 是否存在
            team_query = db.collection('team') \
                .where('customTeamId', '==', project_info_dict['customTeamId'])
            team_dict = team_query.query_to_dict(first=True)

            if team_dict:
                team_gsid = team_dict['teamId']
                project_info_dict['teamId'] = team_gsid
                project_info_dict.pop('customTeamId')
            else:
                return '找不到連結的單位 ID！'

            # S_1-3-3 檢查是否為重複的專案 ID 或名稱
            project_query = db.collection('project') \
                .where('teamId', '==', team_gsid) \
                .where('projectName', '==', project_info_dict['projectName'])
            project_query_dict = project_query.query_to_dict(first=True)

            if project_query_dict and project_query_dict['projectId'] != gsid:
                return '同單位下，自訂專案名稱重複，請輸入其他名稱！'

            project_query = db.collection('project') \
                .where('teamId', '==', team_gsid) \
                .where('customProjectId', '==', project_info_dict['customProjectId'])
            project_query_dict = project_query.query_to_dict(first=True)

            if project_query_dict and project_query_dict['projectId'] != gsid:
                return '同單位下，自訂專案 ID 重複，請輸入其他 ID！'

            # S_2 更新 Firestore
            batch = db.batch()

            # S_2-1 更新 Firestore: project/{projectId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            project / {projectId} / {
                projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                customProjectId: 'demo_project_id',
                projectName: '範例專案',
                teamId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'
            }
            '''
            project_ref = db.document('project', gsid)
            batch.set(project_ref, project_info_dict)

            batch.commit()

        except:
            return '更新專案設定失敗!'

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
