#!/usr/bin/env python3
"""Upload files to a Jira ticket as attachments.

  jira-attach.py --check              test the saved login
  jira-attach.py <KEY> <file> [...]   attach the files to the ticket

Reads JIRA_SITE, JIRA_EMAIL and JIRA_API_TOKEN from ~/.config/tstack/jira.env
(one NAME=value per line, file mode 600). The token never appears in output.
"""
import base64
import json
import mimetypes
import os
import ssl
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ENV_FILE = Path.home() / ".config" / "tstack" / "jira.env"
# Some Python installs on macOS ship without root certificates, so use the system bundle.
SYSTEM_CERTS = "/etc/ssl/cert.pem"
TLS = ssl.create_default_context(cafile=SYSTEM_CERTS if os.path.exists(SYSTEM_CERTS) else None)


def settings():
    if not ENV_FILE.exists():
        sys.exit(f"missing {ENV_FILE}. Ask the user for a Jira API token and save it there (see blueprint/references/conventions.md, Jira token).")
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            values[name.strip()] = value.strip().strip('"').strip("'")
    missing = [n for n in ("JIRA_SITE", "JIRA_EMAIL", "JIRA_API_TOKEN") if not values.get(n)]
    if missing:
        sys.exit(f"{ENV_FILE} has no value for: {', '.join(missing)}")
    return values


def call(cfg, path, data=None, headers=None):
    auth = base64.b64encode(f"{cfg['JIRA_EMAIL']}:{cfg['JIRA_API_TOKEN']}".encode()).decode()
    req = urllib.request.Request(cfg["JIRA_SITE"].rstrip("/") + path, data=data)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=60, context=TLS) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as err:
        hint = " (the token or the email is wrong)" if err.code in (401, 403) else ""
        sys.exit(f"Jira answered {err.code} for {path}{hint}")
    except urllib.error.URLError as err:
        sys.exit(f"could not reach Jira: {err.reason}")


def attach(cfg, key, file_path, name=None):
    name = name or file_path.name
    boundary = uuid.uuid4().hex
    kind = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
        f"Content-Type: {kind}\r\n\r\n"
    ).encode() + file_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    result = call(
        cfg,
        f"/rest/api/3/issue/{key}/attachments",
        data=body,
        headers={"X-Atlassian-Token": "no-check", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    return result[0]["filename"]


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    cfg = settings()
    if args[0] == "--check":
        me = call(cfg, "/rest/api/3/myself")
        print(f"login works for {me.get('displayName', 'this account')}")
        return
    if len(args) < 2:
        sys.exit("give a ticket key and at least one file")
    key, files = args[0], [Path(a) for a in args[1:]]
    absent = [str(f) for f in files if not f.is_file()]
    if absent:
        sys.exit(f"not a file: {', '.join(absent)}")
    for f in files:
        print(f"attached {attach(cfg, key, f)} to {key}")


if __name__ == "__main__":
    main()
