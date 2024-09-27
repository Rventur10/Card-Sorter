import asyncio
from playwright.async_api import async_playwright

async def fetch_card_data(page, index):
    try:
        parent_test_id = f"product-card__image--{index}"
        parent_element = page.locator(f'a[data-testid="{parent_test_id}"]')

        name = await parent_element.locator('span.product-card__title.truncate').inner_text()
        name = name.split('-')[0].strip()

        number = await parent_element.locator('section.product-card__rarity').inner_text()
        number = number.split('#')[1].strip()

        price = await parent_element.locator('span.product-card__market-price--value').inner_text()
        price = float(price.split('$')[1])
        
        return name, number, price
    except Exception as e:
        print(f"Error processing card #{index}: {e}")
        return None, None, None

async def process_page(page, output_file):
    tasks = [fetch_card_data(page, i) for i in range(24)]
    results = await asyncio.gather(*tasks)
    for i, (name, number, price) in enumerate(results):
        if name and number and price:
            output_file.write(f"{name}: {number}: {price}\n")

async def main():
    async with async_playwright() as p:
        browser = await p.firefox.launch() 
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to the page
        await page.goto("https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page=1&RarityName=Ultra+Rare%7CHyper+Rare%7CSecret+Rare&setName=swsh07-evolving-skies%7Cswsh06-chilling-reign%7Cswsh10-astral-radiance%7Cswsh11-lost-origin%7Csm-cosmic-eclipse%7Cswsh12-silver-tempest%7Ccrown-zenith-galarian-gallery%7Cswsh09-brilliant-stars%7Cswsh08-fusion-strike%7Cswsh05-battle-styles%7Cswsh04-vivid-voltage%7Cswsh02-rebel-clash%7Cswsh01-sword-and-shield-base-set%7Cswsh03-darkness-ablaze%7Csv02-paldea-evolved%7Csv04-paradox-rift%7Cswsh10-astral-radiance-trainer-gallery%7Cswsh11-lost-origin-trainer-gallery%7Cswsh12-silver-tempest-trainer-gallery%7Cswsh09-brilliant-stars-trainer-gallery%7Cswsh-sword-and-shield-promo-cards%7Csv01-scarlet-and-violet-base-set%7Csv06-twilight-masquerade%7Csv05-temporal-forces%7Csv03-obsidian-flames")
        
        # Open a file to write output
        with open("card_data.txt", "w") as output_file:
            # Process each page
            for _ in range(53): # Assuming there are 53 pages
                await process_page(page, output_file)
                next_page = page.get_by_label('Next page') 
                await next_page.click()
            
        await context.close()
        await browser.close()

# Run the main function
asyncio.run(main())
