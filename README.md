# Validated JSON Agent

> **The Problem:** LLMs generate text that *looks* like JSON — they don't guarantee it. In production, "usually valid JSON" isn't good enough for anything downstream that expects clean, typed data. This agent treats that failure mode as a normal case to handle: it strips markdown fences, enforces strict Pydantic schemas (including cross-field validations), feeds exact validation errors back to the model on retries, survives API flakes, and logs every failure to a permanent JSONL file.

## 🏗️ Architecture

A robust extraction pipeline that wraps the Google Gemini API, providing critical reliability features like strict schema validation, informed error-feedback retries, and permanent failure logging.

```text
       ┌───────────┐        ┌──────────────┐        ┌─────────────┐
       │           │        │              │        │             │
       │  Client   │───────▶│  Extraction  │───────▶│  Gemini API │
       │ (Request) │  Sync  │    Agent     │  API   │  (Upstream) │
       └───────────┘        └──────┬───────┘        └─────────────┘
                                   │
                    Validation     │
                     Failed?       ▼
                            ┌──────────────┐
                            │   Pydantic   │
                            │  Validation  │
                            └──────┬───────┘
                        Yes        │        No
                   ┌───────────────┘        └──────────────┐
                   ▼                                       ▼
            ┌──────────────┐                        ┌──────────────┐
            │ Feed Error   │                        │ Validated    │
            │ Back to LLM  │                        │ Invoice      │
            └──────┬───────┘                        └──────────────┘
                   │
                   ▼
            ┌──────────────┐
            │ Log to       │
            │ failures.json│
            └──────────────┘
```

---

## 🛠️ Tech Stack

- **AI SDK:** Google GenAI Python SDK (`google-genai`)
- **Data Validation:** Pydantic (`pydantic` with custom field validators)
- **Error Handling & Retry:** Python standard library (`json`, `re`, `time`, `pathlib`)
- **Logging:** JSON Lines (`jsonl`)

---

## 💡 Decisions Made & Solved Problems

- **Pydantic Over Regex:** Enforced strict typed schemas rather than fragile regex parsers to guarantee downstream compatibility.
- **Cross-Field Validation Order:** Defined `line_items` *before* `total_amount` so that cross-field business logic validation (`total_matches_line_items`) runs correctly without skipping.
- **Informed Retries vs. Blind Repeats:** Instead of retrying with the same prompt, the agent feeds the exact Pydantic `ValidationError` or `JSONDecodeError` back to the model so it can self-correct on the next attempt.
- **Separation of API Errors vs. Data Errors:** Handled network/server exceptions (`errors.ServerError`) with a short 5-second backoff and retry, keeping infrastructure issues distinct from data validation failures.
- **Permanent Observability Logs:** Logged every failed attempt with timestamp, attempt number, error details, and raw output to `failures.jsonl` so debugging data is never lost when the terminal closes.

---

## 🚀 Setup & How to Run

### Prerequisites

- Python 3.9+
- A Google Gemini API Key

### Installation

1. **Create and Activate Virtual Environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```powershell
   pip install google-genai pydantic
   ```

3. **Set API Key**
   ```powershell
   $env:GEMINI_API_KEY="your-actual-api-key-here"
   ```

4. **Run Live Extraction Agent**
   ```powershell
   python main.py
   ```

5. **Run Forced Failure Demo** (Demonstrates retry & logging loop)
   ```powershell
   python forced_failure_demo.py
   ```
