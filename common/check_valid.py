
def check_survey_valid(self):
    info_dict = self.info_dict
    result = ''

    # S_1 檢查是否為空
    module_names = ['samplingWithinHousehold', 'visitReport', 'housingType', 'interviewReport', 'recode']
    for k, v in info_dict.items():
        if k not in module_names and not v:
            return '問卷資訊不能為空!'

    # S_2 檢查連結的單位 ID、專案 ID 是否存在
    team_dict = self.get_team_dict(info_dict['customTeamId'])
    if team_dict:
        self.team_gsid = team_dict['teamId']
    else:
        result += f'找不到連結的單位 ID: {info_dict["customTeamId"]}！\n'

    project_dict = self.get_project_dict(info_dict['customProjectId'])
    if project_dict:
        self.project_gsid = project_dict['projectId']
    else:
        result += f'找不到連結的專案 ID: {info_dict["customProjectId"]}！\n'

    # S_3 統一檢查問卷模組 ID 是否存在
    for module in info_dict:
        if module in module_names and info_dict[module]:
            module_dict = self.get_survey_module_dict(info_dict[module])

            if module_dict:
                self.module_dict[module] = module_dict
            else:
                result += f'找不到連結的問卷模組 ID: {info_dict[module]}！\n'

    # S_4 檢查是否為重複的問卷 ID 或名稱
    id_occupied = self.check_survey_field_value_not_occupied('customSurveyId')
    name_occupied = self.check_survey_field_value_not_occupied('surveyName')

    result += f'{id_occupied}{name_occupied}'

    return result


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


def check_survey_field_value_not_occupied(self, field):
    check_dict = self.get_survey_dict_from_field(field, self.info_dict[field])

    if check_dict and check_dict['surveyId'] != self.gsid:
        return f'同專案下，已有 {self.info_dict[field]}，請更換名稱！\n'
    else:
        return ''
    

def check_project_field_value_not_occupied(self, field):
    check_dict = self.get_project_dict_from_field(field, self.info_dict[field])

    if check_dict and check_dict['projectId'] != self.gsid:
        return f'同單位下，已有 {self.info_dict[field]}，請更換名稱！\n'
    else:
        return ''
