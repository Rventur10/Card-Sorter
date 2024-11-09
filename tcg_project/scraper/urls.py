from django.urls import path
from .views import scrape_view
from .views import EbayMarketplaceAccountDeletion

urlpatterns = [
    path('scrape/', scrape_view, name='scrape'),
    path('ebayapi/', EbayMarketplaceAccountDeletion.as_view(), name='ebay-marketplace-account-deletion'),
]