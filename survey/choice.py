from common.common import *


def force_to_str_list(string):
    if string:
        possible_list = ast.literal_eval(string)
        if type(possible_list) == int:
            possible_list = [possible_list]
        str_list = [str(e) for e in possible_list]

        return str_list
    else:
        return []


def choice_row_to_df(row, regex):
    choice_series = row.filter(regex=regex)
    choice_df = pd.DataFrame({
        'choiceId': choice_series.index,
        'choiceBody': choice_series,
    })

    choice_df['choiceId'] = choice_df.choiceId.str.replace(regex, '')

    choice_df.drop(choice_df[choice_df.choiceBody == ''].index, inplace=True)

    choice_df.reset_index(drop=True, inplace=True)

    choice_df['serialNumber'] = choice_df.index
    choice_df.index = choice_df.index.map(str)

    choice_df['asNote'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_note'])), 'asNote'] = True

    choice_df['asSingle'] = False
    choice_df.loc[choice_df.choiceId.isin(force_to_str_list(row['choice_as_single'])), 'asSingle'] = True

    choice_df['choiceGroup'] = ''
    choice_df['upperChoiceId'] = ''

    return choice_df


def create_choice_list(self, row, spreadsheet):
    if row['questionType'] in ['single', 'multiple', 'popupSingle', 'popupMultiple']:
        if row['choice_import']:
            choice_df = self.choice_import_to_df(spreadsheet, row['choice_import'])
        else:
            choice_df = choice_row_to_df(row, regex='choiceId_')
            choice_df['isSpecialAnswer'] = False
    else:
        choice_df = pd.DataFrame()

    # H_ special answer
    special_answer_df = choice_row_to_df(row, regex='specialAnswer_')
    special_answer_df['isSpecialAnswer'] = True

    choice_df = choice_df.append(special_answer_df, ignore_index=True)

    # S_ 按選項順序的分組
    # https://stackoverflow.com/a/62419908
    choice_df['consecutiveChoiceGroup'] = choice_df.choiceGroup.ne(choice_df.choiceGroup.shift()).cumsum()
    choice_df['groupId'] = choice_df.groupby([choice_df.choiceGroup, choice_df.consecutiveChoiceGroup])[
        'choiceGroup'].cumcount()
    choice_df['isGroupFirst'] = (choice_df.groupId == 0) & (choice_df.choiceGroup != '')
    choice_df.drop(columns=['consecutiveChoiceGroup', 'groupId'], inplace=True)

    choice_list = choice_df.to_dict('records')

    has_special_answer = any(choice_df.isSpecialAnswer)

    # H_ answer, answerStatus
    if row['questionType'] == 'description':
        answer_status_type = 'answered'
    elif row['showQuestion'] == '':
        answer_status_type = 'unanswered'
    else:
        answer_status_type = 'hidden'

    return choice_list, has_special_answer, answer_status_type


def choice_import_to_df(self, spreadsheet, choice_import):
    choice_import_df = get_worksheet_df(spreadsheet, worksheet_title=choice_import)

    choice_import_df.columns = self.translate(choice_import_df.columns.to_series(), '選項')

    choice_import_df['serialNumber'] = choice_import_df.index
    choice_import_df.index = choice_import_df.index.map(str)

    if 'asNote' in choice_import_df.columns:
        choice_import_df['asNote'] = choice_import_df.asNote == '1'
    else:
        choice_import_df['asNote'] = False

    if 'asSingle' in choice_import_df.columns:
        choice_import_df['asSingle'] = choice_import_df.asSingle == '1'
    else:
        choice_import_df['asSingle'] = False

    if 'isSpecialAnswer' in choice_import_df.columns:
        choice_import_df['isSpecialAnswer'] = choice_import_df.isSpecialAnswer == '1'
    else:
        choice_import_df['isSpecialAnswer'] = False

    if 'choiceGroup' not in choice_import_df.columns:
        choice_import_df['choiceGroup'] = ''

    if 'upperChoiceId' not in choice_import_df.columns:
        choice_import_df['upperChoiceId'] = ''

    return choice_import_df