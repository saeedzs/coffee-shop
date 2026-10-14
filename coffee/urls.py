from django.urls import path
from . import views

urlpatterns = [
    path("", views.welcome, name="welcome"),
    path("coffee/", views.categories, name="categories"),
    path("coffee/<slug:slug>/", views.category_detail, name="category_detail"),
    path("search/", views.search, name="search"),
    path("about/", views.about, name="about"),
]
