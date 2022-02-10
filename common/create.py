from common.common import *


def create(self, email):
    try:
        if self.type == 'project':
            type_str = '專案'
        elif self.type == 'team':
            type_str = '單位'
        elif self.type == 'survey':
            type_str = '問卷'
        elif self.type == 'module':
            type_str = '問卷模組'

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
        email_message = f'新建立之{type_str}設定檔'
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
    n_row = worksheet.rows

    if self.type == 'project':
        update_url = f'{main_url}?action=update&on=project&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此專案設定")')

        delete_url = f'{main_url}?action=delete&on=project&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "刪除此專案")')

    elif self.type == 'team':
        set_row = 10
        if n_row < set_row:
            worksheet.add_rows(set_row - n_row)
        elif n_row > set_row:
            worksheet.delete_rows(2, n_row - set_row)

        if worksheet.get_value(f'A{n_row}') != backend_version:
            worksheet.clear('A1', f'A{n_row}', fields='*')

            # S_ '設定檔說明' 連結
            doc_url = 'https://yunchengdev.notion.site/2e80fd569f2348d29ecd25671d544da1'
            set_cell(worksheet, 'A1', '設定檔說明', url=doc_url, font_size=36,
                     horizontal_alignment='center')

            # S_ '更新此單位設定' 連結
            update_url = f'{main_url}?action=update&on=team&gsid={gsid}'
            set_cell(worksheet, 'A3', '更新此單位設定', url=update_url, font_size=36,
                     background_color='yellow', horizontal_alignment='center')

            # S_ '刪除此單位及底下所有設定與資料' 連結
            delete_team_url = f'{main_url}?action=delete&on=team&gsid={gsid}'
            set_cell(worksheet, 'A6', '刪除此單位及底下所有設定與資料', url=delete_team_url, font_size=36,
                     background_color='red', color='white', horizontal_alignment='center')

            worksheet.update_value(f'A{set_row}', backend_version)

    elif self.type == 'survey':
        set_row = 20
        if n_row < set_row:
            worksheet.add_rows(set_row - n_row)
        elif n_row > set_row:
            worksheet.delete_rows(2, n_row - set_row)

        if worksheet.get_value('A18') != f'本次操作之後端版本：{backend_version}':
            worksheet.clear('A1', f'A{set_row}', fields='*')

            # S_ '設定檔說明' 連結
            doc_url = 'https://yunchengdev.notion.site/2e80fd569f2348d29ecd25671d544da1'
            set_cell(worksheet, 'A1', '設定檔說明', url=doc_url, font_size=36,
                     horizontal_alignment='center')

            # S_ '更新此問卷設定' 連結
            update_url = f'{main_url}?action=update&on=survey&gsid={gsid}'
            set_cell(worksheet, 'A3', '更新此問卷設定', url=update_url, font_size=36,
                     background_color='yellow', horizontal_alignment='center')

            # S_ '更新此受訪者' 連結
            update_url = f'{main_url}?action=update_respondents&on=survey&gsid={gsid}'
            set_cell(worksheet, 'A4', '更新受訪者', url=update_url, font_size=36,
                     background_color='yellow', horizontal_alignment='center')

            # S_ '更新下載資料連結' 連結
            update_result_url = f'{main_url}?action=update_download_files&on=survey&gsid={gsid}'
            set_cell(worksheet, 'A5', '更新下載資料連結', url=update_result_url, font_size=36,
                     background_color='yellow', horizontal_alignment='center')

            # S_ '轉出入受訪者' 連結
            transfer_url = f'{main_url}?action=transfer&on=survey&gsid={gsid}'
            set_cell(worksheet, 'A12', '轉出入受訪者', url=transfer_url, font_size=36,
                     background_color='orange', horizontal_alignment='center')

            # S_ '清除資料庫所有回覆' 連結
            delete_result_url = f'{main_url}?action=delete_all_responses&on=survey&gsid={gsid}'
            set_cell(worksheet, 'A15', '清除資料庫所有回覆', url=delete_result_url, font_size=36,
                     background_color='red', color='white', horizontal_alignment='center')

            # S_ '刪除此問卷設定' 連結
            # delete_url = f'{main_url}?action=delete&on=survey&gsid={gsid}'
            # set_cell(worksheet, 'A6', '刪除此問卷設定', url=delete_url, font_size=36, background_color='red',
            #          color='white', horizontal_alignment='center')

            set_cell(worksheet, 'A18', f'最後操作之後端版本：{backend_version}')

    elif self.type == 'module':
        # S_ '更新此問卷模組設定' 連結
        update_url = f'{main_url}?action=update&on={self.module_str}module&gsid={gsid}'
        worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "連結此問卷模組至專案")')

        # S_1-7 '刪除此問卷模組設定' 連結
        delete_url = f'{main_url}?action=delete&on={self.module_str}module&gsid={gsid}'
        worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "取消連結此問卷模組至專案")')
