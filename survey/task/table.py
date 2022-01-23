from common.common import *


def process_table_question(self, question_list_df):
    table_id_list = question_list_df.tableId.unique().tolist()

    if len(table_id_list) > 1:
        for table_id in table_id_list:
            if table_id:
                table_df = question_list_df[question_list_df.tableId == table_id].reset_index(
                    drop=True)
                # S_ 表格類型
                table_type = table_df.loc[0, 'questionType']
                if table_type == 'simpleTable':
                    table_df['questionId'] = table_id + table_df.questionId
                    table_df['rowId'] = table_df.index - 1

                    # S_ 讓選項都相同
                    cols = list(filter(re.compile('choice|specialAnswer').search, table_df.columns))
                    table_df[cols] = table_df.loc[0, cols]

                    # S_ showQuestion
                    table_question_id = table_df.loc[0, 'questionId']
                    table_df.loc[1:, 'showQuestion'] = table_df.loc[1:, 'showQuestion'].apply(
                        lambda x: '' if x == '' else f'({x}) & ')
                    table_df.loc[1:, 'showQuestion'] = table_df.loc[1:, 'showQuestion'] + \
                                                       f'({table_question_id} != 1)'

                elif table_type == 'complexTable':
                    # NOTE 分 row, col, cell 處理
                    col_df = table_df[table_df.isTableColumn == '1'].reset_index(drop=True)
                    row_df = table_df[(table_df.isTableColumn != '1') & (table_df.index != 0)] \
                        .reset_index(drop=True)
                    row_df['rowId'] = row_df.index
                    col_df['rowId'] = -1
                    table_df['rowId'] = -1
                    cell_df = row_df.loc[row_df.index.repeat(len(col_df))].reset_index(drop=True)
                    col_df['questionType'] = 'description'
                    row_df['questionType'] = 'description'

                    # S_ 合併 questionBody，在瀏覽模式使用
                    cell_df['questionBody'] = cell_df.questionBody + '\n' + \
                                              col_df.questionBody.tolist() * len(row_df)
                    cell_df['questionNote'] = ''

                    # S_ questionId
                    cell_df['tableRowId'] = cell_df.questionId
                    cell_df['tableColId'] = col_df.questionId.tolist() * len(row_df)
                    cell_df['questionId'] = table_id + cell_df.tableRowId + cell_df.tableColId
                    row_df['questionId'] = table_id + row_df.questionId
                    col_df['questionId'] = table_id + col_df.questionId
                    table_df['questionId'] = table_id + table_df.questionId

                    # S_ showQuestion
                    table_question_id = table_df.loc[0, 'questionId']
                    # S_-1 如果本來就有設定條件的處理
                    col_df['showQuestion'] = col_df.showQuestion.apply(
                        lambda x: '' if x == '' else f'({x}) & ')
                    row_df['showQuestion'] = row_df.showQuestion.apply(
                        lambda x: '' if x == '' else f'({x}) & ')
                    cell_df['showQuestion'] = cell_df.showQuestion.apply(
                        lambda x: '' if x == '' else f'({x}) & ')
                    # S_-2 加入跟此表格有關的條件，!= 1 的用意是在那題隱藏時此題也隱藏，
                    #  row, col 看的是整個表格，而 cell 看的是 row, col
                    col_df['showQuestion'] = col_df.showQuestion + f'({table_question_id} != 1)'
                    row_df['showQuestion'] = row_df.showQuestion + f'({table_question_id} != 1)'
                    cell_df['showQuestion'] = cell_df.apply(
                        lambda row: f'{row.showQuestion}({row.tableId}{row.tableRowId} != 1) & '
                                    f'({row.tableId}{row.tableColId} != 1)', axis=1)
                    # S_-3 如果有 * 則取代成 tableColId
                    # NOTE row_df 的 * 在 reformat_expression 排除
                    cell_df['showQuestion'] = cell_df.apply(
                        lambda row: row.showQuestion.replace('*', row.tableColId), axis=1)

                    cell_df.drop(columns=['tableRowId', 'tableColId'], inplace=True)

                    # S_ combine
                    table_df = table_df.iloc[[0]]
                    table_df = table_df.append(row_df, ignore_index=True)
                    table_df = table_df.append(col_df, ignore_index=True)
                    table_df = table_df.append(cell_df, ignore_index=True)

                if table_type in ['simpleTable', 'complexTable']:
                    # S_ 合併回 question_list_df
                    index_to_drop = question_list_df[question_list_df.tableId == table_id].index
                    question_list_df.drop(index=index_to_drop, inplace=True)
                    question_list_df = question_list_df.iloc[:index_to_drop[0]] \
                        .append(table_df) \
                        .append(question_list_df.iloc[index_to_drop[0]:], ignore_index=True)

    return question_list_df
