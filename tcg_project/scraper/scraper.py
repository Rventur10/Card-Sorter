import asyncio
from playwright.async_api import async_playwright
from scraper.models import Card

async def scrape_cards(page, index):
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

async def process_page(page):
    tasks = [scrape_cards(page, i) for i in range(24)]
    results = await asyncio.gather(*tasks)
    
    for name, number, price in results:
        if name and number and price:
            # Use get_or_create to avoid duplicates
            card, created = Card.objects.get_or_create(
                name=name,
                number=number,
                defaults={
                    'tcg_price': price
                }
            )

            if created:
                print(f"Added new card: {card}")
            else:
                print(f"Card already exists: {card}")

        elif price is not None and price < 5:
            print(f"Skipping card: {name} with price: {price}")
            
            
async def start_search ():
    async with async_playwright() as p:
        browser = await p.firefox.launch() 
        context = await browser.new_context()
        page = await context.new_page()

        # Navigate to the page
        await page.goto("https://www.tcgplayer.com/search/pokemon/product?productLineName=pokemon&view=grid&ProductTypeName=Cards&page=1&RarityName=Ultra+Rare|Hyper+Rare|Secret+Rare&setName=swsh07-evolving-skies|swsh06-chilling-reign|swsh10-astral-radiance|swsh11-lost-origin|sm-cosmic-eclipse|swsh12-silver-tempest|crown-zenith-galarian-gallery|swsh09-brilliant-stars|swsh08-fusion-strike|swsh05-battle-styles|swsh04-vivid-voltage|swsh02-rebel-clash|swsh01-sword-and-shield-base-set|swsh03-darkness-ablaze|sv02-paldea-evolved|sv04-paradox-rift|swsh10-astral-radiance-trainer-gallery|swsh11-lost-origin-trainer-gallery|swsh12-silver-tempest-trainer-gallery|swsh09-brilliant-stars-trainer-gallery|swsh-sword-and-shield-promo-cards|sv01-scarlet-and-violet-base-set|sv06-twilight-masquerade|sv05-temporal-forces|sv03-obsidian-flames|sv07-stellar-crown|sv-shrouded-fable")
        
        # Open a file to write output
        
        for _ in range(53): # Assuming there are 53 pages
            await process_page(page)
            next_page = page.get_by_label('Next page') 
            await next_page.click()
            
        await context.close()
        await browser.close()

