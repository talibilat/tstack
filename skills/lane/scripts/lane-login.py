#!/usr/bin/env python3
"""Log in to a lane's backend and print the access token. Handles mandatory admin TOTP.

Usage: lane-login.py <email> [password]     (env QA_BE=http://127.0.0.1:<api port>, TOTP_STORE=<file>)
       lane-login.py --totp <email>         print the current 6-digit code for an enrolled account
On the first login of an org-wide admin the script enrols TOTP with a generated secret and keeps it in
TOTP_STORE (mode 600, one file per lane). Later logins compute the code from it.
"""
import base64, hashlib, hmac, json, os, struct, sys, time, urllib.error, urllib.request

BASE = os.environ.get("QA_BE", "http://127.0.0.1:18080")
STORE = os.environ.get("TOTP_STORE") or sys.exit("TOTP_STORE not set")
DEFAULT_PW = {"test@example.com": "password123"}


def call(path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        method="POST" if body is not None else "GET",
        data=json.dumps(body).encode() if body is not None else None,
        headers={"content-type": "application/json", **({"authorization": "Bearer " + token} if token else {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def totp(secret, t=None):
    key = base64.b32decode(secret.upper() + "=" * (-len(secret) % 8))
    h = hmac.new(key, struct.pack(">Q", int((t or time.time()) // 30)), hashlib.sha1).digest()
    o = h[-1] & 15
    return "%06d" % ((struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 10**6)


def load():
    try:
        with open(STORE) as f:
            return json.load(f)
    except Exception:
        return {}


def save(store):
    with open(STORE, "w") as f:
        json.dump(store, f)
    os.chmod(STORE, 0o600)


def main():
    if sys.argv[1] == "--totp":
        secret = load().get(sys.argv[2]) or sys.exit(f"{sys.argv[2]} has no TOTP secret yet; run 'lane login' for it once")
        print(totp(secret))
        return
    email = sys.argv[1]
    pw = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PW.get(email, "Test123!")
    st, d = call("/auth/login", {"email": email, "password": pw})
    if st >= 400:
        sys.exit(f"login failed {st}: {d.get('message')}")
    if d.get("status") == "authenticated":
        print(d["access_token"])
        return
    tok = d.get("two_factor_token") or d.get("twoFactorToken")
    store = load()
    if d.get("status") == "two_factor_setup_required":
        _, b = call("/auth/2fa/setup/begin", {}, tok)
        secret = b["secret"]
        st, r = call("/auth/2fa/setup/confirm", {"secret": secret, "code": totp(secret)}, tok)
        if st >= 400:
            sys.exit(f"2fa setup failed {st}: {r.get('message')}")
        store[email] = secret
        save(store)
        print(r.get("access_token") or r.get("accessToken"))
        return
    secret = store.get(email) or sys.exit("2FA enrolled but the secret is not in TOTP_STORE")
    for _ in range(2):
        st, r = call("/auth/2fa/verify", {"code": totp(secret)}, tok)
        if st < 400:
            print(r.get("access_token") or r.get("accessToken"))
            return
        time.sleep(31 - time.time() % 30)  # a code works once per 30 s step; wait for the next one
    sys.exit(f"2fa verify failed {st}: {r.get('message')}")


main()
