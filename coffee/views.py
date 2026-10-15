from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from .models import Product,ShopInfo
from .models import DailyPick

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Category

def welcome(request):
    return render(request, "coffee/welcome.html")

def categories(request):
    return render(request, "coffee/categories.html", {"categories": Category.objects.all()})

DIET_FILTERS = {
    "vegan": {"is_vegan": True},
    "caffeine_free": {"is_caffeine_free": True},
}

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
    query = request.GET.get("q", "").strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related("category").order_by("-available", "name")
    return render(request, "menu/search.html", {"products": products, "query": query})


def about(request):
    info = ShopInfo.load()
    return render(request, "coffee/about.html", {
        "info": info,
        "open_now": info.is_open_now(),
    })
    

def todays_pick():
    today = timezone.localdate()
    pick = DailyPick.objects.filter(date=today).select_related("product__category").first()
    if pick:
        return pick.product, pick.note
    products = list(Product.objects.filter(available=True)
                    .select_related("category").order_by("id"))
    if products:                       # fallback: rotate by date
        return products[today.toordinal() % len(products)], ""
    return None, ""

def categories(request):
    pick, note = todays_pick()
    return render(request, "coffee/categories.html", {
        "categories": Category.objects.all(),
        "pick": pick, "pick_note": note,
    })

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(available=True)
    pick, _ = todays_pick()
    return render(request, "coffee/category_detail.html", {
        "category": category, "products": products,
        "pick_id": pick.id if pick else None,
    })