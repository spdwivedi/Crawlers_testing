---
source_input: fixtures/financial_table_sample.png
content_type: table_grid
confidence_score: 0.98
structured_elements_count: 60
tables_count: 1
bounding_boxes_count: 30
processed_at: '2026-10-21T13:00:16.983103+00:00'
primary_tool: 04_multimodal_auto_resolver
---

# 👁️ Multimodal Auto-Resolver Audit: Table Grid

- **Source Target:** `fixtures/financial_table_sample.png`
- **Modality:** `table_grid`
- **Confidence Score:** **98.0%**
- **Structured Elements Recognized:** `60` blocks / cells
- **Detected Tables:** `1`
- **Bounding Boxes Localized:** `30`

## 📊 Extracted Table Preview (Table 1)

|   Problem ID | Title                   | Difficulty   | Acceptance   | Time Complexity   |
|-------------:|:------------------------|:-------------|:-------------|:------------------|
|            1 | Two Sum                 | Easy         | 52.4%        | O(N)              |
|           15 | 3Sum                    | Medium       | 34.2%        | O(N^2)            |
|           42 | Trapping Rain Water     | Hard         | 62.1%        | O(N)              |
|          146 | LRU Cache               | Medium       | 43.8%        | O(1)              |
|          295 | Find Median from Stream | Hard         | 51.9%        | O(log N)          |

## 📝 Extracted Text & Layout Content

```text
Problem ID | Title | Difficulty | Acceptance | Time Complexity
1 | Two Sum | Easy | 52.4% | O(N)
15 | 3Sum | Medium | 34.2% | O(N^2)
42 | Trapping Rain Water | Hard | 62.1% | O(N)
146 | LRU Cache | Medium | 43.8% | O(1)
295 | Find Median from Stream | Hard | 51.9% | O(log N)
```

## 📦 Deliverables in `cleaned/`

- `multimodal_spec.json` — Pydantic schema validation contract
- `extracted_text.txt` — Consolidated full text dump
- `bounding_boxes.json` — Localized bounding box coordinates
- `tables/` — 1 structured matrix exports (.csv, .json)
