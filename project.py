
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
            delete_url = f'{main_url}?action=delete&on=unit&gsid={gsid}'
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
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            project_info = spreadsheet.worksheet_by_title('專案資訊') \
                .get_values(start='C2', end='C4', include_all=True)

            project_info_dict = {
                'projectId': gsid,
                'customProjectId': project_info[0][0],
                'projectName': project_info[1][0],
                'customUnitId': project_info[2][0],
            }

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in project_info_dict.items():
                if not v:
                    return '專案資訊不能為空!'

            # S_1-3-2 檢查連結的單位 ID 是否存在
            unit_list_ref = self.db.document('unitList', 'unitList')
            unit_list_dict = unit_list_ref.doc_to_dict()

            if unit_list_dict:
                for k, v in unit_list_dict.items():
                    if v['customUnitId'] == project_info_dict['customUnitId']:
                        project_info_dict['unitId'] = k
                        unit_gsid = k
                        project_info_dict.pop('customUnitId')
                        break

            if not unit_gsid:
                return '找不到連結的單位 ID！'

            # S_1-3-3 檢查是否為重複的專案 ID 或名稱
            project_list_ref = self.db.document('projectList', unit_gsid)
            project_list_dict = project_list_ref.doc_to_dict()

            if project_list_dict:
                for k, v in project_list_dict.items():
                    if k != gsid:
                        if v['customProjectId'] == project_info_dict['customProjectId']:
                            return '專案 ID 重複，請輸入其他 ID！'
                        elif v['projectName'] == project_info_dict['projectName']:
                            return '專案名稱重複，請輸入其他名稱！'

            # S_2 更新 Firestore
            batch = self.db.batch()

            # S_2-1 更新 Firestore: project/{projectId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            project / {projectId} / {
                projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                customProjectId: 'demo_project_id',
                projectName: '範例專案',
                unitId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'
            }
            '''
            project_ref = self.db.document('project', gsid)
            batch.set(project_ref, project_info_dict)

            # S_2-2 更新 Firestore: projectList/{unitId}
            # TAG Firestore UPDATE
            # EXAMPLE
            '''
            project_list / {unitId} / {
                {projectId}: (project data)
            }
            '''
            batch.set(project_list_ref, {
                gsid: project_info_dict
            }, merge=True)

            batch.commit()

        except:
            return '更新專案設定失敗!'

        return '更新專案設定成功!'

    def delete(self, gsid):
        try:
            # S_1 刪除 Firestore
            batch = self.db.batch()

            # S_1-1 刪除 Firestore: project/{projectId}
            # TAG Firestore DELETE
            project_ref = self.db.document('project', gsid)
            project_dict = project_ref.doc_to_dict()
            unit_gsid = project_dict['unitId']
            batch.delete(project_ref)

            # S_1-2 刪除 Firestore: projectList/{unitId}
            # TAG Firestore UPDATE
            project_list_ref = self.db.document('projectList', unit_gsid)
            batch.set(project_list_ref, {
                gsid: firestore.DELETE_FIELD
            }, merge=True)

            # S_ 刪除 quizList/{unitId}

            # S_1-3 刪除 interviewer_quiz/{interviewerId_projectId}
            # TAG Firestore DELETE
            # TODO
            # docs = self.db.collection('interviewer_quiz').where('projectId', '==', project_id).stream()
            # for doc in docs:
            #     batch.delete(self.db.document('interviewer_quiz', doc.id))

            # NOTE 保留相關測驗
            # NOTE 保留相關測驗紀錄

            batch.commit()

        except:
            return '刪除專案失敗!'

        return '刪除專案成功!'
