# Troubleshooting lanes

Every entry here happened while building and testing this skill on 6 November 2026.

| Symptom | Cause | Fix |
|---|---|---|
| `lane up` stops with "Docker has N MiB free" | Other stacks or lanes use the memory. A lane needs about 2 GB. | `lane ls`, then `lane down` your own finished lanes or `lane sweep`. Do not stop other people's stacks without asking. |
| `lane up` waits "for the build lock" or "for N MiB free Docker memory before building" | Another lane is building, or memory is short. Builds run one at a time on purpose. | Wait. It gives up after `BUILD_WAIT_MIN` minutes. |
| The frontend shows "Something went wrong", and the frontend log has `getaddrinfo EAI_AGAIN api` | Docker's internal name lookups timed out while another lane built images with little free memory. Seen twice before the build lock existed. | Reload the page and repeat the step. If it repeats, check `lane ls` for a lane in state `building`. |
| A UI step waits forever although the job finished in the backend | The page stopped polling after one failed request. | Reload. The `foundation` flow reloads every minute while it waits for extraction. |
| `lane up` fails at "base stack has no running 'doc-parser-lb'" | The base stack is stopped. | Start the base stack (see `setup.md`), then `lane up` again. |
| The backend cannot reach the parser after the base stack was recreated | Recreated base containers lost their attachment to lane networks. | `lane repair N`. |
| Login in the browser lands back on `/login` | The saved browser session expired or belongs to another lane's database. | `browser.mjs` signs in again on its own. Delete `<lane>/.auth/` to force a fresh login. |
| The asset shows "failed (retryable)" and Full AI Gen stays disabled; the AI service logs `API key not valid` from `google.genai` | The `GOOGLE_API_KEY` in the base stack's `uok-ai/.env` is rejected by Google. Seen on 6 November 2026 in the base stack too (90 errors since 10:24), so not a lane problem. | Put a valid key in `<BASE_DIR>/uok-ai/.env`, then `lane exec N up -d --force-recreate ai-backend` and press Retry indexing on the asset. |
| The `foundation` flow stops at Validate with a `FINDING` such as "assessment weights total 118%" | Real product result: the AI extraction picks up roll-up rows and figure copies of assessments. Seen on both small handbooks. | Read the candidates (`lane exec N exec -T postgres psql ...` or the log), decide which are duplicates, then start a fresh run with `--reject '<pattern>'` and, if conflicts are open, `--resolve-conflicts '<comment>'`. Accepted items cannot be rejected afterwards, so decide before accepting. |
| A UI step waits on a button that never enables | The app needs a decision the flow does not make (individual review, approval tick-boxes, a disabled reason in the button's tooltip). | The failure line prints the page's buttons; read the disabled reason and add the decision as an option. |
| The AI service logs `Failed to resolve 'aruva-otel-gateway'` | The AI service still exports telemetry although `OTEL_ENABLED=false` is set. | Harmless noise. The base stack shows the same. |

## Timings measured on the author's Mac (18 CPUs, 16 GB Docker memory)

| Action | Time |
|---|---|
| `lane up` with base images only | about 1 minute |
| `lane up` building backend and frontend from worktrees (both builds at once, before the build lock) | 14 minutes |
| `lane rebuild N be` after a one-line backend change | under 10 minutes |
| `foundation` flow: upload and processing of a 315 KB handbook | under 10 seconds |
| `foundation` flow: candidate extraction (real AI calls) | 5 to 6 minutes (one run hung 36 minutes on a stalled Azure call and the backend marked it `stuck_run_timeout`; a retry took 5 minutes) |
| `foundation` flow: review, validate, approve and create the Smart Syllabus after decisions | under 1 minute |
| `generate` flow: asset upload and parse through the shared doc-parser (343 KB handbook) | 35 seconds |

## What a lane shares with dev

- Uploads go to the dev cloud storage bucket configured in `uok-be/.env`. File keys are unique ids, so lanes cannot overwrite each other's files.
- AI calls use the real model keys in the `.env` files. They cost money and are rate limited.
- Mail settings are the real ones. Use the seeded `@example.com` accounts only.
