from playwright.sync_api import sync_playwright
import pandas as pd
import requests
import os

# ================= CONFIG =================

ASINS = [
    "B0D9BHX9MZ",
    "B0D9BPK1NV",
    "B0BX46DVXZ",
    "B0F99GWXLL",
    "B0D9BLY9J9",
    "B0F99HW555"
]

PINCODE = "110001"

OUTPUT_FILE = "amazon_price_seller_report.xlsx"

# Telegram credentials from GitHub Secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= SCRAPER =================

results = []

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    page = browser.new_context(locale="en-IN").new_page()

    for asin in ASINS:

        print(f"Processing {asin}")

        page.goto(f"https://www.amazon.in/dp/{asin}")
        page.wait_for_selector("#productTitle")

        # Apply pincode
        try:
            page.locator("#contextualIngressPtLabel").click()
            page.locator("#GLUXZipUpdateInput").fill(PINCODE)
            page.locator("#GLUXZipUpdate").click()
            page.wait_for_timeout(3000)
        except:
            pass

        # Price
        try:
            price = page.locator(".a-price-whole").first.text_content()
            price = price.strip()
        except:
            price = "Not Available"

        # Seller
        try:
            seller = page.locator("#sellerProfileTriggerId").first.text_content()
            seller = seller.strip()
        except:
            seller = "Not Available"

        results.append({
            "ASIN": asin,
            "Pincode": PINCODE,
            "Price": price,
            "Seller": seller
        })

    browser.close()

# ================= SAVE =================

df = pd.DataFrame(results)
df.to_excel(OUTPUT_FILE, index=False)

print("Excel created")

# ================= TELEGRAM SEND =================

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"

with open(OUTPUT_FILE, "rb") as f:
    requests.post(
        url,
        data={"chat_id": CHAT_ID},
        files={"document": f}
    )

print("Report sent to Telegram")
