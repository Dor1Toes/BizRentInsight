import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from django.core.management.base import BaseCommand
from scraper.models import Property

# 半径和 POI 类型
RADIUS = 1000
POI_CATEGORY_DICT = {
    "transport": {"stop_position", "bus_station", "bus_stop", "tram_stop", "halt", "station", "taxi"},
    "shopping": {"supermarket", "mall", "department_store"},
    "education": {"school", "university", "college", "library"},
    "healthcare": {"hospital", "clinic", "veterinary", "pharmacy"},
}


class Command(BaseCommand):
    help = 'Update POI densities for businesses by city based on corresponding POI CSV files.'

    def add_arguments(self, parser):
        parser.add_argument('--poi_folder', type=str, default='osm_data', help='Path to POI folder')

    def handle(self, *args, **options):
        poi_folder = options['poi_folder']

        # 加载所有城市的 POI GeoDataFrame
        city_poi_gdfs = {}
        for city in ['London', 'Birmingham', 'Manchester']:
            poi_file = os.path.join(poi_folder, f"{city}.csv")
            if not os.path.exists(poi_file):
                self.stdout.write(self.style.WARNING(f"POI file for {city} not found, skipping."))
                continue

            poi_df = pd.read_csv(poi_file, encoding='utf-8', encoding_errors='replace')
            poi_df['geometry'] = poi_df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
            poi_gdf = gpd.GeoDataFrame(poi_df, geometry='geometry', crs='EPSG:4326').to_crs(epsg=3395)
            city_poi_gdfs[city] = poi_gdf

        # 加载properties数据
        business_qs = Property.objects.all()
        business_data = []
        for b in business_qs:
            if b.longitude is None or b.latitude is None:
                continue  # 跳过没有坐标的记录
            business_data.append({
                'id': b.id,
                'market': b.market,
                'geometry': Point(b.longitude, b.latitude)
            })
        business_gdf = gpd.GeoDataFrame(business_data, geometry='geometry', crs='EPSG:4326').to_crs(epsg=3395)

        # 初始化密度列
        for category in POI_CATEGORY_DICT.keys():
            business_gdf[f"{category}_density"] = 0

        # 按城市分组处理
        for city, group_df in business_gdf.groupby("market"):
            if city not in city_poi_gdfs:
                self.stdout.write(self.style.WARNING(f"No POI data for city: {city}, skipping."))
                continue

            city_poi = city_poi_gdfs[city]

            for idx, business in group_df.iterrows():
                for category_key, valid_types in POI_CATEGORY_DICT.items():
                    buffer = business.geometry.buffer(RADIUS)
                    category_pois = city_poi[city_poi["type"].isin(valid_types)]
                    count = category_pois[category_pois.geometry.intersects(buffer)].shape[0]
                    business_gdf.at[idx, f"{category_key}_density"] = count

        # 更新数据库中 Business 实例
        for _, row in business_gdf.iterrows():
            try:
                b = Property.objects.get(id=row["id"])
                for category_key in POI_CATEGORY_DICT.keys():
                    setattr(b, f"{category_key}_density", row[f"{category_key}_density"])
                b.save()
            except Property.DoesNotExist:
                continue

        self.stdout.write(self.style.SUCCESS("POI density update complete."))
