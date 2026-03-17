#from django.db import db
from django.db import models

class GenshinAccount(models.Model):
    """原神账号模型"""
    product_id = models.CharField(max_length=50, unique=True, verbose_name="商品ID")
    price = models.FloatField(verbose_name="价格")
    level = models.IntegerField(default=0, verbose_name="等级")
    assets_score = models.FloatField(default=0.0, verbose_name="资产分")
    show_title = models.TextField(verbose_name="商品标题")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="抓取时间")

    def __str__(self):
        return f"原神-{self.product_id}-{self.price}元"

class DeltaAccount(models.Model):
    """三角洲行动账号模型"""
    product_id = models.CharField(max_length=50, unique=True)
    price = models.FloatField()
    assets_m = models.FloatField(default=0.0, verbose_name="总资产(M)")
    hafu_w = models.FloatField(default=0.0, verbose_name="哈夫币(W)")
    show_title = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)