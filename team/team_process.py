from common.common import *


def init_process(self, gsid):
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
    self.get_info_dict('單位資訊')
    self.info_dict['teamId'] = gsid

    # S_ 檢查資訊頁內容是否正確
    self.check_team_valid()


def update_team_process(self):
    # S_ 更新 team
    # NOTE team/{teamId}
    self.batch.set(self.db.document('team', self.gsid), self.info_dict)

    # S_ 更新訪員帳號
    self.update_interviewer_list()

    # S_ 批次同步
    self.set_where(0, '批次同步')
    self.batch.commit()


def delete_team_process(self):
    gsid = self.gsid

    # S_ 刪除單位設定
    # NOTE team/{teamId}
    self.set_where(0, '刪除單位設定')
    self.batch.delete(self.db.document('team', gsid))

    # S_ 刪除訪員帳號
    # NOTE interviewerList/{teamId}
    self.set_where(0, '刪除訪員帳號')
    self.batch.delete(self.db.document('interviewerList', gsid))

    # S_ 刪除底下的專案
    # NOTE project/{projectId}
    self.set_where(0, '刪除底下的專案')
    query_docs = self.db.collection('project') \
        .where('teamId', '==', gsid) \
        .stream()
    self.batch.delete_docs(query_docs)

    # S_ 刪除底下的問卷
    # NOTE survey/{surveyId}
    self.set_where(0, '刪除底下的問卷')
    query_docs = self.db.collection('survey') \
        .where('teamId', '==', gsid) \
        .stream()

    for doc in query_docs:
        self.batch.delete(doc.reference)

        # S_ 刪除 storage 中的問卷
        self.bucket.delete_file(f'survey/{doc.id}/try.json')
        self.bucket.delete_file(f'survey/{doc.id}/{doc.id}.json')

    # S_ 刪除底下的問卷模組
    # NOTE surveyModule/{surveyModuleId}
    self.set_where(0, '刪除底下的問卷模組')
    query_docs = self.db.collection('surveyModule') \
        .where('teamId', '==', gsid) \
        .stream()
    self.batch.delete_docs(query_docs)

    # S_ 刪除相關 respondentList
    # NOTE interviewerRespondentList/{interviewerId_surveyId}
    self.set_where(0, '刪除底下的受訪者')
    query_docs = self.db.collection('interviewerRespondentList') \
        .where('teamId', '==', gsid) \
        .stream()
    self.batch.delete_docs(query_docs)

    # S_ 刪除相關 referenceList
    # NOTE interviewerReferenceList/{interviewerId_surveyId}
    self.set_where(0, '刪除底下的參考作答')
    query_docs = self.db.collection('interviewerReferenceList') \
        .where('teamId', '==', gsid) \
        .stream()
    self.batch.delete_docs(query_docs)

    # S_ 刪除所有回覆
    # NOTE surveyResponse
    self.set_where(0, '刪除所有回覆')
    query_docs = self.db.collection('surveyResponse') \
        .where('teamId', '==', gsid) \
        .stream()
    self.batch.delete_docs(query_docs)

    # TODO 刪除所有錄音檔
    # self.set_where(0, '刪除所有錄音檔')

    # S_ 批次同步
    self.set_where(0, '批次同步')
    self.batch.commit()
