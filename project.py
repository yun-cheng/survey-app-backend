
from common import *


class Project:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

    def create(self, email):
        # S_1-1 連接模板
        # HIGHLIGHT 需開啟 Google Sheets API
        template_id = '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ'
        template_spreadsheet = self.gsheets.open_by_key(template_id)

        # S_1-2 創立新的 spreadsheet
        spreadsheet = self.gsheets.create('新建立之專案設定檔(可自訂名稱)')

        # S_1-3 從模板複製到新創立的 spreadsheet
        for i in range(3):
            worksheet = template_spreadsheet.worksheet('index', i).copy_to(spreadsheet.id)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # S_1-4 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # S_1-5 "更新此專案"連結
        worksheet = spreadsheet.worksheet_by_title('說明')
        update_url = '{}?update_type=project&project_key={}'.format(main_url, spreadsheet.id)
        worksheet.update_value('A3', '=HYPERLINK("{}", "更新此專案")'.format(update_url))

        # S_1-6 "刪除此專案"連結
        delete_url = '{}?delete_type=project&project_key={}'.format(main_url, spreadsheet.id)
        worksheet.update_value('A4', '=HYPERLINK("{}", "刪除此專案")'.format(delete_url))

        # S_1-7 "自訂專案 ID"
        worksheet = spreadsheet.worksheet_by_title('專案資訊')
        worksheet.update_value('B6', spreadsheet.id)

        # S_2 寫入 Firestore
        # TAG update
        result_message = self.update(gsid=spreadsheet.id)

        # S_1-8 設定分享權限
        # HIGHLIGHT 需開啟 Google Drive API
        spreadsheet.share(email, 'writer', emailMessage='新建立之專案設定檔')
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage='新建立之測驗設定檔')
        # NOTE 轉移所有權
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        if result_message == '更新專案成功!':
            return '新建立之專案設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {}'.format(spreadsheet.url)
        else:
            return '建立專案失敗!'

    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            project_df = get_worksheet_df(spreadsheet, worksheet_title='專案資訊')
            project_df['info_name'] = ['unitName', 'projectName', 'id', 'password', 'projectId']
            project_dict = project_df.set_index('info_name').T.to_dict('records')[0]
            project_id = project_dict['projectId']
            project_dict['gsheetsId'] = gsid

            # S_1-3
            # TODO 檢查輸入的內容是否符合格式
            for k, v in project_dict.items():
                if not v:
                    return '專案資訊不能為空!'

            # S_2-1 更新 project
            # TAG firestore
            # EXAMPLE
            '''
            project / demo_project_id / {
                gsheetsId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                id: 'demo_admin',
                password: 'demo_password',
                projectId: 'demo_project_id',
                projectName: '範例專案',
                unitName: '範例單位'
            }
            '''
            # NOTE query 回來就會是 doc generator，必須要用迴圈提取，即使只有一筆
            docs = self.db.collection('project').where('gsheetsId', '==', gsid).stream()
            for doc in docs:
                self.db.document('project', doc.id).delete()

            dict_to_firestore(project_dict, self.db.document('project', project_id))

            # S_2-2 更新 project_list
            # TAG firestore
            # EXAMPLE
            '''
            project_list / project_list / {
                'list': [{
                    gsheetsId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                    projectId: 'demo_project_id',
                    projectName: '範例專案'
                }, ...]
            }
            '''
            doc_ref = self.db.document('project_list', 'project_list')
            project_list_dict = doc_ref.doc_to_dict()

            new_project_dict = {
                'projectId': project_dict['projectId'],
                'projectName': project_dict['projectName'],
                'gsheetsId': project_dict['gsheetsId'],
            }
            if not project_list_dict:
                new_project_list = [new_project_dict]
            else:
                old_project_list = project_list_dict['list']
                new_project_list = []
                for project in old_project_list:
                    if project['gsheetsId'] != gsid:
                        new_project_list.append(project)

                new_project_list.append(new_project_dict)

            dict_to_firestore({
                'list': new_project_list
            }, doc_ref)

            # S_2-3 更新 interviewer
            # TAG firestore
            # EXAMPLE
            '''
            interviewer / demo_project_id / {
                list: [
                    {id: 'id001', name: 'AAA', password: 'password001'},
                    ...
                ]
            }
            '''
            interviewer_df = get_worksheet_df(spreadsheet, worksheet_title='訪員帳號')
            interviewer_dict = df_to_dict(interviewer_df, ['id', 'password', 'name'])

            dict_to_firestore(interviewer_dict, self.db.document('interviewer', project_id))

            # TODO interviewer_quiz 要刪掉去除的訪員

        except:
            return '更新專案失敗!'

        return '更新專案成功!'

    def delete(self, gsid):
        try:
            batch = self.db.batch()

            # S_1 調出該 gsid 的 project_id
            project_query = self.db.collection('project') \
                .where('gsheetsId', '==', gsid)
            docs = project_query.stream()
            for doc in docs:
                project_dict = doc.to_dict()

            project_id = project_dict['projectId']

            # S_2-1 刪除 project/{project_id}/{data}
            batch.delete(self.db.document('project', project_id))

            # S_2-2 刪除 project_list/project_list/list 中該 project
            # TAG firestore
            doc_ref = self.db.document('project_list', 'project_list')
            project_list_dict = doc_ref.doc_to_dict()

            old_project_list = project_list_dict['list']
            new_project_list = []
            for project in old_project_list:
                if project['gsheetsId'] != gsid:
                    new_project_list.append(project)

            batch.set(doc_ref, {
                'list': new_project_list
            })

            # S_2-3 刪除 interviewer/{project_id}/{data}
            # TAG firestore
            batch.delete(self.db.document('interviewer', project_id))

            # S_2-4 刪除 interviewer_quiz/{interviewer_id_project_id}/{data}
            # TAG firestore
            docs = self.db.collection('interviewer_quiz').where('projectId', '==', project_id).stream()
            for doc in docs:
                batch.delete(self.db.document('interviewer_quiz', doc.id))

            # NOTE 保留相關測驗
            # NOTE 保留相關測驗紀錄

            batch.commit()
        except:
            return '刪除專案失敗!'

        return '刪除專案成功!'
