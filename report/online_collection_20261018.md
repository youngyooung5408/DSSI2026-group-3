# 議員、立委與 Meta 資料蒐集紀錄

- 蒐集日期：2026-10-18（台灣時間）
- 本次協作學生：張睿庠／RUEI-HSIANG, CHANG，B12303030
- 範圍：依使用者「都抓」指示，蒐集2026議員候選人、現任地方議員及立法委員名錄；另測試Meta相關資料入口。這是資料準備，尚無策略比較結果。

## 已保存的線上資料

| 資料 | 實際列數 | 來源與解讀 |
| --- | ---: | --- |
| 2026議員候選人登記 | 1,502 | [中選會發布頁](https://web.cec.gov.tw/central/article/64709)；直轄市610、縣市892；22縣市；兩份PDF共66頁，製表日2026-09-07 |
| 內政部議員名錄 | 872 | [直轄市議員](https://www.moi.gov.tw/LocalOfficial.aspx?n=573&TYP=KND0001)356人、[縣市議員](https://www.moi.gov.tw/LocalOfficial.aspx?n=574&TYP=KND0002)516人；22縣市 |
| 第11屆立委名錄 | 123 | [立法院官方頁](https://www.ly.gov.tw/Pages/List.aspx?nodeid=109)；現任區113、離職區10，分欄保存 |
| Meta平台工作單 | 243 | 既有81位縣市長登記者×Facebook／Instagram／Threads；不是243個已驗證帳號 |
| Meta存取紀錄 | 13 | 4個工具／說明入口、9次候選人Facebook連結測試；不是13筆貼文 |

議員登記資料保存公職類別、縣市、選區、登記日期、姓名原文、推薦政黨原文、備註、來源頁碼與網址。另欄移除姓名及政黨名稱中的排版空白；未把推薦政黨轉成黨籍。原PDF、逐頁表格JSON均保留。

內政部表是擷取時名錄列示狀態，不是逐人任免證明；個人頁連結可供後續查生日、學經歷與任期。尚未核對資料異動與法定席次，任期起訖留空。立委名錄不含完整學經歷，保存個人頁供續查，不宣稱背景已完整。舊站ID9 API先發生舊TLS相容問題，啟用相容握手且保留憑證驗證後仍回403，改採官方本屆名錄。

三種名冊未自動以姓名合併，未把立委納入2026地方選舉樣本，也未把內政部列示的議員全部視為2026參選者。最終資格、身分與納入規則仍須核對。

## Meta取得情形

1. **自然貼文**：測試既有官方來源連出的Facebook網址。九次回應為HTTP 200，但解析可見內容只有頁名，未取得可驗證的貼文ID、時間、正文或完整分頁。保存回應供查核，貼文數、追蹤數與窗口統計均不填零。
2. **Meta Content Library／API**：入口回HTTP 200，但這次僅解析到頁面標題。另成功保存[Meta官方研究工具公告](https://about.fb.com/news/2023/11/new-tools-to-support-independent-research/)，其中說明Facebook／Instagram公開內容與Threads網頁介面。公告包含歷史更新；不能以舊公告推定目前申請流程、所有平台API權限或學校已有資格。本次未取得研究工具登入權限、未送申請。
3. **SOMAR**：回HTTP 403與驗證挑戰頁，未取得資料或目前費率，不能宣稱免費或已可使用。
4. **付費廣告**：成功保存[Ad Library API官方說明頁](https://www.facebook.com/ads/library/api/)。此入口說明政治／選舉等廣告的查詢與token流程，本次無授權token，因此尚無廣告明細。廣告支出區間與曝光區間須原樣保存，不能推算精確值或當作總競選支出。
5. **Instagram／Threads**：已建立逐人平台工作單；本次未新增驗證帳號或貼文，不能推定候選人沒有使用這兩個平台。工作單目前僅涵蓋原81位縣市長登記者，議員／立委平台帳號待擴充。

## 檔案與驗證

- [原始資料文件](../data/raw/online_20261018_documentation.ipynb)：逐檔hash、格式、原始樣本與限制。
- [整理Notebook](../data/code/prepare_council_and_meta_20261018.ipynb)：固定輸入版本、完整轉換、儲存後重讀核對。
- [整理後資料文件](../data/processed/online_20261018_documentation.ipynb)：每欄定義、前10列、筆數、缺失與唯一鍵驗證。
- [議員登記CSV](../data/processed/council_candidates_2026_registration.csv)、[內政部名錄CSV](../data/processed/current_councilors_20261018.csv)、[立委名錄CSV](../data/processed/legislators_term11_directory_20261018.csv)。
- [Meta帳號工作單](../data/processed/meta_candidate_account_worklist_20261018.csv)、[存取CSV](../data/processed/meta_access_attempts_20261018.csv)。

三份Notebook均已由乾淨kernel執行並保留輸出。資料準備通過不代表背景欄位、樣本資格或完整社群窗口已完成；沒有執行分群、假說檢定或分類模型。

## 報告與簡報銜接

報告保留既有設計及成員資訊，修正文句並補政治家族、行政經歷、議題類型的操作定義草案。新增定義、樣本分層與主要指標仍待組內確認；政治獻金假說依原稿保留為選後延伸。原稿「併辦核電公投」未取得本次支持依據，移除；投票日期以中選會來源核對。

五頁三分鐘簡報及逐字稿更新到10/18；名冊進度與社群限制同步。正式研究範圍仍須決定縣市長、地方議員如何分層，不能因為抓到立委名錄就自動改題。
