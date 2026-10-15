from django.db import models
import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
import re
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone

def optimize_image(upload, max_width=800, quality=80):
    """Resize to max_width and convert to WebP. Returns (filename, ContentFile)."""
    img = Image.open(upload)
    img = ImageOps.exif_transpose(img)            # fixes sideways phone photos
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    name = os.path.splitext(os.path.basename(upload.name))[0] + ".webp"
    return name, ContentFile(buf.getvalue())
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

    def save(self, *args, **kwargs):
            if self.image and not self.image._committed:     # only for newly uploaded files
                name, data = optimize_image(self.image, max_width=900)
                self.image.save(name, data, save=False)
            super().save(*args, **kwargs)

class Product(models.Model):
    BADGES = [("", "None"), ("new", "New"), ("popular", "Popular"), ("seasonal", "Seasonal")]

    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    ingredients = models.TextField(help_text="e.g. Espresso, steamed milk, foam")
    image = models.ImageField(upload_to="products/")

    # Prices
    price = models.DecimalField("Price (medium)", max_digits=6, decimal_places=2,
                                help_text="The regular price. For items without sizes, like cakes, this is the only price.")
    price_large = models.DecimalField("Price (large)", max_digits=6, decimal_places=2,
                                      null=True, blank=True,
                                      help_text="Leave empty if the item has no sizes")

    # Availability and badge
    available = models.BooleanField(default=True, help_text="Untick when sold out; it will show greyed out")
    badge = models.CharField(max_length=10, choices=BADGES, blank=True)

    # Dietary labels
    is_vegan = models.BooleanField("Vegan", default=False)
    is_caffeine_free = models.BooleanField("Caffeine-free", default=False)
    has_nuts = models.BooleanField("Contains nuts", default=False)
    has_dairy = models.BooleanField("Contains dairy", default=False)

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            name, data = optimize_image(self.image, max_width=800)
            self.image.save(name, data, save=False)
        super().save(*args, **kwargs)

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


import re
from datetime import time
from django.db import models
from django.utils import timezone


class ShopInfo(models.Model):
    DAYS = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
            (4, "Friday"), (5, "Saturday"), (6, "Sunday")]

    name = models.CharField(max_length=100, default="Our Café")
    story = models.TextField(blank=True, help_text="A short, friendly paragraph about the café")
    photo = models.ImageField(upload_to="about/", blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    instagram = models.URLField(blank=True, help_text="Full link, e.g. https://instagram.com/yourcafe")
    telegram = models.URLField(blank=True, help_text="Full link, e.g. https://t.me/yourcafe")
    map_embed_url = models.URLField(blank=True, help_text="Google Maps → Share → Embed a map → copy the src URL")

    # Working hours
    open_all_day = models.BooleanField(default=False, help_text="Open 24 hours (times below are ignored)")
    open_time = models.TimeField(default=time(9, 0))
    close_time = models.TimeField(default=time(23, 0), help_text="A time earlier than opening means it closes after midnight")
    closed_days = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name_plural = "shop info"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.name

    @property
    def phone_link(self):
        return re.sub(r"[^\d+]", "", self.phone)

    @property
    def closed_day_numbers(self):
        return {int(d) for d in self.closed_days.split(",") if d}

    @property
    def open_days_text(self):
        closed = self.closed_day_numbers
        names = dict(self.DAYS)
        if not closed:
            return "Every day"
        if len(closed) == 7:
            return "Closed"
        return "Every day except " + ", ".join(names[d] for d in sorted(closed))

    def is_open_now(self):
        now = timezone.localtime()
        today = now.weekday()
        closed = self.closed_day_numbers

        if self.open_all_day:
            return today not in closed

        t = now.time()
        if self.open_time <= self.close_time:              # normal day, e.g. 09:00–23:00
            return today not in closed and self.open_time <= t <= self.close_time

        # Overnight, e.g. 18:00–02:00
        if t >= self.open_time:                            # evening part belongs to today
            return today not in closed
        if t <= self.close_time:                           # after midnight: yesterday's session
            return (today - 1) % 7 not in closed
        return False
    

class DailyPick(models.Model):
    date = models.DateField(unique=True, default=timezone.localdate)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    note = models.CharField(max_length=200, blank=True,
                            help_text="One line from the barista, e.g. 'Perfect with the rain today'")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date}: {self.product}"