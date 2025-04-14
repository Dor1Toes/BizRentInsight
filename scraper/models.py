from django.db import models

# Scraped currently available properties from LoopNet
class Property(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    address = models.CharField(max_length=255)
    market = models.CharField(max_length=255)
    submarket = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    city = models.CharField(max_length=100)
    space = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    availability = models.CharField(max_length=100)
    image = models.URLField(max_length=255)
    access_link = models.URLField(max_length=255)
    is_expired = models.BooleanField(default=False)
    categories = models.CharField(max_length=255,default="")
    transport_density = models.IntegerField(default=0)
    shopping_density = models.IntegerField(default=0)
    healthcare_density = models.IntegerField(default=0)
    education_density = models.IntegerField(default=0)
    competitor_density = models.IntegerField(default=0)
    RestaurantsPriceRange = models.IntegerField(default=1)
    Adjusted_Price = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.property_id} - {self.submarket}"