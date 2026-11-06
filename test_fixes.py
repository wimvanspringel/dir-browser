#!/usr/bin/env python3
"""Smoke test for directory_server.py fixes: path traversal, symlink handling,
CORS default-off, teardown cleanup, 404 JSON handler. Run from repo root:
    ./venv/bin/python test_fixes.py
"""
import importlib.util

spec = importlib.util.spec_from_file_location(
    "ds", "/home/wim/dir-browser/directory_server.py"
)
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)
ds.app.start_time = 0

c = ds.app.test_client()
failures = []


def check(name, got, expected, detail=None):
    ok = got == expected
    print(f"{'PASS' if ok else 'FAIL'} {name}: {got!r} (expected {expected!r})"
          + (f" -> {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(name)


# normal operation still works
check("normal listing", c.get("/api/directory").status_code, 200)
check("health", c.get("/api/health").status_code, 200)

# traversal blocked
r = c.get("/api/directory?path=../data-backup")
check("sibling traversal blocked", r.status_code, 403, r.get_data(as_text=True))
r = c.get("/api/directory?path=/etc")
check("absolute path blocked", r.status_code, 403)
check("image escape not 200",
      c.get("/api/image/../../../etc/passwd").status_code != 200, True)

# CORS off by default
h = c.get("/api/health")
check("CORS header absent by default",
      "Access-Control-Allow-Origin" in h.headers, False)

# JSON 404 handler intact
r = c.get("/api/nonexistent-endpoint")
check("404 handler", (r.status_code, r.get_json().get("error")), (404, "Endpoint not found"))

# request tracking cleaned up (teardown safety net)
check("no leaked request tracking", len(ds.active_requests), 0)

print()
print("RESULT:", "ALL PASS" if not failures else f"FAILED: {failures}")
raise SystemExit(0 if not failures else 1)
