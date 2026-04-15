import asyncio
import os
from abc import abstractmethod
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import Stealth
from src.adapters.base import BaseAdapter, AdapterHealthCheck
from src.core.types import RawListing, SearchFilters

_PROJECT_ROOT = Path(__file__).parent.parent.parent

_stealth = Stealth()

# Common cookie consent button selectors across EU sites
_COOKIE_SELECTORS = [
    "#didomi-notice-agree-button",              # Didomi (Subito, Leboncoin, etc.)
    "button#onetrust-accept-btn-handler",       # OneTrust
    "#gdpr-banner-accept",                      # Kleinanzeigen
    "button[id*='accept']",                     # Generic accept buttons
    "button[class*='accept']",
    "button[data-testid*='accept']",
    "button[data-testid*='cookie']",
    "[class*='cookie'] button",
    "[id*='cookie'] button",
    "[class*='consent'] button:first-child",
    "button:has-text('Accept')",
    "button:has-text('Accetta')",               # Italian
    "button:has-text('Akzeptieren')",           # German
    "button:has-text('Accepter')",              # French
    "button:has-text('Aceptar')",               # Spanish
    "button:has-text('Zaakceptuj')",            # Polish
    "button:has-text('Elfogadom')",             # Hungarian
    "button:has-text('Souhlasím')",             # Czech
    "button:has-text('Súhlasím')",              # Slovak
    "button:has-text('Prihvaćam')",             # Croatian
    "button:has-text('Sprejemam')",             # Slovenian
    "button:has-text('Приемам')",               # Bulgarian
    "button:has-text('Accept toate')",          # Romanian
]


class PlaywrightBaseAdapter(BaseAdapter):
    base_url: str
    _browser: Browser | None = None
    _persistent_context: BrowserContext | None = None
    _pw = None

    @staticmethod
    def _chrome_executable() -> str | None:
        """Return the path to an installed Chrome/Chromium binary, or None."""
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    async def _get_browser(self) -> Browser:
        if self._browser is None or not self._browser.is_connected():
            if self._pw is None:
                self._pw = await async_playwright().start()
            chrome = self._chrome_executable()
            launch_kwargs: dict = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            }
            if chrome:
                launch_kwargs["executable_path"] = chrome
            self._browser = await self._pw.chromium.launch(**launch_kwargs)
        return self._browser

    async def _new_context(self) -> BrowserContext:
        browser_data_dir = os.environ.get("BROWSER_DATA_DIR")
        if browser_data_dir:
            # Resolve relative paths against project root
            data_path = Path(browser_data_dir)
            if not data_path.is_absolute():
                data_path = _PROJECT_ROOT / data_path
            data_path.mkdir(parents=True, exist_ok=True)
            browser_data_dir = str(data_path)
            # Reuse persistent context with real Chrome cookies to bypass WAF
            if self._persistent_context is None:
                if self._pw is None:
                    self._pw = await async_playwright().start()
                chrome = self._chrome_executable()
                launch_kwargs: dict = {
                    "headless": True,
                    "user_agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "locale": self.language,
                    "viewport": {"width": 1280, "height": 800},
                    "java_script_enabled": True,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                }
                if chrome:
                    launch_kwargs["executable_path"] = chrome
                self._persistent_context = await self._pw.chromium.launch_persistent_context(
                    browser_data_dir,
                    **launch_kwargs,
                )
            return self._persistent_context

        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale=self.language,
            viewport={"width": 1280, "height": 800},
            java_script_enabled=True,
        )
        return context

    async def _dismiss_cookies(self, page: Page) -> None:
        """Try to dismiss cookie consent banners."""
        for selector in _COOKIE_SELECTORS:
            try:
                await page.click(selector, timeout=1000)
                await asyncio.sleep(0.5)
                return
            except Exception:
                continue

    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        context = await self._new_context()
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        try:
            url = self._build_search_url(query)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            await self._dismiss_cookies(page)
            await asyncio.sleep(2)
            results = await self._extract_listings(page, query)
            return results
        finally:
            await page.close()
            if context is not self._persistent_context:
                await context.close()

    async def search_with_diagnostics(
        self, query: str, filters: SearchFilters, capture_dir: Path,
    ) -> tuple[list[RawListing], Path | None, Path | None]:
        """Run search and capture screenshot + DOM snapshot before closing the page."""
        context = await self._new_context()
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        screenshot_path: Path | None = None
        dom_path: Path | None = None
        try:
            url = self._build_search_url(query)
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            await self._dismiss_cookies(page)
            await asyncio.sleep(2)
            results = await self._extract_listings(page, query)

            # Capture diagnostics before closing
            capture_dir.mkdir(parents=True, exist_ok=True)
            screenshots_dir = capture_dir / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            dom_dir = capture_dir / "dom"
            dom_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = screenshots_dir / f"{self.source_name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            dom_path = dom_dir / f"{self.source_name}.html"
            content = await page.content()
            dom_path.write_text(content, encoding="utf-8")

            return results, screenshot_path, dom_path
        except Exception:
            # Still try to capture what we can on error
            try:
                capture_dir.mkdir(parents=True, exist_ok=True)
                screenshots_dir = capture_dir / "screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshots_dir / f"{self.source_name}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
            except Exception:
                pass
            try:
                dom_dir = capture_dir / "dom"
                dom_dir.mkdir(parents=True, exist_ok=True)
                dom_path = dom_dir / f"{self.source_name}.html"
                content = await page.content()
                dom_path.write_text(content, encoding="utf-8")
            except Exception:
                pass
            raise
        finally:
            await page.close()
            if context is not self._persistent_context:
                await context.close()

    def _get_selectors(self) -> dict[str, list[str]]:
        """Return CSS selectors used by this adapter, keyed by purpose.

        Override in subclasses to enable per-selector diagnostic reporting.
        """
        return {}

    async def health_check(self) -> AdapterHealthCheck:
        try:
            context = await self._new_context()
            page = await context.new_page()
            await _stealth.apply_stealth_async(page)
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=15000)
            title = await page.title()
            await page.close()
            if context is not self._persistent_context:
                await context.close()
            if "denied" in title.lower() or "blocked" in title.lower():
                return AdapterHealthCheck(
                    healthy=False,
                    message=(
                        f"{self.source_name} blocked by WAF. "
                        "Set BROWSER_DATA_DIR to a Chrome profile path with valid cookies."
                    ),
                )
            return AdapterHealthCheck(healthy=True, message=f"{self.source_name} reachable")
        except Exception as e:
            return AdapterHealthCheck(healthy=False, message=str(e))

    @abstractmethod
    async def _extract_listings(self, page: Page, query: str) -> list[RawListing]: ...

    @abstractmethod
    def _build_search_url(self, query: str) -> str: ...

    async def close(self) -> None:
        if self._persistent_context:
            await self._persistent_context.close()
            self._persistent_context = None
        if self._browser and self._browser.is_connected():
            await self._browser.close()
