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

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(available=True)
    return render(request, "coffee/category_detail.html",
                  {"category": category, "products": products})
    
def search(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(available=True).filter(
            Q(name__icontains=query) |
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related("category")
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