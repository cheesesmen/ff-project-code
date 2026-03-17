from django.contrib import admin
from .models import GenshinAccount, DeltaAccount

@admin.register(GenshinAccount)
class GenshinAdmin(admin.ModelAdmin):
    # list_display 定义了你在后台列表里能看到的列
    list_display = ('product_id', 'price', 'level', 'show_title')
    # search_fields 增加了搜索框，可以搜商品ID或标题
    search_fields = ('product_id', 'show_title')

@admin.register(DeltaAccount)
class DeltaAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'price', 'show_title')