# 🩺 Clinical‑JSON‑Extractor

Extract structured clinical data from scanned (or born‑digital) PDFs by pairing
**PyMuPDF** for rasterisation with **GPT‑4o Vision** for two LLM steps:

1. **Extraction** – page‑wise OCR + field parsing  
2. **Transformation** – conform raw output to your own JSON schema

> **Quick demo:** a 3‑page PDF containing medical notes is converted into  
> `transformed_attention_extracted.json` in ≲ 25 s and costs **≈ $0.10 USD**.

---

## 📂 Folder layout

```
clinical-json-extractor/
├── README.md
├── requirements.txt
├── extractor.py          # ← code you pasted
└── data/                 # default data bucket
    ├── attention.pdf     # sample input
    ├── medical_schema.json
    ├── extracted_medical.json/      # auto‑created
    └── final_medical.json/          # auto‑created
```

*Feel free to rename `extractor.py`; just update the README commands.*

---

## ⚙️ Setup

```bash
# 1) clone / copy repo
cd clinical-json-extractor

# 2) create Python ≥3.10 environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3) install deps
pip install -r requirements.txt

# 4) add your OpenAI key
export OPENAI_API_KEY="sk‑..."    # Windows (PowerShell): setx OPENAI_API_KEY "sk‑..."
```

---

## ▶️ Running

```bash
# Drop your PDFs (and optionally their schemas) into ./data
python extractor.py
```

### Optional arguments  
The script keeps all constants near the top; edit them to point at different
folders, filenames, or model versions.

---

## 🌐 Architecture overview

```mermaid
flowchart TD
  subgraph 1[Pre‑processing]
    A[PDF] -->|PyMuPDF<br>rasterise @ 200 DPI| B[Base‑64 PNGs]
  end
  subgraph 2[LLM Extraction]
    B -->|GPT‑4o Vision<br>(system prompt #1)| C[Page‑level JSON[]]
    C -. list append .-> D[Raw JSON list]
  end
  subgraph 3[LLM Transformation]
    D -->|GPT‑4o<br>(system prompt #2)| E[Schema‑compliant JSON]
  end
  subgraph 4[Persistence]
    E -->|write file| F[(data/final_*.json)]
  end
```

*Nodes **2** and **3** are the only parts hitting the OpenAI API.*

---

## 💰 Cost cheat‑sheet (GPT‑4o Apr 2025 pricing)

| Step | Requests | Est. tokens/request* | Price / 1M tokens | Cost |
|------|----------|----------------------|-------------------|------|
| Extraction | 3 pages × 1 call | ~450 in + 150 out | \$5 in / \$15 out | \$0.08 |
| Transformation | 1 call | ~1 000 in + 300 out | '' | \$0.02 |
| **Total** | – | – | – | **≈ \$0.10** |

\*Assumes 300×400 px page images and modest JSON output.  
Tune DPI & prompt length to control spend.

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `fitz.fitz.FileDataError: cannot open` | Ensure the PDF path is correct and not encrypted |
| `openai.BadRequestError: “detail”: “image too large”` | Lower `dpi` in `pdf_to_base64_images` or resize PNG before encoding |
| Empty fields in final JSON | Validate `medical_schema.json` keys exactly match what you expect |

---

## 📝 requirements.txt
```text
PyMuPDF==1.24.5
openai==1.25.1
python-dotenv==1.0.1   # optional but handy
# If you want to pin transitive deps:
pillow>=10.0.0         # PyMuPDF uses Pillow internally
```

Happy extracting! Feel free to raise issues or PRs for enhancements 🚀
```

---

### How to use  

1. Copy the **README.md** and **requirements.txt** blocks above into your repo.  
2. Make sure your `extractor.py` lives next to README.md.  
3. Put PDFs and your schema JSON into **`./data/`**.  
4. `python extractor.py` – done!  

You’ll end up with `extracted_*` (raw) and `transformed_*` (schema‑ready) JSON
files ready for downstream analytics or EHR ingestion.
