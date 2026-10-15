# Parser Benchmark Summary — Selectolax vs lxml

**Tool:** `02_selectolax_lxml`
**Source:** `live` (51274 bytes)
**Items Extracted:** `20`

---

## Benchmark Results

| Parser Engine | Selector Syntax | Time (μs) | Time (ms) | Speed Rank |
|---|---|---|---|---|
| **Selectolax (Lexbor C Engine)** | CSS Selectors | `4928.6 μs` | `4.929 ms` | 2nd |
| **lxml (libxml2 / libxslt)** | XPath Tree | `4017.8 μs` | `4.018 ms` | 1st (Fastest) |

**Performance Factor:** `lxml` was `0.82x` as fast in this benchmark.

---

## Extracted Catalog Items (Sample)

[
  {
    "title": "A Light in the ...",
    "url": "catalogue/a-light-in-the-attic_1000/index.html",
    "difficulty": "",
    "tags": [],
    "description_or_meta": "\u00a351.77"
  },
  {
    "title": "Tipping the Velvet",
    "url": "catalogue/tipping-the-velvet_999/index.html",
    "difficulty": "",
    "tags": [],
    "description_or_meta": "\u00a353.74"
  },
  {
    "title": "Soumission",
    "url": "catalogue/soumission_998/index.html",
    "difficulty": "",
    "tags": [],
    "description_or_meta": "\u00a350.10"
  }
]
