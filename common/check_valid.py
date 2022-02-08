from .common import set_where, set_cell


def check_team_valid(self):
    self.set_where(0, '檢查資訊頁內容是否正確')

    info_dict = self.info_dict

    # S_ 檢查是否為空
    for k, v in info_dict.items():
        if not v:
            self.set_where(1, '單位資訊不能為空', error=True)

    # S_ 檢查是否為重複的單位 ID 或名稱
    self.check_team_field_value_not_occupied('customTeamId')
    self.check_team_field_value_not_occupied('teamName')


def check_survey_valid(self):
    self.set_where(0, '檢查資訊頁內容是否正確')

    info_dict = self.info_dict
    worksheet = self.spreadsheet.worksheet_by_title('問卷資訊')

    # S_1 檢查是否為空
    module_names = ['samplingWithinHousehold', 'visitReport', 'housingType', 'interviewReport', 'recode']
    for k, v in info_dict.items():
        if k not in module_names and not v:
            self.set_where(1, '問卷資訊不能為空', error=True)

    # S_2 檢查連結的單位 ID、專案 ID 是否存在
    custom_team_id = info_dict['customTeamId']
    team_dict = self.get_team_dict(custom_team_id)
    if team_dict:
        self.team_gsid = team_dict['teamId']
        url = f'https://docs.google.com/spreadsheets/d/{self.team_gsid}'
        set_cell(worksheet, info_dict['cell']['customTeamId'], custom_team_id, url=url)
    else:
        self.set_where(1, f'找不到連結的單位 ID: {info_dict["customTeamId"]}', error=True)

    custom_project_id = info_dict['customProjectId']
    project_dict = self.get_project_dict(custom_project_id)
    if project_dict:
        self.project_gsid = project_dict['projectId']
        url = f'https://docs.google.com/spreadsheets/d/{self.project_gsid}'
        set_cell(worksheet, info_dict['cell']['customProjectId'], custom_project_id, url=url)
    else:
        self.set_where(1, f'找不到連結的專案 ID: {info_dict["customProjectId"]}', error=True)

    # S_3 統一檢查問卷模組 ID 是否存在
    for module in info_dict:
        if module in module_names and info_dict[module]:
            this_module_id = info_dict[module]
            module_dict = self.get_survey_module_dict(this_module_id)

            if module_dict:
                self.module_dict[module] = module_dict
                url = f'https://docs.google.com/spreadsheets/d/{module_dict["surveyModuleId"]}'
                set_cell(worksheet, info_dict['cell'][module], this_module_id, url=url)
            else:
                self.set_where(1, f'找不到連結的問卷模組 ID: {info_dict[module]}', error=True)

    # S_4 檢查是否為重複的問卷 ID 或名稱
    self.check_survey_field_value_not_occupied('customSurveyId')
    self.check_survey_field_value_not_occupied('surveyName')


def check_project_valid(self):
    info_dict = self.info_dict
    result = ''

    # S_1 檢查是否為空
    for k, v in info_dict.items():
        if k != 'responseImportWorksheetName' and not v:
            return '專案資訊不能為空!'

    # S_2 檢查連結的單位 ID 是否存在
    team_dict = self.get_team_dict(info_dict['customTeamId'])

    if team_dict:
        self.team_gsid = team_dict['teamId']
        self.info_dict['teamId'] = self.team_gsid
        self.info_dict.pop('customTeamId')
    else:
        result += f'找不到連結的單位 ID: {info_dict["customTeamId"]}！\n'

    # S_3 檢查是否為重複的專案 ID 或名稱
    id_occupied = self.check_project_field_value_not_occupied('customProjectId')
    name_occupied = self.check_project_field_value_not_occupied('projectName')

    result += f'{id_occupied}{name_occupied}'

    return result


def check_team_field_value_not_occupied(self, field):
    check_dict = self.get_team_dict_from_field(field, self.info_dict[field])

    if check_dict and check_dict['teamId'] != self.gsid:
        self.set_where(1, f'已有相同的 {self.info_dict[field]}，請重新命名', error=True)


def check_survey_field_value_not_occupied(self, field):
    check_dict = self.get_survey_dict_from_field(field, self.info_dict[field])

    if check_dict and check_dict['surveyId'] != self.gsid:
        self.set_where(1, f'同專案下，已有相同的 {self.info_dict[field]}，請重新命名', error=True)
    

def check_project_field_value_not_occupied(self, field):
    check_dict = self.get_project_dict_from_field(field, self.info_dict[field])

    if check_dict and check_dict['projectId'] != self.gsid:
        return f'同單位下，已有 {self.info_dict[field]}，請更換名稱！\n'
    else:
        return ''
