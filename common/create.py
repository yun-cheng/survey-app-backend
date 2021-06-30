from common.common import *


def create(self, email):
    try:
        if self.type == 'project':
            type_str = '專案'
        elif self.type == 'team':
            type_str = '單位'
        elif self.type == 'survey':
            type_str = '問卷'

        # S_1 連接模板
        # HIGHLIGHT 需開啟 Google Sheets API
        template_spreadsheet = self.gsheets.open_by_key(self.template_id)

        # S_2 創立新的 spreadsheet
        spreadsheet = self.gsheets.create(f'新建立之{type_str}設定檔(可自訂名稱)')
        self.spreadsheet = spreadsheet
        self.gsid = spreadsheet.id

        # S_3 從模板複製到新創立的 spreadsheet
        for template_worksheet in template_spreadsheet.worksheets():
            worksheet = template_worksheet.copy_to(self.gsid)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # S_4 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # S_5 建立超連結
        self.link_url()

        # S_6 設定分享權限
        email_message = '新建立之問卷設定檔'
        spreadsheet.share(email, 'writer', emailMessage=email_message)
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
        # NOTE 轉移所有權
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

    except:
        return f'建立{type_str}失敗!'

    return f'新建立之{type_str}設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'


def link_url(self):
    worksheet = self.spreadsheet.worksheet_by_title('說明')
    gsid = self.gsid

    if self.type == 'project':
        update_url = f'{main_url}?action=update&on=project&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此專案設定")')

        delete_url = f'{main_url}?action=delete&on=project&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "刪除此專案")')

    elif self.type == 'team':
        update_url = f'{main_url}?action=update&on=team&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此單位設定")')

        delete_url = f'{main_url}?action=delete&on=team&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "刪除此單位")')

    elif self.type == 'survey':
        # S_1 '更新此問卷設定' 連結
        update_url = f'{main_url}?action=update&on=survey&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此問卷設定")')

        # S_2 '更新此問卷紀錄' 連結
        update_result_url = f'{main_url}?action=update&on=survey_response&gsid={gsid}'
        worksheet.update_value('A4', f'=HYPERLINK("{update_result_url}", "更新此問卷回覆")')

        # S_3 '刪除此問卷設定' 連結
        delete_url = f'{main_url}?action=delete&on=survey&gsid={gsid}'
        worksheet.update_value('A6', f'=HYPERLINK("{delete_url}", "刪除此問卷設定")')

        # S_4 '刪除此問卷紀錄' 連結
        delete_result_url = f'{main_url}?action=delete&on=survey_response&gsid={gsid}'
        worksheet.update_value('A7', f'=HYPERLINK("{delete_result_url}", "刪除此問卷回覆")')