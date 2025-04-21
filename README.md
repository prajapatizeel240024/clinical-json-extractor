# 🩺 Clinical‑JSON‑Extractor

Extract **structured clinical data** from scanned (or born‑digital) PDFs.

The pipeline pairs **PyMuPDF** for page rasterisation with **two large‑language‑model steps**:

1. **Extraction (LLM ①)** – OCR‑style parsing of each page image  
2. **Transformation (LLM ②)** – reshapes the raw JSON into your target schema

You can run the exact same code against either **OpenAI GPT‑4o** *or* **Groq’s Llama 4 Scout**—just swap the API key & model ID.

> **Quick demo:** a 3‑page PDF of medical notes is converted to  
> `transformed_attention_extracted.json` in ≲ 25 s.  
> Real‑world cost varies by backend (see tables below).

---

## 📂 Folder layout

```
clinical-json-extractor/
├── README.md
├── requirements.txt
├── extractor.py          # ← main script
└── data/
    ├── attention.pdf
    ├── medical_schema.json
    ├── extracted_medical.json/   # auto‑created
    └── final_medical.json/       # auto‑created
```

---

## ⚙️ Setup

```bash
# clone / enter repo root
python -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

| Provider | Required env‑vars | Example |
|----------|------------------|---------|
| **OpenAI / GPT‑4o Vision** | `OPENAI_API_KEY` | `export OPENAI_API_KEY="sk‑..."` |
| **Groq / Llama 4 Scout**   | `GROQ_API_KEY`, `MODEL_PROVIDER=groq` | `export GROQ_API_KEY="gsk‑..."`<br>`export MODEL_PROVIDER=groq` |

*(Both providers use the same `openai`‑compatible Python SDK.)*

---

## ▶️ Running

```bash
python extractor.py        # PDFs & schema live inside ./data
```

The script will:

1. Rasterise each PDF page → Base‑64 PNG  
2. Send each PNG to LLM ① (`extract_medical_data`)  
3. Aggregate page objects → raw JSON list  
4. Pass raw list + schema to LLM ② (`transform_medical_data`)  
5. Save `extracted_*.json` (raw) and `transformed_*.json` (schema‑ready)

---

## 🌐 Architecture overview

![image](https://github.com/user-attachments/assets/4098ec00-6446-4303-b1fe-c39fedfad907)
![image](https://github.com/user-attachments/assets/1ee583ad-f0de-498c-a020-4ede6b764fd0)

```mermaid
flowchart TD
  A[PDF] -->|PyMuPDF @ 200 DPI| B[base‑64 PNGs]
  B -->|LLM ① extract| C[page JSON]
  C -->|append| D[raw JSON list]
  D -->|LLM ② transform| E[schema‑compliant JSON]
  E -->|write file| F[(data/final_*.json)]

  classDef faint fill=#0000,stroke-width:0,color:#999;
  class B,C,D,E faint;
```

## 💰 Cost cheat‑sheets (actual 11‑call run)

### OpenAI | GPT‑4o‑2024‑08‑06 (promo 50 % rate)

| Step            | Calls | Input tokens | Output tokens | Cost* |
|-----------------|------:|-------------:|--------------:|------:|
| Extraction      | 10 | ~8 500 | ~1 100 | \$ 0.0328 |
| Transformation  | 1  | ~ 865 | ~ 68   | \$ 0.0046 |
| **Total**       | **11** | **9 365** | **1 168** | **\$ 0.0374** |

\* Promo pricing: **\$ 2.50 in / \$ 12.50 out** per million tokens.

---

### Groq | meta‑llama / llama‑4‑scout‑17b‑16e‑instruct

| Step            | Calls | Input tokens | Output tokens | Cost† |
|-----------------|------:|-------------:|--------------:|------:|
| Extraction      | 10 | ~8 500 | ~1 100 | \$ 0.001372 |
| Transformation  | 1  | ~ 865 | ~ 68   | \$ 0.000237 |
| **Total**       | **11** | **9 365** | **1 168** | **\$ 0.001609** |

\† Flat blended rate ≈ **\$ 0.153** per million tokens (Apr 2025 Groq list).

> **Savings:** Groq is ~ **23 × cheaper** than GPT‑4o for the same workload.

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `fitz.fitz.FileDataError: cannot open` | Verify PDF path & encryption |
| `openai.BadRequestError: "image too large"` | Lower `dpi` or down‑scale PNG |
| Empty / malformed fields | Ensure `medical_schema.json` keys match the transform prompt |

---

## 📝 requirements.txt

```text
PyMuPDF==1.24.5
openai==1.25.1          # also talks to Groq
python-dotenv==1.0.1
pillow>=10.0.0          # PyMuPDF dependency
```

Happy extracting! 🚀
