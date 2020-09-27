from common import *


class Unit:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

    def create(self, email):
        # S_1 創立並設定新的 spreadsheet
        # S_1-1 連接模板
        template_gsid = '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'
        template_spreadsheet = self.gsheets.open_by_key(template_gsid)

        # S_1-2 創立新的 spreadsheet
        spreadsheet = self.gsheets.create('新建立之單位設定檔(可自訂名稱)')
        gsid = spreadsheet.id

        # S_1-3 從模板複製到新創立的 spreadsheet
        for i in range(3):
            worksheet = template_spreadsheet.worksheet('index', i).copy_to(gsid)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # S_1-4 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # S_1-5 '更新此單位設定' 連結
        worksheet = spreadsheet.worksheet_by_title('說明')
        update_url = f'{main_url}?action=update&on=unit&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此單位設定")')

        # S_1-6 '刪除此單位' 連結
        delete_url = f'{main_url}?action=delete&on=unit&gsid={gsid}'
        worksheet.update_value('A4', f'=HYPERLINK("{delete_url}", "刪除此單位")')

        # S_1-7 設定分享權限
        email_message = '新建立之單位設定檔'
        spreadsheet.share(email, 'writer', emailMessage=email_message)
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
        # NOTE 轉移所有權
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        return f'新建立之單位設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'

    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            unit_info = spreadsheet.worksheet_by_title('單位資訊') \
                .get_values(start='C2', end='C3', include_all=True)

            unit_info_dict = {
                'unitId': gsid,
                'customUnitId': unit_info[0][0],
                'unitName': unit_info[1][0]
            }

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in unit_info_dict.items():
                if not v:
                    return '單位資訊不能為空!'

            # S_1-3-2 檢查是否為重複的單位 ID 或名稱
            unit_list_ref = self.db.document('unitList', 'unitList')
            unit_list_dict = unit_list_ref.doc_to_dict()

            if unit_list_dict:
                for k, v in unit_list_dict.items():
                    if k != gsid:
                        if v['customUnitId'] == unit_info_dict['customUnitId']:
                            return '單位 ID 重複，請輸入其他 ID！'
                        elif v['unitName'] == unit_info_dict['unitName']:
                            return '單位名稱重複，請輸入其他名稱！'

            # S_2 更新 Firestore
            batch = self.db.batch()

            # S_2-1 更新 Firestore: unit/{unitId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            unit / {unitId} / {
                unitId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8',
                customUnitId: 'demo_unit_id',
                unitName: '範例單位名稱'
            }
            '''
            unit_ref = self.db.document('unit', gsid)
            batch.set(unit_ref, unit_info_dict)

            # S_2-2 更新 Firestore: unitList/unitList
            # TAG Firestore UPDATE
            # EXAMPLE
            '''
            unitList / unitList / {
                {unitId}: (unit data)
            }
            '''
            batch.set(unit_list_ref, {
                gsid: unit_info_dict
            }, merge=True)

            # S_2-3 更新 Firestore: interviewer/{unitId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            interviewer / {unitId} / {
                {interviewerId}: {
                    interviewerId: 'id001',
                    interviewerPassword: 'password001',
                    interviewerName: 'AAA'
                }
            }
            '''
            interviewer_df = get_worksheet_df(spreadsheet, worksheet_title='訪員帳號', end='C')
            interviewer_dict = df_to_dict(interviewer_df,
                                          new_column_names=['interviewerId', 'interviewerPassword', 'interviewerName'],
                                          index_column='interviewerId')

            interviewer_ref = self.db.document('interviewer', gsid)
            batch.set(interviewer_ref, interviewer_dict)

            # S_2-4 更新 Firestore:
            # TODO 訪員有變化時，受影響的其他 collection

            batch.commit()

        except:
            return '更新單位設定失敗!'

        return '更新單位設定成功!'

    def delete(self, gsid):
        try:
            # S_1 刪除 Firestore
            batch = self.db.batch()

            # S_1-1 刪除 Firestore: unit/{unitId}
            # TAG Firestore DELETE
            unit_ref = self.db.document('unit', gsid)
            batch.delete(unit_ref)

            # S_1-2 刪除 Firestore: unitList/unitList
            # TAG Firestore DELETE
            unit_list_ref = self.db.document('unitList', 'unitList')
            batch.update(unit_list_ref, {
                gsid: firestore.DELETE_FIELD
            })

            # S_1-3 刪除 Firestore: interviewer/{unitId}
            # TAG Firestore DELETE
            interviewer_ref = self.db.document('interviewer', gsid)
            batch.delete(interviewer_ref)

            # S_1-4 刪除 interviewer_quiz/{interviewer_id_project_id}/{data}
            # TAG Firestore DELETE
            # TODO
            # docs = self.db.collection('interviewer_quiz').where('projectId', '==', project_id).stream()
            # for doc in docs:
            #     batch.delete(self.db.document('interviewer_quiz', doc.id))

            # NOTE 保留相關測驗
            # NOTE 保留相關測驗紀錄

            batch.commit()
        except:
            return '刪除單位失敗!'

        return '刪除單位成功!'
