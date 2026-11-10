# Type-specific checklists

Identify the layers of the ticket and apply the matching list on top of the general positive, negative and edge cases.

## Front end

- UI states: loading, empty, error, success, disabled.
- Field validation: required, minimum and maximum length, special characters, XSS strings.
- Role-based visibility and access, for each user role.
- Browser console errors and failed network requests.
- Request payload and response handling match the API contract.
- Browser matrix from `setup.md` (Chrome, Firefox and Edge by default). Responsive layout where it matters.
- Back, refresh, double-click and rapid repeated actions. Session expiry in the middle of an action.

## Back end

- API contract against the API docs: schema, required fields, status codes, error format.
- Validation: missing, null, wrong type, boundary values, oversized payloads.
- Authentication and authorization (role-based access). Access to other users' or organizations' data.
- Data integrity: database state after the operation, no orphan or duplicate records.
- Idempotency, pagination, sorting, filtering.
- Backward compatibility with the existing front end and existing data.
- Concurrency and race conditions. If they cannot be tested, list them under NOT TESTED.

## AI, document processing and content extraction

- Non-determinism: run each key scenario at least 3 times and report how consistent the results are.
- Input variety: empty, very short, very long, multilingual, malformed, noisy.
- Document variety: PDF (text and scanned), DOCX, corrupted, password-protected, large, multi-page, tables and images.
- Output quality: accuracy against the expected result, hallucinations, missing or extra fields, output schema validity.
- Failure handling: timeouts, model or provider errors, fallback behavior, the error message the user sees.
- Prompt injection and unsafe content in input data.
- Latency, and token and size limits.
- Compare against a reference (expected output or a golden example). If none exists, say so and ask for one.

## Full-stack

- Verify the end-to-end chain and the contract between layers. A change in one repo can break another.
