from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Category, DailyPick, Product, SeasonalTag

DIET_FILTERS = {
    "vegan": {"is_vegan": True},
    "caffeine_free": {"is_caffeine_free": True},
}


def todays_pick():
    """The barista's pick: today's DailyPick if set (and in stock),
    otherwise rotate through the available products by date."""
    today = timezone.localdate()
    pick = (DailyPick.objects.filter(date=today, product__available=True)
            .select_related("product__category").first())
    if pick:
        return pick.product, pick.note

    available = Product.objects.filter(available=True).select_related("category").order_by("id")
    count = available.count()
    if count:
        return available[today.toordinal() % count], ""
    return None, ""


def welcome(request):
    return render(request, "coffee/welcome.html")


def categories(request):
    pick, note = todays_pick()
    return render(request, "coffee/categories.html", {
        "categories": Category.objects.annotate(item_count=Count("products")).order_by("order", "name"),
        "pick": pick,
        "pick_note": note,
        "season_tag": SeasonalTag.current(),
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()

    active_diet = request.GET.get("diet")
    if active_diet in DIET_FILTERS:
        products = products.filter(**DIET_FILTERS[active_diet])
    else:
        active_diet = None

    products = products.order_by("-available", "id")      # sold-out items sink to the bottom
    pick, _ = todays_pick()
    return render(request, "coffee/category_detail.html", {
        "category": category,
        "products": products,
        "pick_id": pick.id if pick else None,
        "active_diet": active_diet,
    })


def search(request):
    query = request.GET.get("q", "").strip()[:60]
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related("category").order_by("-available", "name")
    return render(request, "coffee/search.html", {"products": products, "query": query})


def about(request):
    # Shop details come from the `shop` context processor
    return render(request, "coffee/about.html")
