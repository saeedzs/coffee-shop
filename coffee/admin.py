from django.contrib import admin

# Register your models here.
from .models import Category, Product, ShopInfo, OpeningHour, DailyPick

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "order")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "available")
    list_filter = ("category", "available")
    
@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ShopInfo.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(OpeningHour)
class OpeningHourAdmin(admin.ModelAdmin):
    list_display = ("day", "all_day", "open_time", "close_time", "closed")
    list_editable = ("all_day", "open_time", "close_time", "closed")
    actions = ["make_all_day", "make_closed"]

    @admin.action(description="Mark selected days as open all day")
    def make_all_day(self, request, queryset):
        queryset.update(all_day=True, closed=False)

    @admin.action(description="Mark selected days as closed")
    def make_closed(self, request, queryset):
        queryset.update(closed=True, all_day=False)
        
    from .models import DailyPick

@admin.register(DailyPick)
class DailyPickAdmin(admin.ModelAdmin):
    list_display = ("date", "product", "note")