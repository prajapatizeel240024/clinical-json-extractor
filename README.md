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

*Feel free to rename `extractor.py`; just update the commands below.*

---

## ⚙️ Setup

```bash
# 1) clone / copy repo
cd clinical-json-extractor

# 2) create Python ≥3.10 environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3) install dependencies
pip install -r requirements.txt

# 4) add your OpenAI key (bash)
export OPENAI_API_KEY="sk-..."   # PowerShell: setx OPENAI_API_KEY "sk-..."
```

---

## ▶️ Running

```bash
# Drop PDFs (and optionally their schemas) into ./data
python extractor.py
```

### Optional tweaks  
All constants—paths, model name, DPI—sit near the top of `extractor.py`.  
Edit them to point at different folders, files, or model versions.

---

## 🌐 Architecture overview

```mermaid
flowchart TD
  %% ── 1. Pre‑processing ─────────────────────────────────────
  subgraph "Pre‑processing"
    A[PDF] -->|PyMuPDF – rasterise @ 200 DPI| B[Base‑64 PNGs]
  end

  %% ── 2. LLM Extraction ─────────────────────────────────────
  subgraph "LLM Extraction"
    B -->|GPT‑4o Vision (prompt #1)| C[Page‑level JSON]
    C -->|append| D[Raw JSON list]
  end

  %% ── 3. LLM Transformation ─────────────────────────────────
  subgraph "LLM Transformation"
    D -->|GPT‑4o (prompt #2)| E[Schema‑compliant JSON]
  end

  %% ── 4. Persistence ───────────────────────────────────────
  subgraph Persistence
    E -->|write file| F[(data/final_*.json)]
  end

  %% annotation
  classDef faint fill=#0000,stroke-width:0,color=#999;
  class B,C,D,E faint;
```

*Only the “LLM Extraction” and “LLM Transformation” steps hit the OpenAI API.*

---

## 💰 Cost cheat‑sheet (GPT‑4o Apr 2025 pricing)

| Step            | Calls | Est. tokens / call* | Price / 1M tokens | Cost |
|-----------------|-------|---------------------|-------------------|------|
| Extraction      | 3 pages × 1 | ~450 in + 150 out | \$5 in / \$15 out | \$0.08 |
| Transformation  | 1           | ~1 000 in + 300 out | ″ | \$0.02 |
| **Total**       | —     | —                   | —                 | **≈ \$0.10** |

\*Assumes 300 × 400 px page images and compact JSON output.  
Lower DPI or shorten prompts to trim spend further.

---

## 🔧 Troubleshooting

| Symptom                                                        | Fix |
|---------------------------------------------------------------|-----|
| `fitz.fitz.FileDataError: cannot open`                        | Check that the PDF path is correct and the file isn’t encrypted |
| `openai.BadRequestError: "image too large"`                   | Reduce `dpi` in `pdf_to_base64_images` or resize the PNG before encoding |
| Empty / mis‑shaped fields in final JSON                       | Ensure `medical_schema.json` keys match the schema expected in `transform_medical_data` |

---

## 📝 requirements.txt

```text
PyMuPDF==1.24.5
openai==1.25.1
python-dotenv==1.0.1   # optional but handy
# If you want to pin transitive deps:
pillow>=10.0.0         # PyMuPDF uses Pillow internally
```

---

### How to use

1. Copy this **README.md** and the **requirements.txt** above into your repo.  
2. Ensure `extractor.py` sits next to README.md.  
3. Place PDFs and your schema JSON inside **`./data/`**.  
4. Run `python extractor.py`.  

You’ll get `extracted_*` (raw) and `transformed_*` (schema‑ready) JSON files for downstream analytics or EHR ingestion.

Happy extracting! 🚀
