# 說明

## cloud storage 設定

- cloud storage 預設會有網域的限制，所以要：
  1. 創立 cors.json，並輸入：
     ```json
     [
       {
         "origin": ["*"],
         "method": ["GET"],
         "maxAgeSeconds": 3600
       }
     ]
     ```
  2. 送出指令 `gsutil cors set cors.json gs://{你的bucket名稱}/`

  - [參考](https://stackoverflow.com/questions/37760695/firebase-storage-and-access-control-allow-origin/37765371)


- Rules 設定：
  1. 初始化 Firebase storage 時會自動創立 storage.rules
  2. 編輯後送出指令 `firebase deploy --only storage`

  - [設定內容參考](https://firebase.google.com/docs/rules/basics)
  - [deploy參考](https://firebase.google.com/docs/rules/manage-deploy)