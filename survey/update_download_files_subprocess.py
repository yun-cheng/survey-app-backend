from common.common import *


def get_answer_value(row):
    if row['type'] == 'string':
        return row['stringValue']
    elif row['type'] == 'choice':
        return row['choiceValue']
    elif row['type'] == 'int':
        return row['intValue']
    elif row['type'] == 'choiceList':
        return row['choiceListValue']
    else:
        return None


def process_response_df(self):
    self.set_where(0, '處理模組回覆資料')

    # S_ 處理原始資料
    self.set_where(1, '處理原始資料')
    info_keys = ['responseId', 'respondentId', 'moduleType', 'responseStatus',
                 'interviewerId', 'surveyId', 'deviceId',
                 'createdTimeStamp', 'lastChangedTimeStamp']
    data_keys = ['responseId', 'respondentId', 'moduleType', 'responseStatus',
                 'interviewerId', 'surveyId']
    response_df = pd.DataFrame()
    info_list = []
    for response_id, response in self.response_dict.items():
        info = {k: response[k] for k in info_keys}
        info_list.append(info)

        for k, v in response['answerStatusMap'].items():
            response['answerMap'][k].update(
                {'answerStatus': v['answerStatusType'],
                 'lastChangedTimeStamp': v.get('lastChangedTimeStamp', None)})

        answer_df = pd.DataFrame.from_dict(response['answerMap'], orient='index')
        answer_df.reset_index(inplace=True)
        answer_df.rename(columns={'index': 'questionId', 'noteMap': 'note'}, inplace=True)
        answer_df['choiceValue'] = answer_df.choiceValue.apply(
            lambda x: x['id'] if x is not None else x)
        answer_df['choiceListValue'] = answer_df.choiceListValue.apply(
            lambda x: [y['id'] for y in x] if x is not None else x)
        answer_df['answerValue'] = answer_df.apply(get_answer_value, axis=1)

        answer_df = answer_df[['questionId', 'type', 'answerStatus', 'answerValue', 'note',
                               'lastChangedTimeStamp']]

        data = {k: response[k] for k in data_keys}

        answer_df = pd.concat([pd.DataFrame(data, index=answer_df.index), answer_df],
                              axis=1)
        response_df = response_df.append(answer_df, ignore_index=True)

    self.set_where(1, '篩出要保留的資料')
    response_df = response_df[response_df.type != ''].reset_index(drop=True)

    self.set_where(1, '處理日期時間欄位')
    response_df['lastChangedTimeStamp'] = pd.to_datetime(response_df.lastChangedTimeStamp,
                                                         unit='us') \
        .dt.tz_localize('UTC') \
        .dt.tz_convert('Asia/Taipei') \
        .dt.strftime('%Y-%m-%d %H:%M:%S')

    # S_ 處理文字說明 note
    self.set_where(1, '處理文字說明 note')
    note_df = response_df[response_df.note.notnull()]
    response_df.drop(columns='note', inplace=True)
    response_df['isNote'] = 0
    response_df['noteOf'] = None

    if len(note_df):
        note_df['note'] = note_df.note.apply(lambda x: x.items())
        note_df = note_df.explode('note')
        note_df[['noteOf', 'answerValue']] = note_df.note.tolist()
        note_df.drop(columns='note', inplace=True)
        note_df['isNote'] = 1
        response_df = response_df.append(note_df, ignore_index=True)

    response_df.sort_values(
        ['respondentId', 'moduleType', 'responseId', 'questionId', 'isNote', 'noteOf'],
        ignore_index=True,
        inplace=True)

    response_df.reorder_columns('answerValue', -1)
    response_df.reorder_columns('lastChangedTimeStamp', -1)

    self.info_list = info_list
    self.response_df = response_df


def public_audio_link(self, row):
    responseId = row['responseId']
    audio_link = ''
    if row['moduleType'] == 'main':
        blob = self.bucket.blob(f'audio/{responseId}/{responseId}.m4a')
        try:
            if blob.exists():
                blob.make_public()
                audio_link = blob.public_url
        except:
            audio_link = ''

    return audio_link


def process_info_df(self):
    self.set_where(0, '處理回覆資訊資料')

    info_df = pd.DataFrame.from_dict(self.info_list)

    info_df.sort_values(
        ['respondentId', 'moduleType', 'lastChangedTimeStamp'],
        ignore_index=True,
        inplace=True)

    # S_ 模組內編號
    info_df['idInGroup'] = info_df \
                               .groupby(['respondentId', 'moduleType'], as_index=False) \
                               .cumcount() + 1

    # S_ 各模組最後一筆，以及查址模組全部，是真正需要的資料
    self.set_where(1, '篩出要保留的資料')
    info_df['keep'] = 0

    info_df.loc[info_df.groupby(['respondentId', 'moduleType'], as_index=False)
                    .nth(-1).index, 'keep'] = 1

    info_df.loc[(info_df.responseStatus == 'finished') &
                (info_df.moduleType == 'visitReport'), 'keep'] = 1

    # S_ timestamp
    self.set_where(1, '處理日期時間欄位')
    info_df['createdTimeStamp'] = pd.to_datetime(info_df.createdTimeStamp, unit='us') \
        .dt.tz_localize('UTC') \
        .dt.tz_convert('Asia/Taipei') \
        .dt.strftime('%Y-%m-%d %H:%M:%S')
    info_df['lastChangedTimeStamp'] = pd.to_datetime(info_df.lastChangedTimeStamp, unit='us') \
        .dt.tz_localize('UTC') \
        .dt.tz_convert('Asia/Taipei') \
        .dt.strftime('%Y-%m-%d %H:%M:%S')

    # S_ 產生錄音檔連結
    self.set_where(1, '產生錄音檔連結')
    info_df['audioLink'] = info_df.apply(self.public_audio_link, axis=1)

    self.info_df = info_df


def process_progress_df(self):
    self.set_where(0, '處理受訪者進度資料')

    progress_df = self.info_df[self.info_df.responseStatus == 'finished']
    progress_df = progress_df.groupby('respondentId')['moduleType'].value_counts() \
        .reset_index(name='count')
    progress_df = pd.pivot_table(progress_df, index='respondentId', columns='moduleType',
                                 values='count', fill_value=0).reset_index()

    self.progress_df = progress_df


def wide_question_id(row):
    question_id = row['questionId']
    if row['moduleType'] == 'visitReport':
        question_id = f"{row['moduleType']}__{row['idInGroup']}__{question_id}"
    else:
        question_id = f"{row['moduleType']}__{question_id}"

    if row['isNote']:
        question_id += '__note_' + str(row['noteOf'])

    return question_id


def process_wide_df(self):
    self.set_where(0, '轉成受訪者回覆資料')

    # S_ long to wide
    keep_df = self.info_df.loc[self.info_df.keep == 1, ['responseId', 'idInGroup']]

    wide_df = keep_df.merge(self.response_df, how='left')

    # NOTE 去掉只點進問卷，沒有任何作答
    wide_df = wide_df[wide_df.surveyId.notnull()].reset_index()

    wide_df.drop(columns=['responseStatus', 'answerStatus', 'lastChangedTimeStamp'],
                 inplace=True)

    wide_df['questionId'] = wide_df.apply(wide_question_id, axis=1)

    wide_df.drop(columns=['responseId', 'idInGroup', 'interviewerId', 'moduleType',
                          'isNote', 'noteOf'], inplace=True)

    wide_df.sort_values(
        ['respondentId', 'questionId'],
        ignore_index=True,
        inplace=True)

    wide_df = wide_df.pivot(
        index=['respondentId', 'surveyId'], columns='questionId', values='answerValue'). \
        reset_index()

    self.wide_df = wide_df


def process_download_link(self):
    self.set_where(0, '上傳並更新下載連結')

    # S_ 上傳到資料庫，並產生連結
    self.set_where(1, '上傳到資料庫，並產生連結')
    now = datetime.now(tw_tz).strftime('%Y-%m-%d_%H.%M.%S')

    info_path = f'response/{self.gsid}/{now}/responses_info_{now}.csv'
    info_url = self.bucket.df_to_storage(self.info_df, info_path)
    response_path = f'response/{self.gsid}/{now}/module_responses_{now}.csv'
    response_url = self.bucket.df_to_storage(self.response_df, response_path)
    progress_path = f'response/{self.gsid}/{now}/respondent_progress_{now}.csv'
    progress_url = self.bucket.df_to_storage(self.progress_df, progress_path)
    wide_path = f'response/{self.gsid}/{now}/respondent_responses_{now}.csv'
    wide_url = self.bucket.df_to_storage(self.wide_df, wide_path)

    # S_ 更新設定檔連結
    self.set_where(1, '更新設定檔連結')
    worksheet = self.spreadsheet.worksheet_by_title('說明')

    set_cell(worksheet, 'A7', '下載模組回覆', url=response_url, font_size=24,
             horizontal_alignment='center')
    set_cell(worksheet, 'A8', '下載受訪者回覆', url=wide_url, font_size=24,
             horizontal_alignment='center')
    set_cell(worksheet, 'A9', '下載回覆資訊', url=info_url, font_size=24,
             horizontal_alignment='center')
    set_cell(worksheet, 'A10', '下載受訪者進度', url=progress_url, font_size=24,
             horizontal_alignment='center')
