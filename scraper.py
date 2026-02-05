from playwright.sync_api import sync_playwright
import requests
import os
import time

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

results_text = []

def open_pdp(page, asin):

    url = f"https://www.amazon.in/dp/{asin}"

    for attempt in range(3):

        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            page.wait_for_selector("#productTitle", timeout=60000)
            return True

        except:
            print(f"Retry {attempt+1} for {asin}")
            time.sleep(5)

    return False

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    context = browser.new_context(locale="en-IN")
    page = context.new_page()

    for asin in ASINS:

        print(f"Processing {asin}")

        if not open_pdp(page, asin):
            results_text.append(f"{asin} — PDP Failed")
            continue

        # Apply pincode
        try:
            page.locator("#contextualIngressPtLabel").click()
            page.locator("#GLUXZipUpdateInput").fill(PINCODE)
            page.locator("#GLUXZipUpdate").click()
            page.wait_for_timeout(4000)
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

        results_text.append(f"{asin} — {price} — Seller: {seller}")

    browser.close()

message = "📦 Amazon ASIN Monitor\n\n" + "\n".join(results_text)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

requests.post(url, data={"chat_id": CHAT_ID, "text": message})

print("Telegram message sent")
