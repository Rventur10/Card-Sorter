from django.db import models

class Card(models.Model):
    
    product_url = models.URLField(max_length=500, blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)  # Store the S3 URL
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=50)
    tcg_price = models.DecimalField(max_digits=10, decimal_places=2)
    psa_9_price = models.DecimalField(max_digits=10, decimal_places=2)
    psa_10_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.number} - ${self.price}"
    
    class Meta:
        db_table = 'cards'
