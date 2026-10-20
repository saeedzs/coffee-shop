from django.conf import settings
from django.db.models import Count

from .models import Category, ShopInfo


def site(request):
    """Values every page needs: shop details, navbar categories, currency."""
    return {
        "shop": ShopInfo.load(),
        # Empty categories are left out of the navbar until they have products
        "nav_categories": Category.objects.annotate(item_count=Count("products")).filter(item_count__gt=0).order_by("order", "name"),
        "currency": getattr(settings, "CURRENCY_SYMBOL", "$"),
    }
