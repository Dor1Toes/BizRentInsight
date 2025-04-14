# yourapp/management/commands/update_postcode_coords.py

import requests
from django.core.management.base import BaseCommand
from scraper.models import Property

class Command(BaseCommand):
    help = 'Update lat/lon from postcode using postcodes.io API'

    def handle(self, *args, **kwargs):
        properties = Property.objects.exclude(postal_code__isnull=True).exclude(postal_code__exact='')

        updated = 0
        skipped = 0

        for prop in properties:
            if prop.latitude and prop.longitude:
                skipped += 1
                continue

            url = f"https://api.postcodes.io/postcodes/{prop.postal_code}"

            try:
                response = requests.get(url, timeout=5)
                data = response.json()

                if response.status_code == 200 and data.get("status") == 200:
                    result = data["result"]
                    prop.latitude = result["latitude"]
                    prop.longitude = result["longitude"]
                    prop.save()
                    updated += 1

            except Exception as e:
                self.stderr.write(f"Exception for {prop.postal_code}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"\nDone. Updated: {updated}, Skipped: {skipped}"))
