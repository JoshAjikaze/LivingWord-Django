"""One-off visual verification: screenshot the key public + auth pages."""
import asyncio

from playwright.async_api import async_playwright

PAGES = [
    ("home", "http://127.0.0.1:8000/"),
    ("signup", "http://127.0.0.1:8000/accounts/signup/"),
    ("login", "http://127.0.0.1:8000/accounts/login/"),
    ("password_reset", "http://127.0.0.1:8000/accounts/password/reset/"),
    ("books_list", "http://127.0.0.1:8000/books/"),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium")
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        for name, url in PAGES:
            await page.goto(url)
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"/home/ubuntu/livingword-django/tests/shots/{name}.png", full_page=True)
            print("captured", name, page.url)
        await browser.close()


asyncio.run(main())
