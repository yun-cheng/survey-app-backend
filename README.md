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

## Firestore 設定

- Rules 設定：
  1. 初始化 Firebase firestore 時會自動創立 firestore.rules
  2. 編輯後送出指令 `firebase deploy --only firestore`

  - [設定內容參考](https://firebase.google.com/docs/rules/basics)
  - [deploy參考](https://firebase.google.com/docs/rules/manage-deploy)

## 注意事項

- 有關 Firebase 的設定需先 cd 進 firebase 資料夾
- 若出現錯誤："firebase cannot be loaded because running scripts is disabled on this system."
  - 則先送出指令 `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Firestore batch

- batch.commit() 的 task 數量不能超過 500，而且可能有 bug，因此自己寫了一個 Batch 來處理