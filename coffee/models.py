from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=60)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=140, blank=True)
    image = models.ImageField(upload_to="categories/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("category_detail", args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    ingredients = models.TextField(help_text="e.g. Espresso, steamed milk, foam")
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to="products/")
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class ShopInfo(models.Model):
    name = models.CharField(max_length=100, default="Our Café")
    story = models.TextField(blank=True, help_text="A short, friendly paragraph about the café")
    photo = models.ImageField(upload_to="about/", blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    instagram = models.URLField(blank=True, help_text="Full link, e.g. https://instagram.com/yourcafe")
    telegram = models.URLField(blank=True, help_text="Full link, e.g. https://t.me/yourcafe")
    map_embed_url = models.URLField(blank=True, help_text="Google Maps → Share → Embed a map → copy the src URL")

    class Meta:
        verbose_name_plural = "shop info"

    def save(self, *args, **kwargs):
        self.pk = 1                      # only ever one record
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name


class OpeningHour(models.Model):
    DAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
            (4, "Friday"), (5, "Saturday"), (6, "Sunday")]
    day = models.PositiveSmallIntegerField(choices=DAYS, unique=True)
    all_day = models.BooleanField(default=False, help_text="Open 24 hours, no times needed")
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["day"]

    def clean(self):
        if self.all_day and self.closed:
            raise ValidationError("A day can't be both 'closed' and 'all day'.")

    def __str__(self):
        return self.get_day_display()
    

class DailyPick(models.Model):
    date = models.DateField(unique=True, default=timezone.localdate)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    note = models.CharField(max_length=200, blank=True,
                            help_text="One line from the barista, e.g. 'Perfect with the rain today'")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date}: {self.product}"