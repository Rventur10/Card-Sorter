import asyncio
from playwright.async_api import async_playwright

async def search_and_wait(page, query):
    search_bar = page.locator('input[type="text"][aria-label="Search for anything"]')
    await search_bar.fill(query)
    await search_bar.press("Enter")
    await page.wait_for_selector('.srp-results')
    avg_price = await find_prices(page)
    return avg_price

async def find_prices(page):
    sold_items_selector = 'input[aria-label="Sold Items"]'
    try:
        sold_button = page.locator(sold_items_selector)
        if await sold_button.count() > 0:
            await sold_button.click()
            await page.wait_for_selector('.srp-results')

            total_results_text = await page.locator('.srp-controls__count-heading > span:nth-child(1)').inner_text()
            total_results = int(total_results_text.replace(',', ''))

            prices = []
            price_elements = await page.locator('.s-item__price').all_inner_texts()

            if total_results > 12:
                prices = price_elements[:12]
            else:
                prices = price_elements[:total_results]

            prices = prices[2:]  # Adjust if you need to skip the first two prices

            def parse_price(price_str):
                if 'to' in price_str:
                    return None  # Skip price ranges
                else:
                    return float(price_str.replace('$', '').replace(',', ''))

            prices = [parse_price(price) for price in prices]
            prices = [price for price in prices if price is not None]  # Filter out None values

            if prices:
                total_prices = sum(prices)
                avg_price = total_prices / len(prices)
                avg_price = round(avg_price, 2)
            else:
                avg_price = 0
        else:
            avg_price = 0

    except Exception as e:
        print(f"Error finding prices: {e}")
        avg_price = 0

    await page.goto("https://www.ebay.com/")
    return avg_price

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.ebay.com/")

        with open("card_data.txt", "r") as input_file:
            cards = input_file.readlines()

        with open("ebay_card_data.txt", "w") as output_file:
            for card in cards:
                parts = card.strip().split(': ')[:3]
                parts[1] = parts[1].split('/')[0]
                parts[0] = parts[0].split('(')[0]
                tcg_price = float(parts[2]) + 15  # Adjust the price
                search_query = ' '.join(parts[:2])

                search_query_10 = search_query + " PSA 10 -stamp -world"
                search_query_9 = search_query + " PSA 9 -stamp -world"

                # Search for PSA 10
                avg_p10_prices = await search_and_wait(page, search_query_10)

                # Search for PSA 9
                avg_p9_prices = await search_and_wait(page, search_query_9)

                output_file.write(f"{search_query} - TCG: {round(tcg_price, 2)}, PSA 10: {avg_p10_prices} ({round((avg_p10_prices/tcg_price)*100, 2)}%), PSA 9: {avg_p9_prices} ({round((avg_p9_prices/tcg_price)*100, 2)}%)\n")

        await context.close()
        await browser.close()

# Run the main function
asyncio.run(main())
