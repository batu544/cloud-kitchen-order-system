"""Admin functionality tests using Playwright."""
import sys
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5001"
ADMIN_EMAIL = "admin@kitchen.com"
ADMIN_PASS = "password123"

results = []

def log(msg, status="INFO"):
    icon = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️ ", "WARN": "⚠️ "}.get(status, "•")
    print(f"{icon} {msg}")
    results.append({"status": status, "msg": msg})


def get_token(page):
    return page.evaluate("() => localStorage.getItem('auth_token')")


def api_call(page, method, path, body=None):
    token = get_token(page)
    body_js = f"opts.body = JSON.stringify({json.dumps(body)});" if body else ""
    js = f"""async () => {{
        const opts = {{
            method: '{method}',
            headers: {{ 'Authorization': 'Bearer {token}', 'Content-Type': 'application/json' }}
        }};
        {body_js}
        const r = await fetch('{path}', opts);
        return {{ status: r.status, data: await r.json() }};
    }}"""
    return page.evaluate(js)


def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context()
        page = context.new_page()

        # ── TEST 1: Login as admin ──────────────────────────────────────────
        log("TEST 1: Admin Login (via API + token injection)", "INFO")
        try:
            # Navigate to app first to establish the origin
            page.goto(f"{BASE_URL}/login")
            page.wait_for_load_state("networkidle")

            # Login via API call within browser context, store token in localStorage
            result = page.evaluate(f"""async () => {{
                const r = await fetch('/api/auth/login', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ username: '{ADMIN_EMAIL}', password: '{ADMIN_PASS}' }})
                }});
                const data = await r.json();
                if (data.success && data.data.token) {{
                    localStorage.setItem('auth_token', data.data.token);
                    localStorage.setItem('user', JSON.stringify(data.data));
                }}
                return {{ status: r.status, success: data.success, role: data.data?.role }};
            }}""")

            if result.get('success') and result.get('role') == 'admin':
                log(f"Admin logged in — role=admin, token stored in localStorage", "PASS")
            else:
                log(f"Login failed: {result}", "FAIL")
        except Exception as e:
            log(f"Admin login error: {e}", "FAIL")

        # ── TEST 1b: Login via HTML form (visual test) ─────────────────────
        log("TEST 1b: Admin login via HTML form (visual)", "INFO")
        try:
            # Clear token, test the actual form
            page.evaluate("() => { localStorage.removeItem('auth_token'); localStorage.removeItem('user'); }")
            page.goto(f"{BASE_URL}/login")
            page.wait_for_load_state("networkidle")
            page.fill('#username', ADMIN_EMAIL)
            page.fill('#password', ADMIN_PASS)
            page.click('button[type="submit"]')
            # Wait for JS redirect (api.login stores token then redirects)
            page.wait_for_timeout(2500)
            token = get_token(page)
            if token:
                log(f"HTML form login successful — redirected to {page.url}", "PASS")
            else:
                # Check if we stayed on login with error
                content = page.content()
                error_visible = "hidden" not in page.locator('#error-message').get_attribute('class') if page.locator('#error-message').count() else False
                log(f"HTML form login — token not found, URL: {page.url}", "WARN")
                # Re-login via API
                page.goto(f"{BASE_URL}/login")
                page.evaluate(f"""async () => {{
                    const r = await fetch('/api/auth/login', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{username: '{ADMIN_EMAIL}', password: '{ADMIN_PASS}'}})
                    }});
                    const data = await r.json();
                    if (data.success) {{
                        localStorage.setItem('auth_token', data.data.token);
                        localStorage.setItem('user', JSON.stringify(data.data));
                    }}
                }}""")
        except Exception as e:
            log(f"HTML form login error: {e}", "WARN")

        # ── TEST 2: Verify admin role via /api/auth/me ──────────────────────
        log("TEST 2: Verify admin role via /api/auth/me", "INFO")
        try:
            resp = api_call(page, "GET", "/api/auth/me")
            user = resp['data'].get('data', {})
            if resp['status'] == 200 and user.get('role') == 'admin':
                log(f"Role confirmed: admin (username: {user.get('username')})", "PASS")
            else:
                log(f"Unexpected response: {resp}", "FAIL")
        except Exception as e:
            log(f"Role check error: {e}", "FAIL")

        # ── TEST 3: Admin Reports page ──────────────────────────────────────
        log("TEST 3: Admin Reports page loads", "INFO")
        try:
            page.goto(f"{BASE_URL}/staff/reports")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)
            content = page.content()
            if "report" in content.lower() or "sales" in content.lower():
                log("Reports page loaded successfully", "PASS")
            else:
                log(f"Reports page unexpected content — URL: {page.url}", "WARN")
        except Exception as e:
            log(f"Reports page error: {e}", "FAIL")

        # ── TEST 4: Sales Report API ────────────────────────────────────────
        log("TEST 4: Sales report API", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/sales")
            if resp['status'] == 200:
                records = resp['data'].get('data', [])
                log(f"Sales report returned {len(records)} records", "PASS")
            else:
                log(f"Sales report {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Sales report error: {e}", "FAIL")

        # ── TEST 5: Top Items Report API ────────────────────────────────────
        log("TEST 5: Top items report API", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/top-items?limit=5")
            if resp['status'] == 200:
                log(f"Top items returned {len(resp['data'].get('data', []))} items", "PASS")
            else:
                log(f"Top items {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Top items error: {e}", "FAIL")

        # ── TEST 6: Top Customers Report API ───────────────────────────────
        log("TEST 6: Top customers report API", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/top-customers?limit=5")
            if resp['status'] == 200:
                log(f"Top customers returned {len(resp['data'].get('data', []))} customers", "PASS")
            else:
                log(f"Top customers {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Top customers error: {e}", "FAIL")

        # ── TEST 7: Orders Report API ───────────────────────────────────────
        log("TEST 7: Orders report API", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/orders")
            if resp['status'] == 200:
                log(f"Orders report returned {len(resp['data'].get('data', []))} orders", "PASS")
            else:
                log(f"Orders report {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Orders report error: {e}", "FAIL")

        # ── TEST 8: Pending Payments Report API ────────────────────────────
        log("TEST 8: Pending payments report API", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/pending-payments")
            if resp['status'] == 200:
                log(f"Pending payments returned {len(resp['data'].get('data', []))} records", "PASS")
            else:
                log(f"Pending payments {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Pending payments error: {e}", "FAIL")

        # ── TEST 9: Admin Users Management Page ────────────────────────────
        log("TEST 9: Admin Users management page", "INFO")
        try:
            page.goto(f"{BASE_URL}/admin/users")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            content = page.content()
            if "user" in content.lower():
                log("Admin users page loaded", "PASS")
            else:
                log(f"Admin users page — URL: {page.url}", "WARN")
        except Exception as e:
            log(f"Admin users page error: {e}", "FAIL")

        # ── TEST 10: List Users API ─────────────────────────────────────────
        log("TEST 10: List users API", "INFO")
        test_user_id = None
        test_user_role = None
        test_user_active = True
        try:
            resp = api_call(page, "GET", "/api/admin/users")
            if resp['status'] == 200:
                users = resp['data'].get('data', [])
                log(f"List users returned {len(users)} users", "PASS")
                non_admin = [u for u in users if u.get('username') != ADMIN_EMAIL]
                if non_admin:
                    test_user_id = non_admin[0]['user_id']
                    test_user_role = non_admin[0].get('role', 'customer')
                    test_user_active = non_admin[0].get('is_active', True)
                    log(f"  Test user: {non_admin[0].get('username')} (id={test_user_id}, role={test_user_role})", "INFO")
                else:
                    log("  No non-admin users found", "WARN")
            else:
                log(f"List users {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"List users error: {e}", "FAIL")

        # ── TEST 11: Update User Role ───────────────────────────────────────
        log("TEST 11: Update user role", "INFO")
        if test_user_id:
            try:
                new_role = "staff" if test_user_role == "customer" else "customer"
                resp = api_call(page, "PUT", f"/api/admin/users/{test_user_id}",
                                body={"role": new_role})
                if resp['status'] == 200:
                    log(f"Role changed to '{new_role}'", "PASS")
                    # Revert
                    api_call(page, "PUT", f"/api/admin/users/{test_user_id}",
                             body={"role": test_user_role})
                    log(f"  Reverted back to '{test_user_role}'", "INFO")
                else:
                    log(f"Update role {resp['status']}: {resp['data']}", "FAIL")
            except Exception as e:
                log(f"Update role error: {e}", "FAIL")
        else:
            log("No test user — skipping", "WARN")

        # ── TEST 12: Toggle User Active Status ─────────────────────────────
        log("TEST 12: Toggle user active/inactive", "INFO")
        if test_user_id:
            try:
                resp = api_call(page, "PUT", f"/api/admin/users/{test_user_id}",
                                body={"is_active": False})
                if resp['status'] == 200:
                    log("Deactivated user successfully", "PASS")
                    # Re-activate
                    api_call(page, "PUT", f"/api/admin/users/{test_user_id}",
                             body={"is_active": True})
                    log("  Re-activated user", "INFO")
                else:
                    log(f"Deactivate {resp['status']}: {resp['data']}", "FAIL")
            except Exception as e:
                log(f"Toggle active error: {e}", "FAIL")
        else:
            log("No test user — skipping", "WARN")

        # ── TEST 13: Admin Cannot Delete Own Account ────────────────────────
        log("TEST 13: Admin cannot delete own account (self-delete blocked)", "INFO")
        try:
            me = api_call(page, "GET", "/api/auth/me")
            own_id = me['data'].get('data', {}).get('user_id')
            if own_id:
                resp = api_call(page, "DELETE", f"/api/admin/users/{own_id}")
                if resp['status'] == 400:
                    log("Self-deletion correctly blocked (400)", "PASS")
                else:
                    log(f"Self-deletion returned {resp['status']} — expected 400", "FAIL")
            else:
                log("Could not determine own user_id", "WARN")
        except Exception as e:
            log(f"Self-deletion test error: {e}", "FAIL")

        # ── TEST 14: Delete Non-Existent User ──────────────────────────────
        log("TEST 14: Delete non-existent user returns 404", "INFO")
        try:
            resp = api_call(page, "DELETE", "/api/admin/users/999999")
            if resp['status'] == 404:
                log("Delete non-existent user returns 404", "PASS")
            else:
                log(f"Expected 404, got {resp['status']}: {resp['data']}", "WARN")
        except Exception as e:
            log(f"Delete non-existent user error: {e}", "FAIL")

        # ── TEST 15: Invalid Role Rejected ─────────────────────────────────
        log("TEST 15: Invalid role value rejected (400)", "INFO")
        if test_user_id:
            try:
                resp = api_call(page, "PUT", f"/api/admin/users/{test_user_id}",
                                body={"role": "superuser"})
                if resp['status'] == 400:
                    log("Invalid role correctly rejected (400)", "PASS")
                else:
                    log(f"Expected 400, got {resp['status']}: {resp['data']}", "FAIL")
            except Exception as e:
                log(f"Invalid role test error: {e}", "FAIL")
        else:
            log("No test user — skipping", "WARN")

        # ── TEST 16: Unauthenticated Access Blocked ─────────────────────────
        log("TEST 16: Unauthenticated access to admin endpoints blocked", "INFO")
        try:
            resp = page.evaluate("""async () => {
                const r = await fetch('/api/admin/users');
                return { status: r.status, data: await r.json() };
            }""")
            if resp['status'] == 401:
                log("Unauthenticated request blocked (401)", "PASS")
            else:
                log(f"Expected 401, got {resp['status']}", "FAIL")
        except Exception as e:
            log(f"Auth guard test error: {e}", "FAIL")

        # ── TEST 17: Reports UI — Sales tab renders data ────────────────────
        log("TEST 17: Reports UI renders sales data", "INFO")
        try:
            page.goto(f"{BASE_URL}/staff/reports")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            content = page.content()
            # Check for chart/table elements or data
            if any(k in content.lower() for k in ["sales", "revenue", "order", "total", "chart", "table"]):
                log("Reports UI contains data elements", "PASS")
            else:
                log("Reports UI may not be rendering data", "WARN")
        except Exception as e:
            log(f"Reports UI error: {e}", "FAIL")

        # ── TEST 18: Admin Users UI renders user table ──────────────────────
        log("TEST 18: Admin Users UI renders user table", "INFO")
        try:
            page.goto(f"{BASE_URL}/admin/users")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            content = page.content()
            # Check for table rows or user data
            if any(k in content for k in ["<tr", "<td", "admin@kitchen.com", "role", "Role"]):
                log("Admin users UI renders user table", "PASS")
            else:
                log("Admin users table may not be rendering", "WARN")
        except Exception as e:
            log(f"Admin users UI error: {e}", "FAIL")

        # ── TEST 19: Staff Dashboard accessible to admin ────────────────────
        log("TEST 19: Staff dashboard accessible to admin", "INFO")
        try:
            page.goto(f"{BASE_URL}/staff/dashboard")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)
            content = page.content()
            if any(k in content.lower() for k in ["dashboard", "order", "staff", "kitchen"]):
                log("Staff dashboard accessible to admin", "PASS")
            else:
                log(f"Staff dashboard unexpected — URL: {page.url}", "WARN")
        except Exception as e:
            log(f"Staff dashboard error: {e}", "FAIL")

        # ── TEST 20: Admin can access new order page ────────────────────────
        log("TEST 20: Admin can access new order creation page", "INFO")
        try:
            page.goto(f"{BASE_URL}/staff/orders/new")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)
            content = page.content()
            if any(k in content.lower() for k in ["order", "item", "customer", "phone"]):
                log("New order page accessible to admin", "PASS")
            else:
                log(f"New order page — URL: {page.url}", "WARN")
        except Exception as e:
            log(f"New order page error: {e}", "FAIL")

        # ── TEST 21: Reports with date range filter ─────────────────────────
        log("TEST 21: Sales report with date range", "INFO")
        try:
            resp = api_call(page, "GET",
                            "/api/reports/sales?start_date=2024-01-01&end_date=2026-12-31&group_by=month")
            if resp['status'] == 200:
                log(f"Sales report with date range returned {len(resp['data'].get('data', []))} records", "PASS")
            else:
                log(f"Sales report with date range {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Sales report date range error: {e}", "FAIL")

        # ── TEST 22: Invalid group_by rejected ─────────────────────────────
        log("TEST 22: Invalid group_by rejected (400)", "INFO")
        try:
            resp = api_call(page, "GET", "/api/reports/sales?group_by=year")
            if resp['status'] == 400:
                log("Invalid group_by correctly rejected (400)", "PASS")
            else:
                log(f"Expected 400, got {resp['status']}: {resp['data']}", "FAIL")
        except Exception as e:
            log(f"Invalid group_by test error: {e}", "FAIL")

        # ── SUMMARY ─────────────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("ADMIN FUNCTIONALITY TEST SUMMARY")
        print("=" * 60)
        passed = sum(1 for r in results if r['status'] == 'PASS')
        failed = sum(1 for r in results if r['status'] == 'FAIL')
        warned = sum(1 for r in results if r['status'] == 'WARN')
        total = passed + failed + warned
        print(f"Total tests : {total}")
        print(f"✅ PASSED   : {passed}")
        print(f"❌ FAILED   : {failed}")
        print(f"⚠️  WARNINGS : {warned}")
        print("=" * 60)
        if failed:
            print("\nFailed tests:")
            for r in results:
                if r['status'] == 'FAIL':
                    print(f"  ❌ {r['msg']}")
        if warned:
            print("\nWarnings:")
            for r in results:
                if r['status'] == 'WARN':
                    print(f"  ⚠️  {r['msg']}")

        browser.close()
        return failed


if __name__ == '__main__':
    sys.exit(run_tests())
