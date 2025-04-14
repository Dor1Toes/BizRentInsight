from django.shortcuts import render
from scraper.models import Property
import json
import pandas as pd
from BizRent.count_competitors import update_properties_with_competitor_density
from ml_model.ml_utils.predict import predict_success_for_properties


# show the home page
def homePage(request):
    return render(request, "home_page.html")

# show the searched results
def results(request):
    market = request.GET.get("market", "")
    submarket = request.GET.get("submarket", "")
    raw_categories = request.GET.get("categories", "")
    categories =  ", ".join(part.strip() for part in raw_categories.split(','))

    # 打印接收到的参数，确保它们正确
    print("Market:", market)
    print("Submarket:", submarket)
    print("Categories:", categories)

    properties = Property.objects.all()
    properties = properties.filter(market=market, submarket=submarket)
    # 一开始就过滤掉没有经纬度的
    properties = [p for p in properties if p.longitude and p.latitude]
    # 赋值为选择的categories
    for prop in properties:
        prop.categories =  categories
        print(prop.address)
    
    updated_props = update_properties_with_competitor_density(properties, market)

    # 预测
    predict_df = predict_success_for_properties(updated_props)
    predict_df_sorted = predict_df.sort_values(by='success_index', ascending=False)
    print(predict_df_sorted.head())

    wanted_attrs = [
    'id', 'address', 'price','space','availability',
    'market','submarket','access_link','image','categories',
    'RestaurantsPriceRange',
    'competitor_density', 'transport_density',
    'shopping_density', 'education_density',
    'healthcare_density', 'success_index'
    ]

    # 保证只选中你需要的字段（如果字段不存在会自动跳过）
    filtered_df = predict_df_sorted[[col for col in wanted_attrs if col in predict_df_sorted.columns]]

    # 转换为字典列表
    records = filtered_df.to_dict(orient='records')

    # 转换为 JSON 字符串
    result_json = json.dumps(records, indent=2)
    
    return render(request, 'results_page.html', {'properties_json': result_json})

