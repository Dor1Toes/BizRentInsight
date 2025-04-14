import pandas as pd
from django.core.management.base import BaseCommand
from scraper.models import Property  # 替换为你的 app 名

class Command(BaseCommand):
    help = 'Import adjusted house prices and update Property table based on postal_code.'

    def add_arguments(self, parser):
        parser.add_argument('--csv_file', type=str, default='avg_price_zip\\UK_price_per_zip.csv', help='Path to the CSV file containing postal_code and Adjusted_Price')

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        df = pd.read_csv(csv_path)

        updated = 0
        not_found = 0

        for _, row in df.iterrows():
            postal_code = row['postal_code']
            price = row['Adjusted_Price']

            properties = Property.objects.filter(postal_code__iexact=postal_code)

            if properties.exists():
                properties.update(Adjusted_Price=price)
                updated += properties.count()
            else:
                not_found += 1

        self.stdout.write(self.style.SUCCESS(f"Updated prices for {updated} properties."))
        if not_found > 0:
            self.stdout.write(f"{not_found} postal codes were not matched in the database.")
