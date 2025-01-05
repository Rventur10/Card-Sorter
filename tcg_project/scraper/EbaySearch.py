import os
from dotenv import load_dotenv
from ebaysdk.exception import ConnectionError
from ebaysdk.finding import Connection
from .models import cards

# Load environment variables from .env file
load_dotenv()
APP_ID = os.getenv('API_KEY')


class FetchPrice:
    def __init__(self, keyword, app_id):
        self.api_key = app_id
        self.keyword = keyword

    def fetch(self):
        try:
            # Initialize the eBay API connection
            api = Connection(appid=self.api_key, config_file=None)
            
            # Perform the search
            response = api.execute('findItemsAdvanced', {
                'keywords': self.keyword,  # Search term
                'paginationInput.entriesPerPage': 5,  # Limit to 5 items
                'sortOrder': 'PricePlusShippingLowest',  # Sort by price including shipping            
            })
            
            response_dict = response.dict()
            items = response_dict.get('searchResult', {}).get('item', [])
            if items:
            # Extract prices for all returned items
                prices = [
                float(item.get('sellingStatus', {}).get('currentPrice', {}).get('value'))
                for item in items if item.get('sellingStatus', {}).get('currentPrice', {}).get('value')
            ]
            
            # Sort the prices and calculate the average of the top 3 items
                prices.sort()  # Ensure prices are sorted in ascending order
                top_3_prices = prices[:2]  # Take the top 3 prices
                avg_price = sum(top_3_prices) / len(top_3_prices) if top_3_prices else 0
                
                return round(avg_price, 2)  # Return the average price of the top 3 items
            else:
                print("No items found.")
                return None
        
        except ConnectionError as e:
            print("An error occurred while connecting to eBay:", e)
            print("Error details:", e.response.dict())
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None
        
        



# Function to start the eBay search process
def start_ebay_search():
    # Fetch all cards from the database
    all_cards = cards.objects.all()

    cards_to_update = []
    for card in all_cards:
        
        try:
            # Construct search strings for PSA 9 and PSA 10
            
            if '&' in card.card_name:
                # Split card_name by '&' and strip spaces from the resulting parts
                name_part = card.card_name.split('&')[0].strip()
                second_part = card.card_name.split('&')[1].strip() if len(card.card_name.split('&')) > 1 else ""
                
                psa_9_search = f"{name_part} {second_part} {card.card_number.split('/')[0].strip()} PSA 9"
                psa_10_search = f"{name_part} {second_part} {card.card_number.split('/')[0].strip()} PSA 10"
            else:
                psa_9_search = f"{card.card_name.strip()} {card.card_number.split('/')[0].strip()} PSA 9"
                psa_10_search = f"{card.card_name.strip()} {card.card_number.split('/')[0].strip()} PSA 10"
            
            psa_9_fetcher = FetchPrice(psa_9_search, APP_ID)
            psa_10_fetcher = FetchPrice(psa_10_search, APP_ID)
            psa_9_price = psa_9_fetcher.fetch()
            psa_10_price = psa_10_fetcher.fetch()
        
            if psa_9_price is not None:
                card.psa_9_price = psa_9_price
            if psa_10_price is not None:
                card.psa_10_price = psa_10_price
            
            cards_to_update.append(card)
        except Exception as e:
    # Log the error and continue with the next card
            print(f"Error fetching prices for card {card.card_name}: {e}")
            continue

# Perform bulk update
    cards.objects.bulk_update(cards_to_update, ['psa_9_price', 'psa_10_price'])