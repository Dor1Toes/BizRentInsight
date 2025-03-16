from django.db import models

# Scraped currently available properties from LoopNet
class Property(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    address = models.CharField(max_length=255)
    market = models.CharField(max_length=255)
    submarket = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    space = models.CharField(max_length=100)
    price = models.CharField(max_length=100)
    availability = models.CharField(max_length=100)
    image = models.URLField(max_length=255)
    access_link = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.property_id} - {self.submarket}"