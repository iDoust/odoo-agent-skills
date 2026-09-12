#!/usr/bin/env python3
"""
Automated Post-Deployment Smoke Test for Odoo

Verifies server health, database connectivity, module installation state,
and critical services immediately following a deployment to Staging or Production.

Exit codes:
  0 = All smoke tests PASSED
  1 = Smoke test FAILED (triggers rollback or alert)
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
import xmlrpc.client
from urllib.parse import urlparse


def validate_endpoint(url: str) -> str:
    """Validate URL format."""
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError(f"Invalid URL '{url}'. Must include http:// or https://")
    return url.rstrip('/')


def run_smoke_test(
    url: str,
    db: str,
    login: str,
    password: str,
    target_modules: list[str] | None = None,
    timeout: int = 15,
) -> bool:
    """Execute automated health checks."""
    url = validate_endpoint(url)
    target_modules = target_modules or []
    all_passed = True

    print(f"\n🚀 Starting Odoo Smoke Test against: {url} (DB: {db})")
    print("=" * 65)

    # 1. Check HTTP Availability & Latency
    print("[1/5] Checking HTTP web endpoint availability...")
    login_url = f"{url}/web/login"
    start_time = time.time()
    try:
        req = urllib.request.Request(
            login_url,
            headers={'User-Agent': 'Odoo-SmokeTest/1.0'}
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency_ms = (time.time() - start_time) * 1000
            if response.status == 200:
                print(f"  ✅ HTTP 200 OK — Latency: {latency_ms:.1f}ms")
            else:
                print(f"  ❌ Unexpected HTTP status: {response.status}")
                all_passed = False
    except Exception as e:
        print(f"  ❌ HTTP connection failed: {e}")
        return False

    # 2. Check XML-RPC Authentication
    print("\n[2/5] Checking XML-RPC authentication...")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    try:
        version_info = common.version()
        server_version = version_info.get('server_version', 'Unknown')
        print(f"  ✅ Odoo Server Version: {server_version}")

        uid = common.authenticate(db, login, password, {})
        if uid:
            print(f"  ✅ Authenticated successfully as '{login}' (UID: {uid})")
        else:
            print(f"  ❌ Authentication failed for user '{login}' on database '{db}'")
            return False
    except Exception as e:
        print(f"  ❌ XML-RPC authentication call failed: {e}")
        return False

    # 3. Check Models API Endpoint
    print("\n[3/5] Checking ORM model access...")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    try:
        user_data = models.execute_kw(
            db, uid, password,
            'res.users', 'read',
            [[uid]], {'fields': ['name', 'company_id']}
        )
        if user_data:
            company_name = user_data[0]['company_id'][1] if user_data[0]['company_id'] else 'None'
            print(f"  ✅ Current user '{user_data[0]['name']}' active in company: '{company_name}'")
        else:
            print("  ❌ Failed to read current user record from ORM")
            all_passed = False
    except Exception as e:
        print(f"  ❌ ORM execution error: {e}")
        all_passed = False

    # 4. Verify Target Modules are 'installed'
    if target_modules:
        print(f"\n[4/5] Verifying installation state of target modules: {', '.join(target_modules)}...")
        try:
            modules_info = models.execute_kw(
                db, uid, password,
                'ir.module.module', 'search_read',
                [[('name', 'in', target_modules)]],
                {'fields': ['name', 'state', 'latest_version']}
            )
            found_names = {m['name']: m for m in modules_info}
            for mod_name in target_modules:
                if mod_name not in found_names:
                    print(f"  ❌ Module '{mod_name}' is NOT found in database!")
                    all_passed = False
                else:
                    m = found_names[mod_name]
                    state = m.get('state')
                    ver = m.get('latest_version') or 'N/A'
                    if state == 'installed':
                        print(f"  ✅ Module '{mod_name}' is INSTALLED (Version: {ver})")
                    else:
                        print(f"  ❌ Module '{mod_name}' state is '{state}' (Expected 'installed')!")
                        all_passed = False
        except Exception as e:
            print(f"  ❌ Module verification query failed: {e}")
            all_passed = False
    else:
        print("\n[4/5] Skipping specific module check (none specified in arguments).")

    # 5. Verify Scheduled Actions (Cron) Health
    print("\n[5/5] Checking cron jobs health...")
    try:
        active_crons_count = models.execute_kw(
            db, uid, password,
            'ir.cron', 'search_count',
            [[('active', '=', True)]]
        )
        print(f"  ✅ Found {active_crons_count} active scheduled actions.")
    except Exception as e:
        print(f"  ⚠️ Could not query ir.cron (possibly restricted permissions): {e}")

    # Summary
    print("\n" + "=" * 65)
    if all_passed:
        print("🎉 ALL SMOKE CHECKS PASSED. System is production ready!")
        print("=" * 65 + "\n")
        return True
    else:
        print("🚨 SMOKE CHECKS FAILED! Immediate attention or rollback required.")
        print("=" * 65 + "\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Automated Post-Deployment Smoke Test for Odoo")
    parser.add_argument(
        "--url",
        default=os.getenv("ODOO_URL", "http://localhost:8069"),
        help="Odoo instance base URL (default: ODOO_URL or http://localhost:8069)",
    )
    parser.add_argument(
        "--db",
        default=os.getenv("ODOO_DB", "odoo"),
        help="Target database name (default: ODOO_DB or odoo)",
    )
    parser.add_argument(
        "--login",
        default=os.getenv("ODOO_LOGIN", "admin"),
        help="Admin/operator login (default: ODOO_LOGIN or admin)",
    )
    parser.add_argument(
        "--password",
        default=os.getenv("ODOO_PASSWORD", "admin"),
        help="Admin/operator password (default: ODOO_PASSWORD or admin)",
    )
    parser.add_argument(
        "--modules",
        default="",
        help="Comma-separated list of module names to verify state='installed'",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP/RPC timeout in seconds (default: 15)",
    )

    args = parser.parse_args()
    modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    success = run_smoke_test(
        url=args.url,
        db=args.db,
        login=args.login,
        password=args.password,
        target_modules=modules,
        timeout=args.timeout,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
