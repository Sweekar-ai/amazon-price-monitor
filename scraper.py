from playwright.sync_api import sync_playwright
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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= SCRAPER =================

results_text = []

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
            price = f"₹{price.strip()}"
        except:
            price = "Price NA"

        # Seller
        try:
            seller = page.locator("#sellerProfileTriggerId").first.text_content()
            seller = seller.strip()
        except:
            seller = "Seller NA"

        line = f"{asin} — {price} — Seller: {seller}"
        results_text.append(line)

    browser.close()

# ================= TELEGRAM MESSAGE =================

message = "📦 Amazon ASIN Monitor\n\n" + "\n".join(results_text)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("Telegram message sent")
