import json
import re
import time
from pathlib import Path
from google import genai
from google.genai import errors
from pydantic import ValidationError
from schemas import Invoice

client = genai.Client()

prompt = """Extract the invoice details from this email as JSON with
fields: vendor_name, invoice_number, total_amount, line_items.

Vendor: Bright Path Consulting, Invoice BP-2026-0447.
3 strategy sessions at $260 each, 12 hours implementation at $95/hr,
1 onboarding workshop flat fee $400.
"""

LOG_PATH = Path("failures.jsonl")


def extract_json(raw_text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def log_failure(attempt: int, raw_text: str, error: Exception) -> None:
    """Append one JSON line per failed attempt — a permanent, searchable record."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "attempt": attempt,
        "error_type": type(error).__name__,
        "error": str(error),
        "raw_output": raw_text,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


# --- Fake a broken first response, no API call needed ---
FAKE_BAD_RESPONSE = """{
  "vendor_name": "Bright Path Consulting",
  "invoice_number": "BP-2026-0447",
  "total_amount": 9999,
  "line_items": [
    {"description": "strategy sessions", "quantity": 3, "unit_price": 260},
    {"description": "implementation support", "quantity": 12, "unit_price": 95},
    {"description": "onboarding workshop", "quantity": 1, "unit_price": 400}
  ]
}"""

MAX_RETRIES = 3
conversation = prompt

for attempt in range(1, MAX_RETRIES + 1):
    print(f"\n--- Attempt {attempt} ---")

    if attempt == 1:
        raw_text = FAKE_BAD_RESPONSE
        print("(using fake bad response to force a failure)")
    else:
        # --- Layer 3: survive the API itself being flaky ---
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation
            )
            raw_text = response.text
        except errors.ServerError as e:
            print(f"\n⚠️ Server error on attempt {attempt}: {e}")
            log_failure(attempt, "(no output — server error)", e)
            print("Waiting 5 seconds before retrying...")
            time.sleep(5)
            continue  # skip straight to the next attempt, don't touch `conversation`

    print("Raw output:")
    print(raw_text)

    try:
        data = extract_json(raw_text)
        invoice = Invoice.model_validate(data)
        print("\n✅ Validated invoice:")
        print(invoice.model_dump_json(indent=2))
        break
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"\n❌ Attempt {attempt} failed: {e}")
        log_failure(attempt, raw_text, e)
        if attempt == MAX_RETRIES:
            print("\n🛑 Giving up — max retries reached. See failures.jsonl for details.")
        else:
            conversation = (
                f"{prompt}\n\n"
                f"Your previous answer was:\n{raw_text}\n\n"
                f"That answer was invalid. Error: {e}\n\n"
                f"Return corrected JSON only — no markdown fences, no commentary."
            )