import re
from datetime import time

from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.dateformat import time_format
from django.utils.formats import date_format

from .images import optimize_on_upload


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
        optimize_on_upload(self.image)
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
        optimize_on_upload(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
        self.pk = 1                      # only ever one record
        optimize_on_upload(self.photo)
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

    @property
    def open_until_text(self):
        """Shown while open: 'Open until 11:00 PM' or 'Open 24 hours'."""
        if self.open_all_day:
            return "Open 24 hours"
        return "Open until " + time_format(self.close_time, "g:i A")

    @property
    def next_opening_text(self):
        """Shown while closed: 'Opens today at 9:00 AM', 'Opens tomorrow at ...',
        'Opens Monday at ...'. Empty if the café is closed every day."""
        now = timezone.localtime()
        closed = self.closed_day_numbers
        names = dict(self.DAYS)
        opening = time(0, 0) if self.open_all_day else self.open_time
        for offset in range(8):
            day = (now.weekday() + offset) % 7
            if day in closed:
                continue
            if offset == 0 and now.time() >= opening:          # today's opening is already behind us
                continue
            when = "today" if offset == 0 else "tomorrow" if offset == 1 else names[day]
            if self.open_all_day:
                return f"Opens {when}"
            return f"Opens {when} at {time_format(opening, 'g:i A')}"
        return ""


class DailyPick(models.Model):
    date = models.DateField(unique=True, default=timezone.localdate)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    note = models.CharField(max_length=200, blank=True,
                            help_text="One line from the barista, e.g. 'Perfect with the rain today'")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date}: {self.product}"


class SeasonalTag(models.Model):
    """The small hanging tag on the menu page: a seasonal special, a short announcement..."""
    title = models.CharField(max_length=30, help_text="Small top line, e.g. Autumn special")
    text = models.CharField(max_length=40, help_text="Main line, e.g. Pumpkin latte")
    note = models.CharField(max_length=30, blank=True,
                            help_text="Small bottom line. Leave empty to show 'until <end date>' automatically")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Optional: tapping the tag opens this item")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text="Optional: tapping the tag opens this category (ignored if an item is chosen)")
    start_date = models.DateField(null=True, blank=True, help_text="Leave empty to show it right away")
    end_date = models.DateField(null=True, blank=True, help_text="Last day it is shown. Leave empty to keep it until you switch it off")
    active = models.BooleanField(default=True, help_text="Untick to hide it without deleting")

    class Meta:
        ordering = ["-id"]
        verbose_name = "seasonal tag"

    def __str__(self):
        return f"{self.title}: {self.text}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("The end date can't be before the start date.")

    @classmethod
    def current(cls):
        """The tag to show today (the newest one, if several are running), or None."""
        today = timezone.localdate()
        return (cls.objects.filter(active=True)
                .filter(Q(start_date__isnull=True) | Q(start_date__lte=today))
                .filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
                .select_related("product__category", "category")
                .first())

    @property
    def is_showing(self):
        today = timezone.localdate()
        return (self.active
                and (self.start_date is None or self.start_date <= today)
                and (self.end_date is None or self.end_date >= today))

    @property
    def note_text(self):
        if self.note:
            return self.note
        if self.end_date:
            return "until " + date_format(self.end_date, "M j")
        return ""

    @property
    def link_url(self):
        if self.product_id:
            return f"{self.product.category.get_absolute_url()}#p{self.product_id}"
        if self.category_id:
            return self.category.get_absolute_url()
        return ""
