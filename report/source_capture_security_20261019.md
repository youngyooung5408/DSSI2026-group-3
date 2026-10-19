# 網頁快照金鑰清理（2026-10-19）

## 四個警報的來源

| GitHub警報 | 快照來源 | 內容與狀態 |
| --- | --- | --- |
| [#1](https://github.com/youngyooung5408/DSSI2026-group-3/security/secret-scanning/1) | 競選網站 oen.tw；電子郵件指向8b170c870f2170688117.source | 本地地圖URL含Google API key；同一值也在另外2份oen快照 |
| [#2](https://github.com/youngyooung5408/DSSI2026-group-3/security/secret-scanning/2) | 華視新聞快照 f0ccfe475c8a37b154f6.source | 本地googleMapsApiKey設定；另一份華視快照也有相同值 |
| [#3](https://github.com/youngyooung5408/DSSI2026-group-3/security/secret-scanning/3) | 臺南市議會快照2b0861c3a2c5f49e357e.source，第149行 | 已在使用者登入的Safari核對：Google API Key、Validity Unknown、Publicly leaked、該位置在2a5838e |
| [#4](https://github.com/youngyooung5408/DSSI2026-group-3/security/secret-scanning/4) | 高雄市政府073b4b373ff6173a4278.html，第42行 | 本地Google Maps載入程式含key |

四個警報類型與位置由使用者貼文及Safari當前警報郵件核對；#3另實際開啟警報頁。#1、#2、#4未另逐頁驗證GitHub有效性狀態。7份已追蹤快照共4個不同Google key值、10個位置。沒有檢測或使用它們，也沒有證據把它們認定為使用者個人GitHub／OpenAI憑證。金鑰來自第三方網站程式碼；是否有效及限制範圍仍未知。

## 本地已完成

1. 原始7份bytes已逐檔SHA核對，私存於Git repo之外的使用者家目錄；私存檔不加入提交清單。
2. 公開來源副本只替換key值，保留其他bytes。來源manifest分列原始及公開SHA；履歷線索表的來源指紋、Notebook固定輸入、資料索引同步更新。
3. [安全轉換驗證Notebook](../data/code/source_capture_security_20261019.ipynb)逐檔以原始備份重算替換，確認除了10個key位置之外完全相同。
4. 受影響的第六輪處理／來源說明／資料說明及第九輪處理／資料說明重新執行；候選人背景數值與社群入口統計不變。
5. [只讀掃描器](../data/code/check_source_credentials.py)掃描目前追蹤檔案為0命中；同一掃描器對2a5838e舊commit仍可找到10個位置。掃描器從不輸出匹配值。
6. 新增.githooks/pre-commit防止暫存內容再次含指定憑證模式。hook檔已準備，尚未安裝；安裝需學生執行git config core.hooksPath .githooks。

## 尚未完成的遠端處理

- 這些修改尚未commit／push，GitHub最新版本尚未清理。
- 即使提交清理，舊commit 2a5838e仍會保留字串；本輪沒有重寫歷史、force push、刪除儲存庫或關閉警報。
- 原網站擁有者才能管理其key；本輪沒有撤銷或宣稱已撤銷。不要以「revoked」理由關閉尚未撤銷的金鑰。GitHub警報不會因新commit刪除字串而自動關閉。
- 若要移除Git歷史，需要另行協調共同作者、備份與歷史重寫範圍；不在這次一般修正提交中默默進行。

依據：[GitHub警報處理說明](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-secret-scanning-alerts/resolving-alerts)。
