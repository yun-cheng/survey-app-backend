from common.common import *


class Survey:
    def __init__(self, gsheets, db, bucket):
        self.gsheets = gsheets
        self.db = db
        self.bucket = bucket
        self.batch = self.db.batch()
        self.team_gsid = ''
        self.project_gsid = ''
        self.gsid = ''
        self.translate_df = None
        self.respondent_df = None
        self.spreadsheet = None
        self.template_id = '17t0kixc-0AJy2YBFUtNcKiCJafmck5BZ1TGaIxTTPNU'
        self.info_dict = {}
        self.survey_dict = {}
        self.module_dict = {}
        self.reference_key_list = []
        self.interviewer_list = []
        self.where = [''] * 5
        self.where_list = []
        self.type = 'survey'

    from common.common import set_where, where_to_str, where_list_to_str
    from common.create import create, link_url
    from common.update import get_info_dict
    from common.check_valid import check_survey_valid, check_survey_field_value_not_occupied
    from common.translate import get_translate_df, translate
    from common.db_operation import get_team_dict, get_project_dict, get_survey_module_dict, \
        get_survey_dict, get_response_dict, get_all_responses_dict, get_respondent_response_dict, \
        batch_set_by_interviewer, get_survey_dict_from_field, set_survey, batch_delete_responses

    from .choice import create_choice_list, choice_import_to_df
    from .expression import reformat_expression
    from .table import process_table_question
    from .question import get_survey_question_list, get_recode_question_list, \
        get_survey_module_question_list, to_formatted_text_list
    from .update_subprocess import update_respondent_list, update_survey_question, \
        update_reference_list, transfer_respondents

    def init(self, gsid):
        # S_ 連接 spreadsheet
        self.set_where(0, '連接 spreadsheet')
        gsheets = self.gsheets
        self.gsid = gsid
        spreadsheet = gsheets.open_by_key(gsid)
        self.spreadsheet = spreadsheet

        # S_ 更新說明頁
        self.set_where(0, '更新說明頁')
        self.link_url()

        # S_ 取得翻譯表
        self.set_where(0, '取得翻譯表')
        self.get_translate_df()

        # S_ 提取資訊頁內容
        self.set_where(0, '提取資訊頁內容')
        self.get_info_dict('問卷資訊')
        self.info_dict['surveyId'] = gsid

        # S_ 檢查資訊頁內容是否正確
        self.check_survey_valid()

        # S_ survey_dict 架構
        self.survey_dict = {
            'teamId': self.team_gsid,
            'projectId': self.project_gsid,
            'surveyId': gsid,
            'customSurveyId': self.info_dict['customSurveyId'],
            'surveyName': self.info_dict['surveyName'],
            'module': defaultdict(dict),
            'moduleInfo': self.module_dict,
        }

    def update(self, gsid):
        try:
            self.init(gsid)

            # S_ 處理受訪者分頁內容
            self.update_respondent_list()

            # S_ 處理各個問卷模組資料表
            self.update_survey_question()

            # S_ 更新參考作答列表
            self.set_where(0, '更新參考作答列表')
            self.update_reference_list()

            # S_ 確認沒問題再一起 commit
            self.set_where(0, '批次上傳')
            self.batch.commit()
            self.set_survey()

            return f'更新問卷設定成功！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

        except:
            return f'更新問卷設定失敗！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'錯誤出現在：<br/>{self.where_to_str()}<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

    def transfer(self, gsid):
        try:
            self.init(gsid)

            self.transfer_respondents()

            # self.batch.commit()

            return f'轉出入成功！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

        except:
            return f'轉出入失敗！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'錯誤出現在：<br/>{self.where_to_str()}<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

    def delete_all_responses(self, gsid):
        try:
            self.init(gsid)

            self.batch_delete_responses()
            self.batch.commit()

            return f'清除資料庫所有回覆成功！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

        except:
            return f'清除資料庫所有回覆失敗！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'錯誤出現在：<br/>{self.where_to_str()}<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

    def update_download_files(self, gsid):
        try:
            self.init(gsid)

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

            response_dict = self.get_all_responses_dict()

            info_keys = ['responseId', 'respondentId', 'moduleType', 'responseStatus',
                         'interviewerId', 'surveyId', 'deviceId',
                         'createdTimeStamp', 'lastChangedTimeStamp']
            data_keys = ['responseId', 'respondentId', 'moduleType', 'responseStatus',
                         'interviewerId', 'surveyId']
            response_df = pd.DataFrame()
            info_list = []
            for response_id, response in response_dict.items():
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

            response_df = response_df[response_df.type != ''].reset_index(drop=True)
            response_df['lastChangedTimeStamp'] = pd.to_datetime(response_df.lastChangedTimeStamp,
                                                                 unit='us') \
                .dt.tz_localize('UTC') \
                .dt.tz_convert('Asia/Taipei') \
                .dt.strftime('%Y-%m-%d %H:%M:%S')

            # S_ info_df
            info_df = pd.DataFrame.from_dict(info_list)

            info_df.sort_values(
                ['respondentId', 'moduleType', 'lastChangedTimeStamp'],
                ignore_index=True,
                inplace=True)

            # S_ 模組內編號
            info_df['idInGroup'] = info_df \
                                       .groupby(['respondentId', 'moduleType'], as_index=False) \
                                       .cumcount() + 1

            # S_ 各模組最後一筆，以及查址模組全部，是真正需要的資料
            info_df['keep'] = 0

            info_df.loc[info_df.groupby(['respondentId', 'moduleType'], as_index=False)
                            .nth(-1).index, 'keep'] = 1

            info_df.loc[(info_df.responseStatus == 'finished') &
                        (info_df.moduleType == 'visitReport'), 'keep'] = 1

            # S_ timestamp
            info_df['createdTimeStamp'] = pd.to_datetime(info_df.createdTimeStamp, unit='us') \
                .dt.tz_localize('UTC') \
                .dt.tz_convert('Asia/Taipei') \
                .dt.strftime('%Y-%m-%d %H:%M:%S')
            info_df['lastChangedTimeStamp'] = pd.to_datetime(info_df.lastChangedTimeStamp,
                                                             unit='us') \
                .dt.tz_localize('UTC') \
                .dt.tz_convert('Asia/Taipei') \
                .dt.strftime('%Y-%m-%d %H:%M:%S')

            # S_ audio link
            def public_audio_link(row):
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

            info_df['audioLink'] = info_df.apply(public_audio_link, axis=1)

            # S_ 完成進度
            progress_df = info_df[info_df.responseStatus == 'finished']
            progress_df = progress_df.groupby('respondentId')['moduleType'].value_counts() \
                .reset_index(name='count')
            progress_df = pd.pivot_table(progress_df, index='respondentId', columns='moduleType',
                                         values='count', fill_value=0).reset_index()

            # S_ note
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

            # S_ long to wide
            keep_df = info_df.loc[info_df.keep == 1, ['responseId', 'idInGroup']]

            wide_df = keep_df.merge(response_df, how='left')

            # NOTE 去掉只點進問卷，沒有任何作答
            wide_df = wide_df[wide_df.surveyId.notnull()].reset_index()

            wide_df.drop(columns=['responseStatus', 'answerStatus', 'lastChangedTimeStamp'],
                         inplace=True)

            def wide_question_id(row):
                question_id = row['questionId']
                if row['moduleType'] == 'visitReport':
                    question_id = f"{row['moduleType']}__{row['idInGroup']}__{question_id}"
                else:
                    question_id = f"{row['moduleType']}__{question_id}"

                if row['isNote']:
                    question_id += '__note_' + str(row['noteOf'])

                return question_id

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

            # FIXME recode module answer value

            # S_ upload
            now = datetime.now(tw_tz).strftime('%Y-%m-%d_%H.%M.%S')

            info_path = f'response/{self.gsid}/{now}/responses_info_{now}.csv'
            info_url = self.bucket.df_to_storage(info_df, info_path)
            response_path = f'response/{self.gsid}/{now}/module_responses_{now}.csv'
            response_url = self.bucket.df_to_storage(response_df, response_path)
            progress_path = f'response/{self.gsid}/{now}/respondent_progress_{now}.csv'
            progress_url = self.bucket.df_to_storage(progress_df, progress_path)
            wide_path = f'response/{self.gsid}/{now}/respondent_responses_{now}.csv'
            wide_url = self.bucket.df_to_storage(wide_df, wide_path)

            # S_
            worksheet = self.spreadsheet.worksheet_by_title('說明')

            set_cell(worksheet, 'A6', '下載模組回覆', url=response_url, font_size=24,
                     horizontal_alignment='center')
            set_cell(worksheet, 'A7', '下載受訪者回覆', url=wide_url, font_size=24,
                     horizontal_alignment='center')
            set_cell(worksheet, 'A8', '下載回覆資訊', url=info_url, font_size=24,
                     horizontal_alignment='center')
            set_cell(worksheet, 'A9', '下載受訪者進度', url=progress_url, font_size=24,
                     horizontal_alignment='center')

            return f'更新下載資料成功！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'

        except:
            return f'更新下載資料失敗！請關閉視窗，避免頁面重整後重新送出更新請求。<br/><br/>' \
                   f'錯誤出現在：<br/>{self.where_to_str()}<br/><br/>' \
                   f'執行歷程：{self.where_list_to_str()}'
