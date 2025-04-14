import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


RADIUS = 1000  # 米

def update_properties_with_competitor_density(properties, market,yelp_folder='yelp_data'):
    """
    给传入的 properties 列表（QuerySet）更新 competitor_density 字段，
    使用对应城市的 CSV 文件作为竞争对手来源。
    """

    # 预加载城市的 CSV 数据为 GeoDataFrame
    csv_path = os.path.join(yelp_folder, f"{market}.csv")
    df = pd.read_csv(csv_path, encoding='utf-8', encoding_errors='replace')
    df['geometry'] = df.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326').to_crs(epsg=3395)

    # 逐个 property 计算竞争对手密度
    result_list = []

    for prop in properties:
        if prop.longitude is None or prop.latitude is None:
            continue

        business_point = Point(prop.longitude, prop.latitude)
        business_geom = gpd.GeoSeries([business_point], crs='EPSG:4326').to_crs(epsg=3395).iloc[0]
        buffer = business_geom.buffer(RADIUS)

        prop_categories = set(str(prop.categories).split(", "))

        # 类别匹配的 competitor
        filtered = gdf[gdf["categories"].apply(
            lambda x: bool(prop_categories.intersection(set(str(x).split(", "))))
        )]

        nearby = filtered[filtered.geometry.intersects(buffer)]
        prop.competitor_density = len(nearby)
        result_list.append(prop)

    return result_list
