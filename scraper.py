from playwright.sync_api import sync_playwright
import requests
import os
import time
from datetime import datetime

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

# ================= TELEGRAM FUNCTION =================

def send_telegram_message(results):

    now = datetime.now().strftime("%d %b %H:%M")

    text = f"📦 Amazon ASIN Monitor ({now})\n\n"

    if len(results) == 0:
        text += "⚠️ No data scraped.\nAmazon may have blocked the request."
    else:
        for r in results:
            text += f"{r['ASIN']} → {r['Seller']} | ₹{r['Price']}\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })

    print("Telegram Status:", response.status_code)
    print("Telegram Response:", response.text)

# ================= PDP OPEN FUNCTION =================

def open_pdp(page, asin):

    url = f"https://www.amazon.in/dp/{asin}"

    for attempt in range(3):

        try:
            print(f"Opening {asin} (Attempt {attempt+1})")

            page.goto(url, timeout=120000)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_selector("#productTitle", timeout=60000)

            return True

        except:
            print(f"PDP load failed for {asin}")
            time.sleep(5)

    return False

# ================= SCRAPER =================

results = []

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    context = browser.new_context(locale="en-IN")
    page = context.new_page()

    for asin in ASINS:

        print(f"\nProcessing ASIN: {asin}")

        if not open_pdp(page, asin):

            results.append({
                "ASIN": asin,
                "Seller": "PDP Failed",
                "Price": "NA"
            })
            continue

        # Apply pincode
        try:
            page.locator("#contextualIngressPtLabel").click()
            page.locator("#GLUXZipUpdateInput").fill(PINCODE)
            page.locator("#GLUXZipUpdate").click()
            page.wait_for_timeout(4000)
        except:
            print("Pincode apply skipped")

        # Extract price
        try:
            price = page.locator(".a-price-whole").first.text_content()
            price = price.strip()
        except:
            price = "NA"

        # Extract seller
        try:
            seller = page.locator("#sellerProfileTriggerId").first.text_content()
            seller = seller.strip()
        except:
            seller = "NA"

        print(f"Seller: {seller}")
        print(f"Price: ₹{price}")

        results.append({
            "ASIN": asin,
            "Seller": seller,
            "Price": price
        })

    browser.close()

# ================= SEND TELEGRAM =================

send_telegram_message(results)

print("\nMonitor run completed")
