import json
import re
from google import genai
from pydantic import ValidationError
from schemas import Invoice

client = genai.Client()

MESSY_INVOICE = """
Hey, sending over the invoice for last month's work.
From: Bright Path Consulting
Invoice #: BP-2026-0447
We did 3 strategy sessions at $260 each, and 12 hours of
implementation support at $95/hr. Also one flat fee of $400
for the onboarding workshop.
"""

prompt = f"""Extract the invoice details from this email as JSON with
fields: vendor_name, invoice_number, total_amount, line_items.

{MESSY_INVOICE}
"""


def extract_json(raw_text: str) -> dict:
    """Strip markdown fences if present, then parse."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


MAX_RETRIES = 3

# This grows over the loop — first the original prompt, then feedback if it fails.
conversation = prompt

for attempt in range(1, MAX_RETRIES + 1):
    print(f"\n--- Attempt {attempt} ---")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=conversation
    )

    print("Raw model output:")
    print(response.text)

    try:
        data = extract_json(response.text)
        invoice = Invoice.model_validate(data)
        print("\n✅ Validated invoice:")
        print(invoice.model_dump_json(indent=2))
        break  # success — stop retrying
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"\n❌ Attempt {attempt} failed: {e}")
        if attempt == MAX_RETRIES:
            print("\n🛑 Giving up — max retries reached.")
        else:
            # Feed the bad answer AND the error back in as extra context.
            conversation = (
                f"{prompt}\n\n"
                f"Your previous answer was:\n{response.text}\n\n"
                f"That answer was invalid. Error: {e}\n\n"
                f"Return corrected JSON only — no markdown fences, no commentary."
            )