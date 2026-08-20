"""End-to-end browser test of signup → email verification → profile."""
import asyncio
import subprocess

from playwright.async_api import async_playwright

import uuid

BASE = "http://127.0.0.1:8000"
EMAIL = f"grace+{uuid.uuid4().hex[:6]}@example.com"
NAME = "Grace Reader"


def confirm_key():
    out = subprocess.check_output(
        [
            "python3",
            "manage.py",
            "shell",
            "-c",
            "from allauth.account.models import EmailAddress, EmailConfirmationHMAC;"
            "ea = EmailAddress.objects.get(email='" + EMAIL + "');"
            "print(EmailConfirmationHMAC.create(ea).key)",
        ],
        cwd="/home/ubuntu/livingword-django",
    )
    return out.decode().strip().splitlines()[-1]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/chromium")
        ctx = await b.new_context()
        page = await ctx.new_page()

        # 1. Signup
        await page.goto(f"{BASE}/accounts/signup/")
        await page.fill("#id_name", NAME)
        await page.fill("#id_email", EMAIL)
        await page.fill("#id_password1", "SecureP@ssword1")
        await page.fill("#id_password2", "SecureP@ssword1")
        await page.click("button[type=submit]")
        await page.wait_for_load_state("networkidle")
        print("1. After signup:", page.url)
        assert "confirm-email" in page.url

        # 2. Confirm email via generated key
        key = confirm_key()
        print("2. Confirmation key:", key)
        await page.goto(f"{BASE}/accounts/confirm-email/{key}/")
        await page.wait_for_load_state("networkidle")
        print("3. Confirm page:", page.url)
        html = await page.content()
        open("/tmp/confirm_page.html", "w").write(html)
        print("   has Confirm button:", "Confirm my email" in html)
        if "confirm-email" in page.url:
            await page.get_by_role("button", name="Confirm my email").click()
            await page.wait_for_load_state("networkidle")
            print("4. After confirm:", page.url)
            await page.screenshot(path="/home/ubuntu/livingword-django/tests/shots/email_confirmed.png", full_page=True)

        # 3. Log in with the now-verified credentials
        await page.goto(f"{BASE}/accounts/login/")
        await page.fill("#id_login", EMAIL)
        await page.fill("#id_password", "SecureP@ssword1")
        await page.click("button[type=submit]")
        await page.wait_for_load_state("networkidle")
        print("4b. After login:", page.url)

        # 4. Check nav now shows logged-in state + profile
        await page.goto(f"{BASE}/")
        await page.wait_for_load_state("networkidle")
        nav = await page.text_content("nav")
        print("5. Nav contains My account:", "My account" in nav)
        print("6. Nav contains Sign in:", "Sign in" in nav)

        await page.goto(f"{BASE}/accounts/profile/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path="/home/ubuntu/livingword-django/tests/shots/profile.png", full_page=True)
        print("7. Profile url:", page.url)
        await b.close()


asyncio.run(main())
