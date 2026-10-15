# 📊 Visual Table Extraction & Canvas Grid Report

**Tool:** `18_paddleocr_img2table`  
**Action:** `visual_test_ocr`  
**Source Image:** `raw/embedded_table_image.png`  
**Extracted Rows:** **5** | **Columns:** **5**  
**Extraction Duration:** 2149.25 ms  
**Timestamp:** 2026-10-15 18:05:52 UTC

---

## 🗃️ Extracted Data Table
|   Problem ID | Title                   | Difficulty   | Acceptance   | Time Complexity   |
|-------------:|:------------------------|:-------------|:-------------|:------------------|
|            1 | Two Sum                 | Easy         | 52.4%        | O(N)              |
|           15 | 3Sum                    | Medium       | 34.2%        | O(N^2)            |
|           42 | Trapping Rain Water     | Had          | 62.1%        | O(N)              |
|          146 | LRU Cache               | Medium       | 43.8%        | O(1)              |
|          295 | Find Median from Stream | Hard         | 51.9%        | O(log N)          |

---

## 📐 Cell Coordinate Mapping
- Total Grid Cells Detected: **30**
- Output Formats: **JSON**, **CSV**, **Markdown**

---

## 📁 Output Artifacts
- **Raw Table Graphic:** `raw/embedded_table_image.png`
- **Raw Cell Bounding Boxes:** `raw/table_cells_raw.json`
- **Cleaned Structured JSON:** `cleaned/extracted_table.json`
- **Cleaned Tabular CSV:** `cleaned/extracted_table.csv`
