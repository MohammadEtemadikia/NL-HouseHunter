from playwright.async_api import async_playwright
import asyncio
import json
import os
from datetime import datetime
from telegram import Bot

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

DATA_FILE = "seen_ads.json"

seen_ads = set()
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            seen_ads = set(json.load(f))
    except:
        pass

async def send_telegram(msg):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=msg, disable_web_page_preview=True)

async def get_pararius_new():
    new_ads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.pararius.com/apartments/nederland/600-1000/25m2", timeout=60000)
        await page.wait_for_timeout(5000)  # صبر برای لود JS

        # selectorهای احتمالی ۲۰۲۶ – می‌تونی بعداً تنظیم کنی
        cards = await page.query_selector_all("article, div[class*='listing'], li[class*='item'], div[data-testid*='listing']")

        for card in cards[:15]:
            try:
                link_el = await card.query_selector("a[href*='/for-rent/'], a[href*='/apartments/']")
                if not link_el: continue
                href = await link_el.get_attribute("href")
                link = "https://www.pararius.com" + href if href.startswith("/") else href
                unique = link.split("?")[0].rstrip("/")
                if unique in seen_ads: continue

                title = await (await card.query_selector("h2, h3, .title, [class*='address']")).inner_text() or "بدون عنوان"
                price_el = await card.query_selector("[class*='price'], .rent, strong")
                price = await price_el.inner_text() if price_el else ""

                # چک New
                new_el = await card.query_selector("text=/New|Nieuw/i")
                is_new = bool(new_el)

                seen_ads.add(unique)
                label = " (New!)" if is_new else ""
                new_ads.append(f"🆕 Pararius{label}\n{title.strip()}\n{price.strip()}\n{link}")
            except:
                pass
        await browser.close()
    return new_ads

# مشابه برای Funda – selectorها رو می‌تونی تنظیم کنی
async def get_funda_new():
    new_ads = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.funda.nl/zoeken/huur?selected_area=[%22nl%22]&price=%22500-1000%22&publication_date=%221%22", timeout=60000)
        await page.wait_for_timeout(8000)

        items = await page.query_selector_all("li[data-object-id], article, div[class*='search-result'], li[class*='result']")

        for item in items[:12]:
            try:
                link_el = await item.query_selector("a")
                if not link_el: continue
                href = await link_el.get_attribute("href")
                link = "https://www.funda.nl" + href if href.startswith("/") else href
                unique = link.split("?")[0].rstrip("/")
                if unique in seen_ads: continue

                title_el = await item.query_selector("h2, .title, [data-testid='listing-title']")
                title = await title_el.inner_text() if title_el else "بدون عنوان"

                price_el = await item.query_selector("[data-testid='price'], .price, strong")
                price = await price_el.inner_text() if price_el else ""

                new_el = await item.query_selector("text=/Nieuw|New/i")
                is_new = bool(new_el)

                seen_ads.add(unique)
                label = " (Nieuw!)" if is_new else ""
                new_ads.append(f"🆕 Funda{label}\n{title.strip()}\n{price.strip()}\n{link}")
            except:
                pass
        await browser.close()
    return new_ads

async def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not os.path.exists(DATA_FILE):
        await send_telegram(f"اسکریپر Playwright شروع شد - {now}")

    par_new = await get_pararius_new()
    fun_new = await get_funda_new()
    all_new = par_new + fun_new

    if all_new:
        msg = f"آگهی جدید پیدا شد ({len(all_new)}) — {now}\n\n" + "\n─────────────────\n".join(all_new)
        await send_telegram(msg)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ads), f, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
