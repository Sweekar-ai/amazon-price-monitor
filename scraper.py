from playwright.sync_api import sync_playwright
import requests
import os
import time

# ================= CONFIG =================

ASINS = [
    "B0BX484K3Y",
    "B0D9BRS5WX",
    "B0F99HW555",
    "B0D9BLY9J9",
    "B0FSLDJQRV"
]

PINCODE = "110001"

# Hard-coded Product Names
ASIN_PRODUCT_MAP = {
    "B0BX484K3Y": "Creatine Unflavoured (250g)",
    "B0D9BRS5WX": "Creatine Fruit Fusion (307g)",
    "B0F99HW555": "Creatine Kiwi Kick (307g)",
    "B0D9BLY9J9": "Creatine Tropical Tango (307g)",
    "B0FSLDJQRV": "Creatine Watermelon Wave (307g)"
}

OWN_SELLER = "Wellversed Health"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ================= TELEGRAM =================

def send_telegram(message):

    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram secrets missing")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    res = requests.post(url, data=payload)

    print("Telegram Status:", res.status_code)
    print("Telegram Response:", res.text)

# ================= SCRAPER =================

results = []

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    context = browser.new_context(locale="en-IN")
    page = context.new_page()

    for asin in ASINS:

        print(f"Processing ASIN: {asin}")

        url = f"https://www.amazon.in/dp/{asin}"
        page.goto(url, timeout=60000)

        # Wait PDP
        try:
            page.wait_for_selector("#productTitle", timeout=30000)
        except:
            results.append((asin, "PDP Failed", "₹NA"))
            continue

        # Apply pincode
        try:
            page.locator("#contextualIngressPtLabel").click()
            page.wait_for_selector("#GLUXZipUpdateInput")
            page.fill("#GLUXZipUpdateInput", PINCODE)
            page.click("#GLUXZipUpdate")
            page.wait_for_timeout(3000)
        except:
            pass

        # Seller
        try:
            seller = page.locator("#sellerProfileTriggerId").inner_text()
        except:
            seller = "Unknown"

        # Price
        try:
            price = page.locator(".a-price-whole").first.inner_text()
            price = f"₹{price}"
        except:
            price = "₹NA"

        results.append((asin, seller, price))

    browser.close()

# ================= MESSAGE BUILDER =================

message = "🛡️ <b>HaukX Surveillance Alert</b>\n"
message += "━━━━━━━━━━━━━━━━━━━\n\n"

for asin, seller, price in results:

    product_name = ASIN_PRODUCT_MAP.get(asin, "Unknown Product")

    # Hijacker highlight
    seller_display = seller
    if seller != OWN_SELLER and seller != "Unknown":
        seller_display = f"🚨 {seller}"

    message += (
        f"📦 <b>{product_name}</b>\n"
        f"🔎 {asin}\n"
        f"👤 {seller_display}\n"
        f"💰 {price}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
    )

message += "\n⏱ Auto-monitored via HaukX Engine"

# ================= SEND =================

send_telegram(message)

print("Monitor run completed")
