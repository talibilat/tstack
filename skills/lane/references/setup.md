# lane setup

One-time setup per machine. `lane doctor` checks every item below.

## 1. Tools

Docker Desktop with Compose v2.20 or newer (the `include` key with `env_file`), `jq`, `python3`, `node` 18 or newer, and Google Chrome. Then install the browser driver into the skill's own folder, outside every repo:

```
npm --prefix ~/.agents/skills/lane/scripts install
```

That installs `playwright-core` only. It drives the Chrome you already have, so no browser download.

## 2. The base stack

Lanes borrow stateless services from one always-on stack, built from `origin/dev`. On the author's machine it is the compose project `qa-dev` in `ARUVA/qa-stack` (its README explains how it was built). Any base works if it has:

- a running compose project with the services `doc-parser-lb`, `content-extractor-lb`, `presidio-analyzer`, `presidio-anonymizer` and `presidio-image-redactor`;
- a folder with dev checkouts `uok-be`, `uok-ai`, `uok-fe`, each with a working `.env` (lanes read these `.env` files and never copy them into worktrees). `uok-be/.env` must hold the same `DOC_PARSER_INTERNAL_TOKEN` and `CONTENT_EXTRACTOR_INTERNAL_TOKEN` the base's parser and extractor use;
- built images for the backend, AI service and frontend, used by any lane that does not build that repo.

`lane up` attaches those five shared services to the Docker network `aruva-lanes-shared` with the aliases `shared-<service>`. This adds a network to running containers without restarting them. If the base stack is recreated, the next `lane up` attaches them again.

## 3. Config

Create `~/.config/ttl/aruva.env` (or point `TTL_CONFIG` at another file). It is machine-specific and never committed:

```
LANES_HOME=/path/to/ARUVA/lanes          # lane folders, logs and proofs
BASE_PROJECT=qa-dev                       # compose project of the base stack
BASE_DIR=/path/to/ARUVA/qa-stack          # holds uok-be, uok-ai, uok-fe checkouts with .env
BE_BASE_IMAGE=qa-dev-uok-be:local
AI_BASE_IMAGE=qa-dev-ai-backend:latest
FE_BASE_IMAGE=qa-dev-frontend:latest
PORT_BASE=20000                           # lane N uses PORT_BASE + N*100 + offset
MAX_LANES=6
MIN_FREE_MIB=1800                         # lane up refuses below this much free Docker memory
STALE_HOURS=6                             # lane sweep removes lanes idle longer than this
```

## 4. Install the skill

The skill lives in the skills repo and is linked into each agent's folder:

```
ln -s <skills repo>/skills/lane ~/.agents/skills/lane
ln -s ~/.agents/skills/lane ~/.claude/skills/lane
ln -s ~/.agents/skills/lane ~/.codex/skills/lane
ln -s ~/.agents/skills/lane ~/.cursor/skills/lane
```

## Ports and memory

Lane N uses these host ports, all bound to 127.0.0.1:

| Service | Port | Lane 1 |
|---|---|---|
| Frontend | base + 0 | 20100 |
| AI service | base + 10 | 20110 |
| Postgres | base + 32 | 20132 |
| Qdrant HTTP, gRPC | base + 33, + 34 | 20133, 20134 |
| Neo4j HTTP | base + 74 | 20174 |
| Backend API | base + 80 | 20180 |
| Neo4j bolt | base + 87 | 20187 |

where base is `PORT_BASE + N*100`.

A lane uses about 2 GB of Docker memory (backend in single-process mode about 350 MB, AI service 500 to 800 MB, Neo4j 600 MB, the rest small). The number of lanes you can run at once is roughly (Docker memory minus everything else running) divided by 2 GB. Raising Docker Desktop's memory limit raises it; that needs a Docker restart, which stops every running stack, so plan it.
