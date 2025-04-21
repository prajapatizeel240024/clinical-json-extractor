# 🩺 Clinical‑JSON‑Extractor

Extract structured clinical data from scanned (or born‑digital) PDFs by pairing  
**PyMuPDF** for rasterisation with **GPT‑4o Vision** for two LLM steps:

1. **Extraction** – page‑wise OCR + field parsing  
2. **Transformation** – conform raw output to your JSON schema

> **Quick demo:** a 3‑page PDF of medical notes is converted to  
> `transformed_attention_extracted.json` in ≲ 25 s and costs **≈ $0.10 USD**.

---

## 📂 Folder layout

```
clinical-json-extractor/
├── README.md
├── requirements.txt
├── extractor.py          # ← main script
└── data/
    ├── attention.pdf     # sample input
    ├── medical_schema.json
    ├── extracted_medical.json/      # auto‑created
    └── final_medical.json/          # auto‑created
```

---

## ⚙️ Setup

```bash
cd clinical-json-extractor
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."   # PowerShell: setx OPENAI_API_KEY "sk-..."
```

---

## ▶️ Running

```bash
python extractor.py            # PDFs & schema go in ./data
```

---

## 🌐 Architecture overview

```mermaid
flowchart TD
  A[PDF] -->|rasterise 200dpi| B[base‑64 PNGs]
  B -->|extract gpt‑4o| C[page‑level JSON]
  C -->|append| D[raw JSON list]
  D -->|transform gpt‑4o| E[schema‑compliant JSON]
  E -->|write file| F[(data/final_*.json)]

  classDef faint fill=#0000,stroke-width:0,color:#999;
  class B,C,D,E faint;
```

---

## 💰 Cost cheat‑sheet (GPT‑4o Apr 2025)

| Step            | Calls | Est. tokens / call* | Price / 1M tokens | Cost |
|-----------------|-------|---------------------|-------------------|------|
| Extraction      | 3 pages × 1 | ~450 in + 150 out | \$5 in / \$15 out | \$0.08 |
| Transformation  | 1           | ~1 000 in + 300 out | ″ | \$0.02 |
| **Total**       | —           | —                 | — | **≈ \$0.10** |

*Assumes 300 × 400 px page images and compact JSON. Tune DPI/prompt to adjust.*

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `fitz.fitz.FileDataError: cannot open` | Check that the PDF path is correct and not encrypted |
| `openai.BadRequestError: "image too large"` | Lower `dpi` or resize PNG before encoding |
| Empty / mis‑shaped fields | Ensure `medical_schema.json` matches the keys expected in the transform step |

---

## 📝 requirements.txt

```text
PyMuPDF==1.24.5
openai==1.25.1
python-dotenv==1.0.1
pillow>=10.0.0
```

Happy extracting! 🚀
