
from common import *


class Quiz:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

    def create(self, email):
        # NOTE 連接模板
        template_id = '1kFso7_L21vzRpeeHDgpl9HLAlP8SSVZ_vgpH_qQvS3I'
        template_spreadsheet = self.gsheets.open_by_key(template_id)

        # NOTE 創立新的 spreadsheet
        spreadsheet = self.gsheets.create('新建立之測驗設定檔(可自訂名稱)')

        # NOTE 從模板複製到新創立的 spreadsheet
        for i in range(5):
            worksheet = template_spreadsheet.worksheet('index', i).copy_to(spreadsheet.id)
            worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

        # NOTE 刪除初始 worksheet
        sheet1 = spreadsheet.worksheet_by_title('Sheet1')
        spreadsheet.del_worksheet(sheet1)

        # NOTE "更新此測驗"連結
        worksheet = spreadsheet.worksheet_by_title('說明')
        update_url = '{}?update_type=quiz_all&quiz_id={}'.format(main_url, spreadsheet.id)
        worksheet.update_value('A3', '=HYPERLINK("{}", "更新此測驗")'.format(update_url))

        # NOTE 清空 "連結專案 ID"
        worksheet = spreadsheet.worksheet_by_title('測驗資訊')
        worksheet.update_value('B3', '')

        # TAG 寫入 Firestore
        result_message = self.update(gsid=spreadsheet.id)

        # NOTE 設定分享權限
        spreadsheet.share(email, 'writer', emailMessage='新建立之測驗設定檔')
        # TODO 到時我的權限可拿掉
        spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage='新建立之測驗設定檔')
        # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)  # NOTE 轉移所有權

        if result_message == '更新測驗成功!':
            return '新建立之測驗設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {}'.format(spreadsheet.url)

        else:
            return '建立測驗失敗!'

    def update(self, gsid):
        try:
            # NOTE 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # NOTE 提取資訊
            # TODO 處理日期 https://api.dart.dev/stable/2.9.0/dart-core/DateTime/parse.html
            quiz_df = get_worksheet_df(spreadsheet, worksheet_title='測驗資訊')
            quiz_df['info_name'] = ['name', 'projectId', 'startTime', 'endTime']
            quiz_dict = quiz_df.set_index('info_name').T.to_dict('records')[0]

            # NOTE TODO 檢查輸入的內容是否符合格式
            for k, v in quiz_dict.items():
                if k in ['name', 'projectId'] and not v:
                    return '測驗名稱或連結專案 ID 不能為空!'

            # TAG 更新 quiz
            # EXAMPLE
            '''
            quiz / {gsid} / {
                projectId: 'demo_project_id',
                name: '範例測驗',
                startTime: '2/20/2020 0:00:00',
                endTime: null
            }
            '''
            dict_to_firestore(quiz_dict, self.db.document('quiz', gsid))

            # TAG 更新 question_list
            # EXAMPLE
            '''
            quiz / {gsid} / {
                list: [
                    {id: '1', body: 'Question 1', answer: 'O'},
                    ...
                ]
            }
            '''
            question_list_df = get_worksheet_df(spreadsheet, worksheet_title='題庫')
            question_list_dict = df_to_dict(question_list_df, ['id', 'body', 'answer'])
            dict_to_firestore(question_list_dict, self.db.document('question_list', gsid))

            # TAG 更新 interviewer_quiz
            project_id = quiz_dict['projectId']
            self.update_interviewer_quiz(project_id=project_id, gsid=gsid, quiz_dict=quiz_dict)

        except:
            return '更新測驗失敗!'

        return '更新測驗成功!'

    def update_interviewer_quiz(self, project_id, gsid, quiz_dict):
        interviewer_dict = self.db.document('interviewer', project_id).doc_to_dict()
        interviewer_list = interviewer_dict['list']

        batch = self.db.batch()

        for interviewer in interviewer_list:
            # EXAMPLE
            '''
            interviewer_quiz / id001_demo_project_id / {
                interviewerId: 'id001',
                projectId: 'demo_project_id',
                'quizList': [{
                    startTime: (timestamp),
                    endTime: null,
                    id: 'xxxxxxxxxxxxxxxxxxxxxx',
                    name: '範例測驗',
                    isFinished: false
                }, ...]
            }
            '''
            interviewer_ref = self.db.document('interviewer_quiz', '{}_{}'.format(interviewer['id'], project_id))

            old_dict = interviewer_ref.doc_to_dict()

            new_quiz_dict = quiz_dict.copy()
            new_quiz_dict.pop('projectId')
            new_quiz_dict['id'] = gsid
            tw_tz = pytz.timezone('Asia/Taipei')  # NOTE 設定時區
            if new_quiz_dict['startTime']:
                new_quiz_dict['startTime'] = parse(new_quiz_dict['startTime']).astimezone(tw_tz)
            if new_quiz_dict['endTime']:
                new_quiz_dict['endTime'] = parse(new_quiz_dict['endTime']).astimezone(tw_tz)
            new_quiz_dict['isFinished'] = False

            if not old_dict:
                batch.set(interviewer_ref, {
                    'interviewerId': interviewer['id'],
                    'projectId': project_id,
                    'quizList': [new_quiz_dict]
                })
            else:
                old_quiz_list = old_dict['quizList']

                new_quiz_list = []
                for quiz in old_quiz_list:
                    if quiz['id'] != gsid:
                        new_quiz_list.append(quiz)
                    else:
                        new_quiz_dict['isFinished'] = quiz['isFinished']  # NOTE 維持原本的完成狀態

                new_quiz_list.append(new_quiz_dict)

                batch.update(interviewer_ref, {
                    'interviewerId': interviewer['id'],
                    'projectId': project_id,
                    'quizList': new_quiz_list
                })

        batch.commit()

    def update_result(self, gsid, project_id=None, interviewer_id=None):
        try:
            if project_id and interviewer_id:
                # NOTE 寫入到 interviewer_quiz
                doc_ref = self.db.document('interviewer_quiz', f'{interviewer_id}_{project_id}')
                quiz_list_dict = doc_ref.doc_to_dict()

                old_quiz_list = quiz_list_dict['quizList']

                new_quiz_list = []
                for quiz in old_quiz_list:
                    if quiz['id'] == gsid:
                        new_quiz = quiz.copy()
                        new_quiz['isFinished'] = True  # TODO 這邊先直接寫 True
                        new_quiz_list.append(new_quiz)
                    else:
                        new_quiz_list.append(quiz)

                doc_ref.update({
                    'quizList': new_quiz_list
                })

            # NOTE 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # NOTE query 資料
            quiz_result_query = self.db.collection('quiz_result') \
                .where('quizId', '==', gsid) \
                .where('isFinished', '==', True)

            quiz_result_dict = quiz_result_query.query_to_dict()

            if quiz_result_dict:
                # NOTE 資料處理
                wide_dict = defaultdict(dict)
                tw_tz = pytz.timezone('Asia/Taipei')  # NOTE 設定時區
                for key, value in quiz_result_dict.items():
                    wide_dict[key]['reply_id'] = key
                    wide_dict[key]['interviewer_id'] = value['interviewer']['id']
                    wide_dict[key]['interviewer_name'] = value['interviewer']['name']
                    wide_dict[key]['total_right_score'] = value['score']['right']
                    wide_dict[key]['total_wrong_score'] = value['score']['wrong']
                    wide_dict[key]['upload_timestamp'] = value['serverTimeStamp'].astimezone(tw_tz).replace(tzinfo=None)

                    for question_id, score in value['scoreHistory']['scoreHistory'].items():
                        wide_dict[key]['question_id_{}'.format(question_id)] = score

                wide_df = pd.DataFrame.from_dict(wide_dict, orient='index')

                id_cols = ['reply_id', 'interviewer_id', 'interviewer_name',
                           'total_right_score', 'total_wrong_score', 'upload_timestamp']
                long_df = wide_df.melt(id_vars=id_cols, var_name='question_id', value_name='score')

                long_df = long_df[long_df.score.notnull()]
                long_df['score'] = long_df.score.astype(int)
                long_df['question_id'] = long_df.question_id.str.replace('question_id_', '')

                long_df = long_df.sort_values(by=['upload_timestamp', 'question_id'])

                wide_df = long_df.copy()
                wide_df['question_id'] = 'question_id_' + long_df.question_id
                wide_df = wide_df.pivot_table(index=id_cols, columns='question_id', values='score').reset_index()

                # NOTE 寫入 spreadsheet
                long_sheet = spreadsheet.worksheet_by_title('測驗紀錄_long')
                wide_sheet = spreadsheet.worksheet_by_title('測驗紀錄_wide')
                long_sheet.clear()
                long_sheet.set_dataframe(long_df, 'A1', nan='')
                wide_sheet.clear()
                wide_sheet.set_dataframe(wide_df, 'A1', nan='')
        except:
            return '更新測驗紀錄失敗!'

        return '更新測驗紀錄成功!'
