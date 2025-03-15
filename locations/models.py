from django.db import models

# Create your models here
class Location(models.Model):
    name = models.CharField(max_length=200)  # 地点名称
    address = models.TextField()  # 详细地址
    latitude = models.FloatField()  # 纬度
    longitude = models.FloatField()  # 经度
    rental_price = models.FloatField()  # 租金价格
    competitor_density = models.IntegerField()  # 竞争对手数量
    traffic_score = models.FloatField()  # 交通评分
    suitability_score = models.FloatField(default=0)  # 适合度评分

    def __str__(self):
        return self.name