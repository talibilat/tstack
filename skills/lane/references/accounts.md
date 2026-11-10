# Test accounts in every lane

`lane up` seeds each lane's own database with the repo's `prisma/seed-e2e.ts`. These are public fixture passwords from the uok-be repo, not secrets. Every lane has the same accounts, but each lane has its own data, so a change in lane 2 never shows up in lane 3.

| Role | Email | Password | 2FA |
|---|---|---|---|
| Super admin | e2e-admin@example.com | Test123! | TOTP, handled by `lane login` and `browser.mjs` |
| Org admin (institution super admin) | e2e-isa@example.com | Test123! | TOTP, handled the same way |
| Department admin | e2e-da@example.com | Test123! | none |
| Professor | e2e-professor@example.com | Test123! | none |
| Professor with no courses | e2e-professor-nocourses@example.com | Test123! | none |
| Teaching assistant | e2e-ta@example.com | Test123! | none |
| Staff, read-only staff | e2e-staff@example.com, e2e-staff-readonly@example.com, e2e-dept-readonly@example.com | Test123! | none |
| Researcher | e2e-researcher@example.com | Test123! | none |
| Student | test@example.com | password123 | none |

More fixtures exist: `e2e-inst-student-1..3@example.com`, `e2e-page-professor-01..12@example.com`, `e2e-page-student-NN@example.com`. The seed output is in `<lane>/logs/up.log`.

## Admin TOTP

There is no TOTP bypass in the app. The first `lane login <N> e2e-admin@example.com` enrols a generated secret through `/auth/2fa/setup/*` and stores it in `<lane>/.totp-secrets.json` (mode 600). Later logins compute the code. For a manual browser login, `lane totp <N> <email>` prints the current 6-digit code. A code works once per 30-second step, so the scripts wait for the next step when a code was just used.

## Seeded courses the professor owns

| Course | Id | Use it for |
|---|---|---|
| E2E Professor Faculty-Assigned Course | 44444444-4444-4444-8444-444444444701 | Starts with no syllabus versions and no foundation. The `foundation` flow picks the first course like this. |
| E2E Unpublished Course | 11111111-1111-4111-8111-111111111112 | One unpublished version |
| E2E Professor Course (Few Syllabus Versions) | 44444444-4444-4444-8444-444444444802 | 3 versions |
| E2E Professor Course (Many Syllabus Versions) | 44444444-4444-4444-8444-444444444801 | 21 versions, pagination |
| Intro to Computer Science | 11111111-1111-4111-8111-111111111111 | 8 course runs, one active |

## Small real PDFs for upload tests

Under `Data/` next to the repos (local only, not in git). Prefer the small handbooks: `Maths/Applied_Mathematics_Course_Handbook 1.pdf` (315 KB) and `Chemistry/Foundations_of_College_Chemistry_Course_Handbook_v2 1.pdf` (343 KB). The textbooks are 12 to 180 MB and take a long time to parse.
