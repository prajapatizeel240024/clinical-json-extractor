# clinical-json-extractor

```markdown
# clinical-json-extractor

A Python pipeline that converts clinical PDF reports into structured JSON using GPT‑4o.  
It performs two stages:

1. **Extraction**: OCR each PDF page → send image to GPT‑4o → extract medical fields  
2. **Transformation**: Normalize raw JSON → conform to your JSON Schema via GPT‑4o  

---

## 📁 Repository Structure

```
clinical-json-extractor/
├── clinical_extractor.py     # Main script
├── data/
│   ├── medical_reports/      # ▶️ Place your input PDFs here
│   ├── extracted_medical/    # ▶️ Raw GPT‑4o outputs (one JSON per PDF)
│   ├── transformed_medical/  # ▶️ Final schema‑conformant JSON
│   └── medical_schema.json   # ▶️ JSON Schema for transformation
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone git@github.com:<your-username>/clinical-json-extractor.git
   cd clinical-json-extractor
   ```

2. **Create & activate a virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Mac/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your OpenAI API key**  
   ```bash
   export OPENAI_API_KEY="sk-..."    # Mac/Linux
   set OPENAI_API_KEY="sk-..."       # Windows
   ```

5. **Prepare folders & schema**  
   ```bash
   mkdir -p data/medical_reports
   mkdir -p data/extracted_medical
   mkdir -p data/transformed_medical
   # Copy your PDFs into data/medical_reports/
   ```

6. **Edit the schema**  
   - Review `data/medical_schema.json` to match your desired output structure.

7. **Run the pipeline**  
   ```bash
   python clinical_extractor.py
   ```

   - **Stage 1**: Generates `*_extracted.json` in `data/extracted_medical/`  
   - **Stage 2**: Generates `transformed_*_extracted.json` in `data/transformed_medical/`

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    A[PDF Files<br/>(data/medical_reports)] --> B[pdf_to_base64_images()]
    B --> C[extract_medical_data()<br/> (calls GPT‑4o)]
    C --> D[<u>raw JSON per page</u>]
    D --> E[extract_from_multiple_pages()]
    E --> F["data/extracted_medical/<file>_extracted.json"]
    F --> G[main_transform()]
    G --> H[transform_medical_data()<br/> (calls GPT‑4o)]
    H --> I["data/transformed_medical/transformed_<file>_extracted.json"]
```

1. **pdf_to_base64_images**  
   Renders each PDF page at 200 dpi → encodes to base64 PNG.

2. **extract_medical_data**  
   Sends one page‑image to GPT‑4o with a system prompt that requests:
   - `medical_diagnosis` (array of strings)  
   - `surgical_history` (array of strings)  
   - `allergies` (object with `has_allergies` + `allergy_list`)  
   - `physical_examination` (height, weight, vitals, overall_health)

3. **extract_from_multiple_pages**  
   Loops over all base64 pages, collects GPT‑4o’s dict outputs, and writes a list of page‑objects as `*_extracted.json`.

4. **transform_medical_data**  
   Loads your JSON Schema (`medical_schema.json`) and sends the entire raw‐extracted JSON to GPT‑4o with instructions to:
   - Conform exactly to the schema  
   - Omit non‑schema fields  
   - Fill missing fields with `null`  
   - Translate and reformat as needed (e.g. dates)

5. **main_transform**  
   Applies the transformation per PDF and saves the final, schema‑compliant JSON.

---

## 📄 requirements.txt

```text
pymupdf
openai
```

---

### Questions or Issues?

Feel free to open an issue or pull request on GitHub.  
Happy extracting! 😊
