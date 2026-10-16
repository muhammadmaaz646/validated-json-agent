Project brief:
Validated JSON Agent
Enforces Pydantic schemas, retries on parse errors, logs every failure.
• Proves your outputs survive production.

Final project overview:
It’s a Validated JSON Extraction Agent that wraps around Google Gemini LLM calls to reliably pull structured data from messy unstructured text (like invoice emails).
Normally, when you make a simple call to an LLM asking for JSON, you don’t have any guarantee on what comes back (if you ask for JSON from the LLM, for example, there might be some text in front of it that when you pass it to your code, it gives an error.). What if the LLM returns broken JSON, skips required fields, or makes up a total amount that doesn't add up to the line items? Your downstream app crashes, or bad data enters your database.
That’s why this project adds schema validation, business logic checks, self-correcting retries, and error logging.
It uses Python, the Google GenAI SDK (gemini-2.5-flash), Pydantic for schema enforcement/validation, and Regex/JSON for cleaning LLM output.

How it works:

1. Schema & Math Validation (schemas.py): It defines Pydantic models for Invoice and LineItem. It validates not only field types and non-empty strings, but also executes custom business logic—such as recalculating the line item totals and raising a ValueError if the LLM's total_amount doesn't match the math.
2. Self-Correction Feedback Loop (main.py): When Gemini outputs a response, the app strips markdown code fences and validates it against Pydantic. If validation fails (due to invalid JSON or math mismatches), the script catches the error, wraps the bad response along with the exact validation error back into the conversation context, and asks Gemini to correct its own mistake (up to MAX_RETRIES).
3. API Resilience & Failure Logging (logging_errors.py & failures.jsonl): Beyond LLM output errors, it handles transient API server errors (errors.ServerError) with sleep backoffs. Every failed attempt, raw output, and error stack trace is logged in real-time to a failures.jsonl file for debugging and auditing.

More learnings:
What is parsing?
To parse means to break down a complex block of text, data, or code into smaller, understandable components based on a set of grammatical or structural rules.

One more thing, one time, Gemini's servers themselves were temporarily overloaded and rejected the request outright. So this should be considered in production as well. (This time, I just wrote some code to handle that error.)

Let’s start with the basic version:
Code with the issue (if you ask for JSON from the LLM, there’s some text in front of it that when you pass it to your code, it gives an error.): https://claude.ai/chat/f569b517-3d20-4707-98f1-6cd44906ed16#:~:text=main.py%20(naive,%EE%81%96
Code with the issue resolved (Using pydantic schemas and removing any characters that are not JSON):
https://claude.ai/chat/f569b517-3d20-4707-98f1-6cd44906ed16#:~:text=instead%20of%20pieced%2D%E2%80%A6-,Here%27s%20your%20full%20current%20working%20state,-%E2%80%94%20the%20%22before%22%20(naive
