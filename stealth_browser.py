import asyncio
import os
from typing import Optional, Dict, Any

from playwright.async_api import async_playwright, Page, BrowserContext
from loguru import logger
import yaml

from utils.fingerprint import generate_browser_fingerprint

class StealthBrowser:
    """A wrapper for Playwright to provide stealthy browser automation with proxy and fingerprinting."""

    def __init__(self, proxy: Optional[str] = None) -> None:
        """Initializes the StealthBrowser.

        Args:
            proxy: The proxy URL to use for the browser context (e.g., "http://user:pass@ip:port").
        """
        self.proxy = proxy
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.config = self._load_config()
        logger.info(f"StealthBrowser initialized with proxy: {self.proxy if self.proxy else 'None'}")

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from config.yaml."""
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    async def launch(self) -> Page:
        """Launches a new browser instance with stealth options and returns a new page.

        Returns:
            A Playwright Page object.
        """
        if self.browser and self.context and self.page:
            logger.warning("Browser already launched. Returning existing page.")
            return self.page

        p = await async_playwright().start()
        browser_config = self.config["PLAYWRIGHT"]
        fingerprint = generate_browser_fingerprint()

        launch_options = {
            "headless": browser_config["HEADLESS"],
            "slow_mo": browser_config["SLOW_MO"],
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                f"--user-agent={fingerprint['user_agent']}"
            ]
        }

        context_options = {
            "viewport": fingerprint["screen"],
            "locale": fingerprint["accept_language"].split(',')[0],
            "accept_downloads": True,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            "extra_http_headers": {
                "Accept-Language": fingerprint["accept_language"],
                "User-Agent": fingerprint["user_agent"],
            }
        }

        if self.proxy:
            proxy_config = {"server": self.proxy}
            if "@" in self.proxy: # Basic auth check
                parts = self.proxy.split("@")
                auth_parts = parts[0].split("://")[1].split(":")
                proxy_config["username"] = auth_parts[0]
                proxy_config["password"] = auth_parts[1]
            context_options["proxy"] = proxy_config
            logger.info(f"Using proxy: {self.proxy}")

        self.browser = await p.chromium.launch(**launch_options)
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()

        # Set additional stealth properties
        await self.page.evaluate(f""" 
            Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
            Object.defineProperty(navigator, 'platform', {{ get: () => '{fingerprint['platform']}' }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {fingerprint['device_memory']} }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {fingerprint['hardware_concurrency']} }});
        """)

        logger.info("Browser launched successfully with stealth settings.")
        return self.page

    async def close(self) -> None:
        """Closes the browser instance."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            logger.info("Browser closed.")

    async def goto(self, url: str, timeout: Optional[int] = None) -> None:
        """Navigates the page to a given URL.

        Args:
            url: The URL to navigate to.
            timeout: Maximum navigation time in milliseconds, defaults to Playwright config.
        """
        if not self.page:
            raise RuntimeError("Browser page not initialized. Call launch() first.")
        try:
            await self.page.goto(url, timeout=timeout if timeout else self.config["PLAYWRIGHT"]["TIMEOUT"])
            logger.info(f"Navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            raise

    async def get_page(self) -> Page:
        """Returns the current page object."""
        if not self.page:
            raise RuntimeError("Browser page not initialized. Call launch() first.")
        return self.page

if __name__ == "__main__":
    from utils.logger import setup_logging
    setup_logging("DEBUG")

    async def main():
        # Example with proxy
        # stealth_browser = StealthBrowser(proxy="http://user:pass@1.1.1.1:8080")
        stealth_browser = StealthBrowser()
        try:
            page = await stealth_browser.launch()
            await stealth_browser.goto("https://www.whatismybrowser.com/detect/what-is-my-user-agent")
            await asyncio.sleep(5) # Give time for page to load and display info
            # You can add assertions here to check if user agent is as expected
            logger.info("Successfully navigated to user agent detection page.")
        except Exception as e:
            logger.error(f"StealthBrowser example failed: {e}")
        finally:
            await stealth_browser.close()

    asyncio.run(main())
