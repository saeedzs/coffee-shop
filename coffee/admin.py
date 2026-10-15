from django import forms
from django.contrib import admin
from .models import Category, Product, ShopInfo, DailyPick


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "order")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "price_large", "badge", "available")
    list_editable = ("badge", "available")
    list_filter = ("category", "available", "badge")
    search_fields = ("name", "ingredients")
    actions = ["mark_sold_out", "mark_available"]

    fieldsets = (
        (None, {"fields": ("category", "name", "image", "ingredients")}),
        ("Prices", {"fields": ("price", "price_large")}),
        ("Badge and availability", {"fields": ("badge", "available")}),
        ("Dietary labels", {"fields": (("is_vegan", "is_caffeine_free"), ("has_nuts", "has_dairy"))}),
    )

    @admin.action(description="Mark selected as SOLD OUT")
    def mark_sold_out(self, request, queryset):
        queryset.update(available=False)

    @admin.action(description="Mark selected as available again")
    def mark_available(self, request, queryset):
        queryset.update(available=True)

@admin.register(DailyPick)
class DailyPickAdmin(admin.ModelAdmin):
    list_display = ("date", "product", "note")


class ShopInfoForm(forms.ModelForm):
    closed_days = forms.MultipleChoiceField(
        choices=ShopInfo.DAYS,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Closed days",
        help_text="Tick the days the café is closed. Leave empty if it's open every day.",
    )

    class Meta:
        model = ShopInfo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        value = self.instance.closed_days if self.instance.pk else ""
        self.initial["closed_days"] = value.split(",") if value else []

    def clean_closed_days(self):
        return ",".join(self.cleaned_data["closed_days"])


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    form = ShopInfoForm

    def has_add_permission(self, request):
        return not ShopInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False