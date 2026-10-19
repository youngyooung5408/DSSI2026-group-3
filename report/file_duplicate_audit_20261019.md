# 重複檔案整理與議員CSV格式修正

## 2026-10-20 已執行整理

- 移除11份位元組完全相同的副本，合計6,072,601 bytes（5.79 MiB）。刪除前逐份比較內容相等。
- 保留每筆來源URL、日期、archive member及查核脈絡；多筆來源紀錄可以指向同一份保存檔。
- 更新程式、資料索引、manifest、CSV來源欄與固定SHA-256綁定。raw來源正文未改寫，只有相同副本移除及metadata路徑更新。
- 保留歷史資料版本；兩份當時與來源擷取快照相同的輸出改直接引用該快照。
- 只整理本次核對的現存副本；未修改下載器的全域快取策略，重新下載仍可能產生副本。

## 保存路徑對照

| 已移除副本 | 保存路徑 |
| --- | --- |
| `data/raw/background_expansion_20261019/a36fb7c7ce76ca27fd07.source` | [data/raw/council_review_20261019/xu_bulletin_2022.pdf](../data/raw/council_review_20261019/xu_bulletin_2022.pdf) |
| `data/processed/candidate_background_source_pages_20261019.csv` | [data/processed/snapshots/source_extraction_20261019/candidate_background_source_pages_20261019.csv](../data/processed/snapshots/source_extraction_20261019/candidate_background_source_pages_20261019.csv) |
| `data/processed/council_education_source_leads_20261019.csv` | [data/processed/snapshots/source_extraction_20261019/council_education_source_leads_20261019.csv](../data/processed/snapshots/source_extraction_20261019/council_education_source_leads_20261019.csv) |
| `data/raw/career_expansion_20261019/fff69c0c06e8ba50d093.source` | [data/raw/social_followup_round6_20261019/fff69c0c06e8ba50d093.html](../data/raw/social_followup_round6_20261019/fff69c0c06e8ba50d093.html) |
| `data/raw/background_expansion_20261019/423278c9fc97482ccf61.source` | [data/raw/candidate_websites_20261017/010_candidate_website.html](../data/raw/candidate_websites_20261017/010_candidate_website.html) |
| `data/raw/background_expansion_20261019/0a3c61e17821ee90df2b.source` | [data/raw/round3_20261019/0a3c61e17821ee90df2b.source](../data/raw/round3_20261019/0a3c61e17821ee90df2b.source) |
| `data/raw/background_expansion_20261019/89387de37ec1d9313a9a.source` | [data/raw/candidate_websites_20261017/011_candidate_website.html](../data/raw/candidate_websites_20261017/011_candidate_website.html) |
| `data/raw/identity_followup_20261019/a898038ddbed35271eaf.html` | [data/raw/identity_followup_20261019/64fbcee5c646c495e8a3.html](../data/raw/identity_followup_20261019/64fbcee5c646c495e8a3.html) |
| `data/raw/cec_all_offices/043_elcand.csv` | [data/raw/cec_all_offices/042_elcand.csv](../data/raw/cec_all_offices/042_elcand.csv) |
| `data/raw/identity_followup_20261019/0d72576b6c0368207f77.html` | [data/raw/mayor_birth_followup_20261019/wen_cna.html](../data/raw/mayor_birth_followup_20261019/wen_cna.html) |
| `data/raw/identity_followup_20261019/4e383d63bf8f41b03895.html` | [data/raw/mayor_birth_followup_20261019/wen_cna.html](../data/raw/mayor_birth_followup_20261019/wen_cna.html) |

## 議員登記CSV

- 43筆姓名欄含換行；全部共51個儲存格僅將排版換行改為空格。清理後每筆候選人佔一行。
- 1,502筆、16欄、candidate_key唯一；1,503個實體行（含表頭）。從兩份raw表格JSON獨立重建所有資料列，與保存CSV完全一致。
- `party_recommendation_joined`完全不變；原文字欄的政黨排版換行僅改為空格，不將「無」改為其他標籤。
- 產生Notebook同步加入換行清理，raw PDF及table JSON保留原始排版。
- 本次未執行完整Notebook；已清除修改之處理cell舊輸出並註記，其他Notebook執行輸出標示為先前紀錄。

## 提交狀態

本次尚未stage、commit或push；舊安全清理提交清單不足以涵蓋本次擴充範圍，提交前須重新檢查。
