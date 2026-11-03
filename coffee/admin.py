from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, DailyPick, Product, SeasonalTag, ShopInfo

admin.site.site_header = "Café admin"
admin.site.site_title = "Café admin"


def thumbnail(image):
    if not image:
        return "—"
    return format_html('<img src="{}" style="height:44px;width:58px;object-fit:cover;border-radius:6px;">', image.url)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("photo", "name", "order", "product_count", "has_persian")
    list_display_links = ("photo", "name")
    list_editable = ("order",)
    search_fields = ("name", "name_fa")
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "image", "order"),
                "description": "Write the name in ENGLISH here and the Persian name in the “Persian version (فارسی)” section below."}),
        ("Persian version (فارسی)", {"fields": ("name_fa", "description_fa"),
                                    "description": "Optional. If left empty, the English text is shown on the Persian page."}),
    )

    @admin.display(description="Photo")
    def photo(self, obj):
        return thumbnail(obj.image)

    @admin.display(description="Products")
    def product_count(self, obj):
        return obj.products.count()

    @admin.display(description="Persian", boolean=True)
    def has_persian(self, obj):
        return bool(obj.name_fa)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("photo", "name", "category", "price", "price_large", "badge", "available", "has_persian")
    list_display_links = ("photo", "name")
    list_editable = ("badge", "available")
    list_filter = ("category", "available", "badge")
    search_fields = ("name", "name_fa", "ingredients", "ingredients_fa")
    ordering = ("category__order", "name")
    list_per_page = 30
    actions = ["mark_sold_out", "mark_available"]

    fieldsets = (
        (None, {"fields": ("category", "name", "image", "ingredients"),
                "description": "Write the name and ingredients in ENGLISH here. The Persian name and ingredients go in "
                               "the “Persian version (فارسی)” section at the bottom. Customers see each language on its own page."}),
        ("Prices", {"fields": ("price", "price_large")}),
        ("Badge and availability", {"fields": ("badge", "available")}),
        ("Dietary labels", {"fields": (("is_vegan", "is_caffeine_free"), ("has_nuts", "has_dairy"))}),
        ("Persian version (فارسی)", {"fields": ("name_fa", "ingredients_fa"),
                                    "description": "Optional. If left empty, the English text is shown on the Persian page."}),
    )

    @admin.display(description="Photo")
    def photo(self, obj):
        return thumbnail(obj.image)

    @admin.display(description="Persian", boolean=True)
    def has_persian(self, obj):
        return bool(obj.name_fa and obj.ingredients_fa)

    @admin.action(description="Mark selected as SOLD OUT")
    def mark_sold_out(self, request, queryset):
        queryset.update(available=False)

    @admin.action(description="Mark selected as available again")
    def mark_available(self, request, queryset):
        queryset.update(available=True)


@admin.register(DailyPick)
class DailyPickAdmin(admin.ModelAdmin):
    list_display = ("date", "product", "note")
    autocomplete_fields = ["product"]


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
    fieldsets = (
        ("The café", {"fields": ("name", "story", "photo")}),
        ("Contact", {"fields": ("address", "phone", "email")}),
        ("Persian version (فارسی)", {"fields": ("name_fa", "story_fa", "address_fa"),
                                    "description": "Optional. If left empty, the English text is shown on the Persian page."}),
        ("Working hours", {"fields": ("open_all_day", ("open_time", "close_time"), "closed_days")}),
        ("Social links and map", {"fields": ("instagram", "telegram", "map_embed_url")}),
    )

    def has_add_permission(self, request):
        return not ShopInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SeasonalTag)
class SeasonalTagAdmin(admin.ModelAdmin):
    list_display = ("title", "text", "start_date", "end_date", "active", "showing_now")
    list_editable = ("active",)
    autocomplete_fields = ["product", "category"]
    fieldsets = (
        ("What it says", {"fields": ("title", "text", "note")}),
        ("Persian version (فارسی)", {"fields": ("title_fa", "text_fa", "note_fa"),
                                    "description": "Optional. If left empty, the English text is shown on the Persian page."}),
        ("Where tapping it goes (optional)", {"fields": ("product", "category")}),
        ("When it shows", {"fields": ("start_date", "end_date", "active")}),
    )

    @admin.display(description="Showing now", boolean=True)
    def showing_now(self, obj):
        return obj.is_showing
