# GitHub更新與比較分支（2026-11-08）

> **後續樣本更新**：本報告比對時本機為209人；學生其後暫納入游智彬，現行兩市研究版為210人，與本報告當時GitHub兩市202人差8人。[新版分群與敏感度](taipei_kaohsiung_g5_g6_yu_provisional_20261108.md)。以下保留當次209人比較紀錄。

作者：RUEI-HSIANG, CHANG／張睿庠（B12303030；AI協助）。核對時間：2026-11-08 18:06:01 Asia/Taipei。

依學生本次明確要求，查GitHub新提交，並建立獨立比較分支。**本地及GitHub分支均已建立並回讀核對；沒有將新資料合併進現有分群。**
GitHub connector可讀取此repo，但建立分支回403 `Resource not accessible by integration`；改用本機既有Git憑證建立遠端分支成功，再由GitHub API獨立核對。

## 新提交

本機原`main`為`c800beb13865fc8e481b2beea19143a075848225`；GitHub `main`為`c93097f08b3c6b12118f944401806261f94aaedb`。GitHub compare確認ahead 2、behind 0，共改6個檔案。

| Commit | Asia/Taipei提交時間 | 實際內容 |
| --- | --- | --- |
| [57e164f](https://github.com/youngyooung5408/DSSI2026-group-3/commit/57e164fe6b798f1f73300af57e34f1c3a8413ab3) | 2026-11-08 16:35:12 | 新增G1–G6範圍合併Notebook、分析／排除／缺口CSV與學生決定檔；原280人，排除9人後271人。 |
| [c93097f](https://github.com/youngyooung5408/DSSI2026-group-3/commit/c93097f08b3c6b12118f944401806261f94aaedb) | 2026-11-08 16:36:59 | 更新PROJECT.md成員與貢獻紀錄。 |

[固定兩提交比較](https://github.com/youngyooung5408/DSSI2026-group-3/compare/c800beb13865fc8e481b2beea19143a075848225...c93097f08b3c6b12118f944401806261f94aaedb)；[比較分支與目前main](https://github.com/youngyooung5408/DSSI2026-group-3/compare/compare/tk-g5-g6-20261108...main)。

## 分支狀態

- 本地目前分支：`compare/tk-g5-g6-20261108`，HEAD=`c800beb13865fc8e481b2beea19143a075848225`。
- [GitHub比較分支](https://github.com/youngyooung5408/DSSI2026-group-3/tree/compare/tk-g5-g6-20261108)：`c800beb13865fc8e481b2beea19143a075848225`，已成功發布並以GitHub branches API回讀核對。
- 本地`main`仍為`c800beb13865fc8e481b2beea19143a075848225`；GitHub `main`仍為`c93097f08b3c6b12118f944401806261f94aaedb`。未merge、rebase或更新任何研究輸入。
- **此遠端分支目前保存的是原有commit基準，不是未提交的209人分群檔快照。** 工作目錄的資料、Notebook及報告仍未commit，不會因建立分支而自動上傳。
- 建分支前後23個關鍵輸入／結果檔SHA完全相同；後續新增本比較報告及文字維護不改分群CSV。

## 兩版資料的實際差異

GitHub[新分析檔](https://github.com/youngyooung5408/DSSI2026-group-3/blob/c93097f08b3c6b12118f944401806261f94aaedb/data/processed/candidates_scope_g1_g6_20261108.csv)不是本機209人資料的單純更新版；樣本範圍與缺值政策不同。

| 項目 | 本機已執行G5／G6分群 | GitHub新合併資料 |
| --- | --- | --- |
| 地理／公職範圍 | 臺北＋高雄，兩市首長及議員 | 全國首長＋臺北／高雄議員 |
| 總人數 | 209＝兩市首長11＋議員198 | 271＝全國首長80＋兩市議員191 |
| 只看臺北／高雄 | 209 | 202 |
| 兩市G5缺值 | 0 | 3 |
| 兩市G6缺值 | 0 | 175 |
| 全檔G6缺值 | 0 | 229 |
| 本輪缺值刪除條件 | 僅G5或G6缺值才排除，實際0人 | 依學生決定檔排除9人，主要為年齡／學歷資料不足 |

201位候選人同時在兩版的兩市樣本內。共同候選人的不同格數：年齡18、學歷19、G5有3、G6有174；性別與政黨0。
共同候選人的G5／G6凡兩邊都有編碼者，沒有0／1衝突；G5的3格與G6的174格差異，均為GitHub空白而本機已有值。
這不表示兩版全部背景欄位一致，也不是對來源真實性的新增認證。

本機保留、GitHub排除的8位兩市候選人：林揚庭、左曉明、許原榮、熊羿、譚傳紹、李奇峯、孔垂崢HaisulIslituan、李傅鈺婷。本次僅用G5／G6，不依年齡或學歷缺值剔除他們。
GitHub新檔另外含游智彬；本機準備檔依既有資格稽核排除他。這是兩版保存樣本的差異，未在本輪重審資格。
魏造文是GitHub排除的第9位，屬基隆，不在本機兩市209人內，不能把他算進兩市人數差。

## 新資訊可供後續查核

GitHub有7位本機仍缺年齡者的人工值：

| 姓名 | 本機年齡 | GitHub年齡 |
| --- | --- | ---: |
| 陳彥廷 | 缺值 | 43 |
| 何恕懷 | 缺值 | 38 |
| 鄧樂強 | 缺值 | 61 |
| 李惠暄 | 缺值 | 43 |
| 賴俊翰 | 缺值 | 44 |
| 王振庭 | 缺值 | 27 |
| 李道翔 | 缺值 | 40 |

GitHub學生決定檔的18筆補值目前全部沒有`source_url`。其Notebook也明示來源網址待補；上述值是組員提供的人工查核結果，尚未在本輪核對原始來源。
另外有陳彥廷、何恕懷、李道翔學歷分類差異，以及李文的非空學歷衝突（本機研究所、GitHub大學以下）。
這些可作下一輪核對清單；不直接覆寫已有來源，也不因遠端commit較新就重跑分群。本次G5／G6結果保持原版。

## 驗證與限制

本輪讀完新merge Notebook的程式與說明，檢查保存輸出，並直接載入GitHub的271人CSV、9人排除表、37格缺口表及27筆學生決定檔。
5份下載內容已按Git blob SHA-1逐檔核對；下列SHA-256記錄本輪檢視版本。副本存repo外暫存區，未註冊為正式分析輸入、未覆寫data/processed。
新merge Notebook未重新執行；其執行紀錄屬既有保存輸出。本輪實際執行的是CSV範圍、鍵、缺值及同鍵逐欄比較。
本機Git會對`.git/objects/pack/._pack-*.idx`發出`non-monotonic index`警告；本輪未清理Git內部檔案。分支push exit=0，GitHub回讀分支與main的SHA也核對通過。

| GitHub固定commit內路徑 | 本輪副本SHA-256 |
| --- | --- |
| `data/code/merge_scope_g1_g6_20261108.ipynb` | `ba9d664eeba4bafea895d1df6cc9f0ca072c6ebb1c0da283f18180365ecef6ae` |
| `data/processed/candidates_scope_g1_g6_20261108.csv` | `1cecbebba4480c3b07b37f4c92eb38793cbc521ec5b052e32f8c87fb19855a43` |
| `data/processed/candidates_scope_g1_g6_excluded_20261108.csv` | `b02e425259c8b3759abdbf67b42f1d9dd6c4b4020e22f70f1d248825eec6de29` |
| `data/processed/candidates_scope_g1_g6_gaps_20261108.csv` | `7beda58f25fc2dfb6af33480e2896171dd97f3732cd7d221eb4b6a34b00f971d` |
| `data/raw/student_decisions_20261108/scope_student_decisions_20261108.csv` | `c7c11e8f98cefb1ad964832a0e149dd102a37fcc9567264bd2a742eeb0eae6c3` |

## 後續與交付狀態

比較分支已可使用；本輪不提交研究資料、Notebook或報告。先比較樣本／排除規則，再決定哪些有來源的新背景值要整合。
若要在GitHub上看到目前的209人分群檔，仍需學生檢查並commit到`compare/tk-g5-g6-20261108`後再push；目前分支頁只會看到原commit基準。
本報告與PROJECT.md文字維護尚待提交；建立分支不等於研究成果已提交。
