
from common import *


class Quiz:
    def __init__(self, gsheets, db):
        self.gsheets = gsheets
        self.db = db

    def create(self, email):
        try:
            # S_1-1 連接模板
            template_id = '1kFso7_L21vzRpeeHDgpl9HLAlP8SSVZ_vgpH_qQvS3I'
            template_spreadsheet = self.gsheets.open_by_key(template_id)

            # S_1-2 創立新的 spreadsheet
            spreadsheet = self.gsheets.create('新建立之測驗設定檔(可自訂名稱)')
            gsid = spreadsheet.id

            # S_1-3 從模板複製到新創立的 spreadsheet
            for i in range(5):
                worksheet = template_spreadsheet.worksheet('index', i).copy_to(gsid)
                worksheet.title = re.search(r'(?<=\s)\S+$', worksheet.title).group(0)

            # S_1-4 刪除初始 worksheet
            sheet1 = spreadsheet.worksheet_by_title('Sheet1')
            spreadsheet.del_worksheet(sheet1)

            # S_1-5 '更新此測驗設定' 連結
            worksheet = spreadsheet.worksheet_by_title('說明')
            update_url = f'{main_url}?action=update&on=quiz&gsid={gsid}'
            worksheet.update_value('A3', f'=HYPERLINK("{update_url}", "更新此測驗設定")')

            # S_1-6 '更新此測驗紀錄' 連結
            update_result_url = f'{main_url}?action=update&on=quiz_result&gsid={gsid}'
            worksheet.update_value('A4', f'=HYPERLINK("{update_result_url}", "更新此測驗紀錄")')

            # S_1-7 '刪除此測驗設定' 連結
            delete_url = f'{main_url}?action=delete&on=quiz&gsid={gsid}'
            worksheet.update_value('A5', f'=HYPERLINK("{delete_url}", "刪除此測驗設定")')

            # S_1-8 '刪除此測驗紀錄' 連結
            delete_result_url = f'{main_url}?action=delete&on=quiz_result&gsid={gsid}'
            worksheet.update_value('A6', f'=HYPERLINK("{delete_result_url}", "刪除此測驗紀錄")')

            # S_1-9 設定分享權限
            email_message = '新建立之測驗設定檔'
            spreadsheet.share(email, 'writer', emailMessage=email_message)
            # TODO 到時我的權限可拿掉
            spreadsheet.share('yuncheng.dev@gmail.com', 'writer', emailMessage=email_message)
            # NOTE 轉移所有權
            # spreadsheet.share('yuncheng.dev@gmail.com', 'owner', transferOwnership=True)

        except:
            return '建立測驗失敗!'

        return f'新建立之測驗設定檔連結已寄至信箱（可能會在垃圾郵件中....），或複製此連結進入：<br/><br/> {spreadsheet.url}'

    def update(self, gsid):
        try:
            # S_1-1 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_1-2 提取資訊
            # TODO 處理日期 https://api.dart.dev/stable/2.9.0/dart-core/DateTime/parse.html
            quiz_info = spreadsheet.worksheet_by_title('測驗資訊') \
                .get_values(start='C2', end='C4', include_all=True)

            quiz_info_dict = {
                'quizId': gsid,
                'quizName': quiz_info[0][0],
                'customProjectId': quiz_info[1][0],
                'customUnitId': quiz_info[2][0]
            }

            # S_1-3 檢查輸入的內容是否符合格式
            # S_1-3-1 檢查是否為空
            for k, v in quiz_info_dict.items():
                if not v:
                    return '測驗資訊不能為空!'

            # S_1-3-2 檢查連結的單位 ID、專案 ID 是否存在
            unit_query = self.db.collection('unit') \
                .where('customUnitId', '==', quiz_info_dict['customUnitId'])
            unit_dict = unit_query.query_to_dict(first=True)

            if unit_dict:
                quiz_info_dict['unitId'] = unit_dict['unitId']
                unit_gsid = unit_dict['unitId']
                quiz_info_dict.pop('customUnitId')
            else:
                return '找不到連結的單位 ID！'

            project_query = self.db.collection('project') \
                .where('customProjectId', '==', quiz_info_dict['customProjectId'])\
                .where('unitId', '==', unit_gsid)
            project_query_dict = project_query.query_to_dict(first=True)

            if project_query_dict:
                quiz_info_dict['projectId'] = project_query_dict['projectId']
                project_gsid = project_query_dict['projectId']
                quiz_info_dict.pop('customProjectId')
            else:
                return '找不到連結的專案 ID！'

            # S_1-3-3 檢查是否為重複的測驗名稱
            quiz_query = self.db.collection('quiz') \
                .where('projectId', '==', project_gsid) \
                .where('unitId', '==', unit_gsid)\
                .where('quizName', '==', quiz_info_dict['quizName'])
            quiz_query_dict = quiz_query.query_to_dict(first=True)

            if quiz_query_dict:
                return '同專案下，測驗名稱重複，請輸入其他名稱！'

            # S_2 更新 Firestore
            batch = self.db.batch()

            # S_2-1 更新 Firestore: quiz/{quizId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            quiz / {quizId} / {
                quizId: '1kFso7_L21vzRpeeHDgpl9HLAlP8SSVZ_vgpH_qQvS3I',
                quizName: '範例測驗',
                projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                unitId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8'
            }
            '''
            quiz_ref = self.db.document('quiz', gsid)
            batch.set(quiz_ref, quiz_info_dict)

            # S_2-2 更新 Firestore: quizList/{unitId}
            # TAG Firestore UPDATE
            # EXAMPLE
            '''
            quizList / {unitId} / {
                {projectId}: {
                    unitId: '1VRGeK8m-w_ZCjg1SDQ74TZ7jpHsRiTiI3AcD54I5FC8',
                    projectId: '1u1NdL7ZND_E3hU1jS2SNhhDIluIuHrcHpG4W9XyUChQ',
                    quizList: {
                        {quizId}: {
                            quizId: '1kFso7_L21vzRpeeHDgpl9HLAlP8SSVZ_vgpH_qQvS3I',
                            quizName: '範例測驗'
                        }
                    }
                }
            }
            '''
            quiz_list_dict = {
                'unitId': unit_gsid,
                'projectId': project_gsid,
                'quizList': {
                    gsid: {
                        'quizId': gsid,
                        'quizName': quiz_info_dict['quizName'],
                        'isFinished': False
                    }
                }

            }
            quiz_list_ref = self.db.document('quizList', unit_gsid)
            batch.set(quiz_list_ref, {
                project_gsid: quiz_list_dict
            }, merge=True)

            # S_2-3 更新 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore UPDATE
            # S_2-3-1 取得 interviewerList
            interviewer_list_ref = self.db.document('interviewerList', unit_gsid)
            interviewer_list_dict = interviewer_list_ref.doc_to_dict()

            # S_2-3-2 迴圈 interviewerList
            # TODO 刪除 interviewer 時的處理
            for k, v in interviewer_list_dict.items():
                # S_2-3-2-1 加入 interviewerId
                quiz_list_dict['interviewerId'] = k

                # S_2-3-2-2 取得舊資料，目的是提取測驗完成狀態
                interviewer_quiz_ref = self.db.document('interviewerQuiz', f'{k}_{project_gsid}')
                old_quiz_list_dict = interviewer_quiz_ref.doc_to_dict()

                if old_quiz_list_dict:
                    is_finished = old_quiz_list_dict['quizList'][gsid]['isFinished']
                    quiz_list_dict['quizList'][gsid]['isFinished'] = is_finished
                else:
                    quiz_list_dict['quizList'][gsid]['isFinished'] = False

                batch.set(interviewer_quiz_ref, quiz_list_dict, merge=True)

            # S_2-4 更新 Firestore: questionList/{quizId}
            # TAG Firestore SET
            # EXAMPLE
            '''
            questionList / {quizId} / {
                {questionId}: {
                    questionId: '1',
                    questionBody: 'Question 1',
                    answer: 'O'
                }
            }
            '''
            question_list_df = get_worksheet_df(spreadsheet, worksheet_title='題庫', end='C')
            question_list_dict = df_to_dict(question_list_df,
                                            new_column_names=['questionId', 'questionBody', 'answer'],
                                            index_column='questionId')

            question_list_ref = self.db.document('questionList', gsid)
            batch.set(question_list_ref, question_list_dict)

            batch.commit()

        except:
            return '更新測驗設定失敗!'

        return '更新測驗設定成功!'

    def update_result(self, gsid, project_gsid, interviewer_id):
        try:
            # S_1 更新 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore UPDATE
            # NOTE interviewerQuiz 該 interviewer isFinished 改 True
            if project_gsid and interviewer_id:
                interviewer_quiz_ref = self.db.document('interviewerQuiz', f'{interviewer_id}_{project_gsid}')
                quiz_list_dict = interviewer_quiz_ref.doc_to_dict()

                quiz_list_dict['quizList'][gsid]['isFinished'] = True

                interviewer_quiz_ref.set(quiz_list_dict, merge=True)

            # S_2 更新 spreadsheet
            # S_2-1 連接 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)

            # S_2-2 query quiz_result 資料
            quiz_result_query = self.db.collection('quizResult') \
                .where('quizId', '==', gsid) \
                .where('isFinished', '==', True)
            quiz_result_dict = quiz_result_query.query_to_dict()

            # S_2-3
            if quiz_result_dict:
                # S_2-3-1 資料處理
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
                        wide_dict[key][f'question_id_{question_id}'] = score

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

                # S_2-3-2 寫入 spreadsheet
                long_sheet = spreadsheet.worksheet_by_title('測驗紀錄_long')
                wide_sheet = spreadsheet.worksheet_by_title('測驗紀錄_wide')
                long_sheet.clear()
                long_sheet.set_dataframe(long_df, 'A1', nan='')
                wide_sheet.clear()
                wide_sheet.set_dataframe(wide_df, 'A1', nan='')
        except:
            return '更新測驗紀錄失敗!'

        return '更新測驗紀錄成功!'

    def delete(self, gsid):
        try:
            # S_1 刪除 Firestore
            batch = self.db.batch()

            # S_1-1 刪除 Firestore: quiz/{quizId}
            # TAG Firestore DELETE
            quiz_ref = self.db.document('quiz', gsid)
            quiz_dict = quiz_ref.doc_to_dict()
            unit_gsid = quiz_dict['unitId']
            project_gsid = quiz_dict['projectId']
            batch.delete(quiz_ref)

            # S_1-2 刪除 Firestore: quizList/{unitId}
            # TAG Firestore UPDATE
            quiz_list_ref = self.db.document('quizList', unit_gsid)
            batch.set(quiz_list_ref, {
                project_gsid: {
                    'quizList': {
                        gsid: firestore.DELETE_FIELD
                    }
                }
            }, merge=True)

            # S_1-3 刪除 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore UPDATE
            # NOTE 因為 gsid 有可能是數字開頭，所以必須要加上 ``
            interviewer_quiz_docs = self.db.collection('interviewerQuiz') \
                .where(f'quizList.`{gsid}`.quizId', '==', gsid) \
                .stream()

            for doc in interviewer_quiz_docs:
                doc_dict = doc.to_dict()
                doc_dict['quizList'][gsid] = firestore.DELETE_FIELD
                batch.set(doc.reference, doc_dict, merge=True)

            # S_1-4 刪除 Firestore: questionList/{quizId}
            # TAG Firestore DELETE
            question_list_ref = self.db.document('questionList', gsid)
            batch.delete(question_list_ref)

            batch.commit()

        except:
            return '刪除測驗設定失敗!'

        return '刪除測驗設定成功!'

    def delete_result(self, gsid):
        try:
            # S_1 更新 Firestore: interviewerQuiz/{interviewerId_projectId}
            # TAG Firestore UPDATE
            batch = self.db.batch()

            interviewer_quiz_docs = self.db.collection('interviewerQuiz') \
                .where(f'quizList.`{gsid}`.quizId', '==', gsid) \
                .where(f'quizList.`{gsid}`.isFinished', '==', True) \
                .stream()

            for doc in interviewer_quiz_docs:
                doc_dict = doc.to_dict()
                doc_dict['quizList'][gsid]['isFinished'] = False
                batch.set(doc.reference, doc_dict, merge=True)

            # S_1-4 刪除 Firestore: quizResult/{replyId}
            # TAG Firestore DELETE
            quiz_result_docs = self.db.collection('quizResult') \
                .where('quizId', '==', gsid) \
                .stream()

            for doc in quiz_result_docs:
                batch.delete(doc.reference)

            batch.commit()

            # S_2 清空 spreadsheet
            spreadsheet = self.gsheets.open_by_key(gsid)
            long_sheet = spreadsheet.worksheet_by_title('測驗紀錄_long')
            wide_sheet = spreadsheet.worksheet_by_title('測驗紀錄_wide')
            long_sheet.clear()
            wide_sheet.clear()

        except:
            return '刪除測驗設定失敗!'

        return '刪除測驗設定成功!'
