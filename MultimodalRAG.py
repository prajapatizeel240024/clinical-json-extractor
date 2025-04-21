import os
import fitz           
import base64
import json
from openai import OpenAI

# ─── Configuration ─────────────────────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")  # must be set in your environment
client  = OpenAI(api_key=api_key)

# Paths for extraction
READ_PATH        = "./data"             # input PDFs (contains attention.pdf)
PDF_FILE         = "attention.pdf"      # specific PDF file to process
EXTRACT_PATH     = "./data"             # output path
EXTRACT_FILE     = "extracted_medical.json"  # extracted JSON filename

# Paths for transformation
SCHEMA_PATH      = "./data/medical_schema.json"  # your JSON schema file
TRANSFORM_PATH   = "./data/final_medical.json"  # where transformed JSON goes

# ─── Helpers ───────────────────────────────────────────────────────────────────

def pdf_to_base64_images(pdf_path: str, dpi: int = 200) -> list[str]:
    """
    Convert each page of the PDF into a base64-encoded PNG.
    """
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
    Send one page-image to GPT‑4o, returning a JSON object:
      {
        "medical_diagnosis": [...],
        "surgical_history": [...],
        "allergies": {
           "has_allergies": true|false,
           "allergy_list": [...]
        },
        "physical_examination": {
           "height": "...", "weight": "...", "blood_pressure": "...",
           "pulse": "...", "respiratory_rate": "...", "temperature": "...",
           "overall_health": "good|fair|poor"
        }
      }
    """
    system_prompt = """
You are an OCR-like data extraction tool for clinical notes.
Given the image of one page of a medical record, extract exactly:

1. medical_diagnosis: list of primary diagnoses.
2. surgical_history: list of past surgeries.
3. allergies:
   • has_allergies: true/false
   • allergy_list: list each allergy if true; otherwise empty.
4. physical_examination:
   • height: feet/inches (e.g. "5'7\"")
   • weight: lbs (e.g. "150 lbs")
   • blood_pressure: mmHg (e.g. "120/80")
   • pulse: bpm (e.g. "72")
   • respiratory_rate: breaths/min (e.g. "16")
   • temperature: °F (e.g. "98.6")
   • overall_health: one of "good", "fair", or "poor"

Output ONLY a JSON object with these keys.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
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
    return response.choices[0].message.content

def extract_from_multiple_pages(base64_images, original_filename, output_directory):
    """
    For each base64_image (one page), call extract_medical_data()
    which already returns a dict, collect those dicts in a list,
    then write that list out as JSON.
    """
    entire_report = []
    for b64 in base64_images:
        page_dict = extract_medical_data(b64)   # <-- this is already a dict
        entire_report.append(page_dict)

    os.makedirs(output_directory, exist_ok=True)
    out_path = os.path.join(
        output_directory,
        original_filename.replace('.pdf', '_extracted.json')
    )
    with open(out_path, 'w', encoding='utf-8') as f:
        # directly dump the list of dicts
        json.dump(entire_report, f, ensure_ascii=False, indent=2)

    return out_path


def main_extract(read_path, write_path):
    """
    Walk a folder of PDFs, convert each to base64 PNGs,
    run extract_from_multiple_pages, and write one JSON per PDF.
    """
    for fn in os.listdir(read_path):
        if not fn.lower().endswith('.pdf'):
            continue
        pdf_file = os.path.join(read_path, fn)
        print(f"Processing {fn}…")
        pages_b64 = pdf_to_base64_images(pdf_file)
        out_json  = extract_from_multiple_pages(pages_b64, fn, write_path)
        print(f"  → Saved JSON: {out_json}")

# ─── Transformation ────────────────────────────────────────────────────────────

def transform_medical_data(json_raw, json_schema) -> dict:
    """
    Take raw JSON (list of page‐objects) and a schema,
    output JSON conformed to schema.
    """
    system_prompt = f"""
You are a data transformation tool. Given raw JSON data and a JSON schema,
output data that conforms exactly to the schema.
- Omit fields that don't match.
- Fill missing fields with null.
- Translate to English if needed.
- Format dates as YYYY-MM-DD.

Here is the schema:
{json.dumps(json_schema, indent=2)}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text":
                    f"Transform this JSON to match the schema: {json.dumps(json_raw)}"
                }
            ]}
        ]
    )
    return response.choices[0].message.content

def main_transform(extracted_json_path: str,
                   json_schema_path: str,
                   save_path: str):
    # Load schema
    with open(json_schema_path, "r", encoding="utf-8") as sf:
        schema = json.load(sf)
    os.makedirs(save_path, exist_ok=True)

    for fname in os.listdir(extracted_json_path):
        if not fname.endswith("_extracted.json"):
            continue
        full_in = os.path.join(extracted_json_path, fname)
        with open(full_in, "r", encoding="utf-8") as rf:
            raw = json.load(rf)

        print(f"🔄 Transforming ⟶ {fname}")
        transformed = transform_medical_data(raw, schema)

        out_name = f"transformed_{fname}"
        full_out = os.path.join(save_path, out_name)
        with open(full_out, "w", encoding="utf-8") as wf:
            json.dump(transformed, wf, ensure_ascii=False, indent=2)
        print(f"  ✅ Saved transformed JSON: {full_out}")

# ─── Script Entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 1) Extract fields from all PDFs
    main_extract(READ_PATH, EXTRACT_PATH)
    # 2) Transform extracted JSON into final schema
    main_transform(EXTRACT_PATH, SCHEMA_PATH, TRANSFORM_PATH)
