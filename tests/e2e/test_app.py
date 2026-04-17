"""
End-to-end Playwright tests for Cloud Kitchen Order System.
Run with:  pytest tests/e2e/test_app.py -v --headed  (headed)
           pytest tests/e2e/test_app.py -v            (headless)
"""
import re
import time
import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:5001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(page: Page, username: str, password: str):
    page.goto(f"{BASE}/login")
    page.fill("#username", username)
    page.fill("#password", password)
    page.click("button[type=submit]")
    page.wait_for_url(re.compile(r"/(menu|staff|my-orders)"), timeout=6000)


# ---------------------------------------------------------------------------
# 1. Static / navigation
# ---------------------------------------------------------------------------

class TestNavigation:
    def test_homepage_loads(self, page: Page):
        page.goto(BASE)
        expect(page).to_have_title(re.compile("Cloud Kitchen", re.I))
        expect(page.locator("h2", has_text="Popular Dishes")).to_be_visible()

    def test_menu_page_loads(self, page: Page):
        page.goto(f"{BASE}/menu")
        expect(page).to_have_title(re.compile("Menu", re.I))
        # Category nav renders after JS loads
        page.wait_for_selector("#category-nav a", timeout=8000)
        expect(page.locator("#category-nav a").first).to_be_visible()

    def test_cart_page_loads(self, page: Page):
        page.goto(f"{BASE}/cart")
        expect(page.locator("h1", has_text="Shopping Cart")).to_be_visible()

    def test_track_page_loads(self, page: Page):
        page.goto(f"{BASE}/track")
        expect(page.locator("h1", has_text="Track")).to_be_visible()

    def test_login_page_loads(self, page: Page):
        page.goto(f"{BASE}/login")
        expect(page.locator("h2", has_text="Welcome Back")).to_be_visible()
        expect(page.locator("#username")).to_be_visible()
        expect(page.locator("#password")).to_be_visible()

    def test_register_page_loads(self, page: Page):
        page.goto(f"{BASE}/register")
        expect(page.locator("h2", has_text="Create Account")).to_be_visible()

    def test_health_endpoint(self, page: Page):
        resp = page.request.get(f"{BASE}/health")
        assert resp.ok
        body = resp.json()
        assert body["status"] == "healthy"


# ---------------------------------------------------------------------------
# 2. Security headers
# ---------------------------------------------------------------------------

class TestSecurityHeaders:
    def test_x_frame_options(self, page: Page):
        resp = page.request.get(BASE)
        assert resp.headers.get("x-frame-options") == "SAMEORIGIN"

    def test_x_content_type(self, page: Page):
        resp = page.request.get(BASE)
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_csp_header_present(self, page: Page):
        resp = page.request.get(BASE)
        assert "content-security-policy" in resp.headers

    def test_referrer_policy(self, page: Page):
        resp = page.request.get(BASE)
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


# ---------------------------------------------------------------------------
# 3. Auth — registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_missing_fields(self, page: Page):
        page.goto(f"{BASE}/register")
        page.click("button[type=submit]")
        # HTML5 required fields should prevent submission
        # Page should stay on register
        expect(page).to_have_url(re.compile("/register"))

    def test_register_short_password(self, page: Page):
        page.goto(f"{BASE}/register")
        page.fill("#customer-name", "Test User")
        page.fill("#phone", "8880001234")
        page.fill("#username", "shortpwuser")
        page.fill("#password", "abc")
        page.fill("#confirm-password", "abc")
        page.click("button[type=submit]")
        # Should stay on register — HTML5 minlength=8 blocks it
        expect(page).to_have_url(re.compile("/register"))

    def test_register_password_mismatch(self, page: Page):
        page.goto(f"{BASE}/register")
        page.fill("#customer-name", "Mismatch User")
        page.fill("#phone", "8880005678")
        page.fill("#username", "mismatchuser")
        page.fill("#address", "123 Test Street")
        page.fill("#password", "password123")
        page.fill("#confirm-password", "different123")
        page.check("#terms")
        page.click("button[type=submit]")
        # Should show error, not navigate away
        expect(page).to_have_url(re.compile("/register"))
        error_el = page.locator("#error-message")
        expect(error_el).to_be_visible()


# ---------------------------------------------------------------------------
# 4. Auth — login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_invalid_credentials(self, page: Page):
        page.goto(f"{BASE}/login")
        page.fill("#username", "nobody@nowhere.com")
        page.fill("#password", "wrongpass")
        page.click("button[type=submit]")
        error_el = page.locator("#error-message")
        expect(error_el).to_be_visible(timeout=5000)
        expect(error_el).to_contain_text("Invalid")

    def test_login_valid_username(self, page: Page):
        login(page, "playwright_test_user", "testpass99")
        # Should redirect away from login
        expect(page).not_to_have_url(re.compile("/login"))

    def test_login_with_phone(self, page: Page):
        page.goto(f"{BASE}/login")
        page.fill("#username", "9990001111")   # phone number registered above
        page.fill("#password", "testpass99")
        page.click("button[type=submit]")
        expect(page).not_to_have_url(re.compile("/login"), timeout=6000)

    def test_open_redirect_blocked(self, page: Page):
        """Redirect param pointing to external URL must not follow it."""
        page.goto(f"{BASE}/login?redirect=https://evil.example.com")
        page.fill("#username", "playwright_test_user")
        page.fill("#password", "testpass99")
        page.click("button[type=submit]")
        # Wait until redirected away from login
        page.wait_for_url(re.compile(r"/(menu|staff|my-orders)"), timeout=6000)
        # Final URL must be on localhost, not evil.example.com
        assert page.url.startswith(BASE), f"Expected redirect to stay on {BASE}, got: {page.url}"

    def test_already_logged_in_redirects(self, page: Page):
        login(page, "playwright_test_user", "testpass99")
        # Visiting login again should redirect away
        page.goto(f"{BASE}/login")
        page.wait_for_url(re.compile(r"/(menu|staff|my-orders)"), timeout=5000)
        expect(page).not_to_have_url(re.compile("/login"))


# ---------------------------------------------------------------------------
# 5. Menu
# ---------------------------------------------------------------------------

class TestMenu:
    def test_menu_items_visible(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections", timeout=8000)
        # At least one item card visible
        item_cards = page.locator("#menu-sections .bg-white")
        expect(item_cards.first).to_be_visible()

    def test_search_filters_items(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections", timeout=8000)
        page.fill("#menu-search", "Samosa")
        page.wait_for_timeout(400)
        visible = page.locator("#menu-sections h3:visible")
        count = visible.count()
        assert count >= 1
        for i in range(count):
            assert "samosa" in visible.nth(i).inner_text().lower()

    def test_search_no_results_shows_empty(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections", timeout=8000)
        page.fill("#menu-search", "xyzxyzxyz_notfound")
        page.wait_for_timeout(400)
        expect(page.locator("#empty-menu")).to_be_visible()

    def test_add_to_cart_opens_modal(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        # Click first "Add" button
        page.locator("#menu-sections button", has_text="Add").first.click()
        expect(page.locator("#cart-modal")).to_be_visible(timeout=3000)

    def test_modal_close(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        page.locator("#menu-sections button", has_text="Add").first.click()
        expect(page.locator("#cart-modal")).to_be_visible(timeout=3000)
        page.locator("#cart-modal button", has_text="Cancel").click()
        page.wait_for_timeout(300)
        modal_classes = page.locator("#cart-modal").get_attribute("class")
        assert "hidden" in modal_classes, f"Expected modal to have 'hidden' class, got: {modal_classes}"

    def test_popular_dishes_render_on_homepage(self, page: Page):
        page.goto(BASE)
        page.wait_for_selector("#popular-items .bg-white", timeout=8000)
        cards = page.locator("#popular-items .bg-white")
        assert cards.count() >= 1
        # Cards should not contain raw HTML (XSS check)
        first_name = cards.first.locator("h3").inner_text()
        assert "<" not in first_name


# ---------------------------------------------------------------------------
# 6. Cart
# ---------------------------------------------------------------------------

class TestCart:
    def _add_item_to_cart(self, page: Page):
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        page.locator("#menu-sections button", has_text="Add").first.click()
        expect(page.locator("#cart-modal")).to_be_visible(timeout=3000)
        page.click("button:has-text('Add to Cart')")
        page.wait_for_timeout(500)

    def test_empty_cart_shows_empty_state(self, page: Page):
        page.goto(f"{BASE}/cart")
        # Clear localStorage cart
        page.evaluate("localStorage.removeItem('cart')")
        page.reload()
        expect(page.locator("#empty-cart")).to_be_visible(timeout=5000)

    def test_add_item_updates_badge(self, page: Page):
        self._add_item_to_cart(page)
        badge = page.locator("#cart-badge")
        expect(badge).to_be_visible()
        assert int(badge.inner_text()) >= 1

    def test_cart_displays_added_item(self, page: Page):
        self._add_item_to_cart(page)
        page.goto(f"{BASE}/cart")
        page.wait_for_selector("#cart-items .bg-white", timeout=5000)
        expect(page.locator("#cart-items .bg-white").first).to_be_visible()


# ---------------------------------------------------------------------------
# 7. Checkout pre-fill (logged-in user)
# ---------------------------------------------------------------------------

class TestCheckoutPrefill:
    def test_prefill_when_logged_in(self, page: Page):
        login(page, "playwright_test_user", "testpass99")
        # Add item to cart so checkout doesn't redirect away
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        page.locator("#menu-sections button", has_text="Add").first.click()
        page.wait_for_selector("#cart-modal", timeout=3000)
        page.click("button:has-text('Add to Cart')")
        page.wait_for_timeout(500)
        # Go to checkout
        page.goto(f"{BASE}/checkout")
        page.wait_for_timeout(2000)  # allow prefill API call
        name_val = page.input_value("#customer-name")
        phone_val = page.input_value("#customer-phone")
        assert name_val.strip() != "", f"Name not prefilled, got: '{name_val}'"
        assert phone_val.strip() != "", f"Phone not prefilled, got: '{phone_val}'"

    def test_logged_in_banner_visible(self, page: Page):
        login(page, "playwright_test_user", "testpass99")
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        page.locator("#menu-sections button", has_text="Add").first.click()
        page.wait_for_selector("#cart-modal", timeout=3000)
        page.click("button:has-text('Add to Cart')")
        page.wait_for_timeout(500)
        page.goto(f"{BASE}/checkout")
        page.wait_for_timeout(2000)
        expect(page.locator("#logged-in-banner")).to_be_visible()

    def test_guest_sees_login_prompt(self, page: Page):
        # Ensure not logged in
        page.goto(BASE)
        page.evaluate("localStorage.clear()")
        # Add item
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-sections button", timeout=8000)
        page.locator("#menu-sections button", has_text="Add").first.click()
        page.wait_for_selector("#cart-modal", timeout=3000)
        page.click("button:has-text('Add to Cart')")
        page.wait_for_timeout(500)
        page.goto(f"{BASE}/checkout")
        page.wait_for_timeout(1000)
        expect(page.locator("#login-prompt")).to_be_visible()


# ---------------------------------------------------------------------------
# 8. Order History (My Orders)
# ---------------------------------------------------------------------------

class TestMyOrders:
    def test_my_orders_redirects_guest(self, page: Page):
        page.evaluate("localStorage.clear()")
        page.goto(f"{BASE}/my-orders")
        page.wait_for_url(re.compile("/login"), timeout=5000)
        expect(page).to_have_url(re.compile("/login"))

    def test_my_orders_loads_when_logged_in(self, page: Page):
        login(page, "playwright_test_user", "testpass99")
        page.goto(f"{BASE}/my-orders")
        expect(page.locator("h1", has_text="My Orders")).to_be_visible()
        # Wait for loading to finish
        page.wait_for_selector("#orders-loading.hidden, #orders-empty, #orders-list .bg-white", timeout=8000)


# ---------------------------------------------------------------------------
# 9. API — rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_login_rate_limit(self, page: Page):
        """Hitting login >10 times/min should return 429."""
        import json
        responses = []
        for _ in range(12):
            resp = page.request.post(
                f"{BASE}/api/auth/login",
                data=json.dumps({"username": "ratelimit_test", "password": "wrong"}),
                headers={"Content-Type": "application/json"}
            )
            responses.append(resp.status)
        assert 429 in responses, f"Expected 429 in responses, got: {set(responses)}"


# ---------------------------------------------------------------------------
# 10. XSS protection
# ---------------------------------------------------------------------------

class TestXSSProtection:
    def test_no_alert_from_search(self, page: Page):
        """Entering script tags in search must not trigger an alert."""
        alerts_fired = []
        page.on("dialog", lambda d: alerts_fired.append(d.message) or d.dismiss())
        page.goto(f"{BASE}/menu")
        page.wait_for_selector("#menu-search", timeout=8000)
        page.fill("#menu-search", '<img src=x onerror="alert(1)">')
        page.wait_for_timeout(500)
        assert len(alerts_fired) == 0, f"XSS alert fired: {alerts_fired}"


# ---------------------------------------------------------------------------
# conftest-style fixture (inline)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_storage(page: Page):
    """Clear localStorage before each test to avoid state bleed."""
    page.goto(BASE)
    page.evaluate("localStorage.clear()")
    yield
