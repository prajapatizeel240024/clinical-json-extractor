import os
import fitz           # pip install pymupdf
import base64
import json
from groq import Groq

# ─── Configuration ─────────────────────────────────────────────────────────────
# Make sure you’ve set: export GROQ_API_KEY="your_groq_key"
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("Please set the GROQ_API_KEY environment variable")
client = Groq(api_key=api_key)

# Paths for extraction
READ_PATH      = "./data"             # contains attention.pdf
EXTRACT_PATH   = "./data"             # will write *_extracted.json here

# Paths for transformation
SCHEMA_PATH    = "./data/medical_schema.json"
TRANSFORM_PATH = "./data/final_medical.json"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def pdf_to_base64_images(pdf_path: str, dpi: int = 200) -> list[str]:
    """Convert each page of the PDF into a base64-encoded PNG."""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72))
        png = pix.tobytes("png")
        b64 = base64.b64encode(png).decode("utf-8")
        pages.append(b64)
    return pages

def extract_medical_data(base64_image: str) -> dict:
    """
    Send one page-image to Groq (Llama-4-Maverick) and return a dict:
      {
        "medical_diagnosis": [...],
        "surgical_history": [...],
        "allergies": { "has_allergies": bool, "allergy_list": [...] },
        "physical_examination": { ... }
      }
    """
    system_prompt = """
You are an OCR-like data extraction tool for clinical notes.
Given one page-image, extract exactly:

1. medical_diagnosis: list of primary diagnoses.
2. surgical_history: list of past surgeries.
3. allergies:
   • has_allergies: true/false
   • allergy_list: list allergies if true; otherwise empty.
4. physical_examination:
   • height: e.g. "5'7\""
   • weight: e.g. "150 lbs"
   • blood_pressure: e.g. "120/80"
   • pulse: e.g. "72"
   • respiratory_rate: e.g. "16"
   • temperature: e.g. "98.6"
   • overall_health: "good"|"fair"|"poor"

Output ONLY a JSON object with these keys.
"""
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Extract the medical fields from this page:"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }}
            ]}
        ]
    )
    return resp.choices[0].message.content

def extract_from_multiple_pages(base64_images, original_filename, output_directory):
    """
    Run extract_medical_data() on each page; save the list of dicts
    to <original_filename>_extracted.json.
    """
    report = [extract_medical_data(b64) for b64 in base64_images]

    os.makedirs(output_directory, exist_ok=True)
    out_path = os.path.join(
        output_directory,
        original_filename.replace(".pdf", "_extracted.json")
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return out_path

# ─── Extraction Driver ─────────────────────────────────────────────────────────

def main_extract(read_path, write_path):
    """Walk read_path for PDFs, extract each, and save JSONs in write_path."""
    for fn in os.listdir(read_path):
        if not fn.lower().endswith(".pdf"):
            continue
        src = os.path.join(read_path, fn)
        print(f"⏳ Extracting {fn}…")
        pages_b64 = pdf_to_base64_images(src)
        saved = extract_from_multiple_pages(pages_b64, fn, write_path)
        print(f"✅ Saved: {saved}")

# ─── Transformation ────────────────────────────────────────────────────────────

def transform_medical_data(record: dict, json_schema: dict) -> dict:
    """
    Send one record and the schema to Groq, get back a schema-conformant JSON object.
    """
    system_prompt = f"""
You are a data transformation tool. Given one record and a JSON schema,
output exactly one JSON object that:
- Omits any fields not in the schema.
- Fills missing fields with null.
- Translates any non-English text into English.
- Formats dates as YYYY-MM-DD.

Here is the schema:
{json.dumps(json_schema, indent=2)}
"""
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text":
                    f"Transform this record to match the schema: {json.dumps(record)}"
                }
            ]}
        ]
    )
    return resp.choices[0].message.content

def main_transform(extracted_json_path: str,
                   json_schema_path: str,
                   save_path: str):
    """
    For each *_extracted.json in extracted_json_path:
      • Load the list of raw records
      • Transform each record individually
      • Save the list of transformed records to save_path/transformed_<fname>
    """
    with open(json_schema_path, "r", encoding="utf-8") as sf:
        schema = json.load(sf)

    os.makedirs(save_path, exist_ok=True)
    for fname in os.listdir(extracted_json_path):
        if not fname.endswith("_extracted.json"):
            continue

        full_in = os.path.join(extracted_json_path, fname)
        with open(full_in, "r", encoding="utf-8") as rf:
            raw_list = json.load(rf)

        print(f"🔄 Transforming {fname}…")
        transformed_list = []
        for idx, record in enumerate(raw_list, start=1):
            print(f"   • Record {idx}/{len(raw_list)}…", end="\r")
            transformed = transform_medical_data(record, schema)
            transformed_list.append(transformed)
        print()  # newline after progress

        out_name = f"transformed_{fname}"
        full_out = os.path.join(save_path, out_name)
        with open(full_out, "w", encoding="utf-8") as wf:
            json.dump(transformed_list, wf, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {full_out}")

# ─── Script Entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1) Extraction: PDF → raw JSON
    main_extract(READ_PATH, EXTRACT_PATH)
    # 2) Transformation: raw JSON → schema-conformant JSON
    main_transform(EXTRACT_PATH, SCHEMA_PATH, TRANSFORM_PATH)
