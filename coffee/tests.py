import shutil
import tempfile
from datetime import datetime
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .models import Category, DailyPick, Product, ShopInfo
from .views import todays_pick

TEMP_MEDIA = tempfile.mkdtemp()


def fake_photo(size=(400, 300), name="photo.png"):
    buf = BytesIO()
    Image.new("RGB", size, (120, 80, 50)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class MenuTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.hot = Category.objects.create(name="Hot", slug="hot", image=fake_photo(), order=0)
        self.cakes = Category.objects.create(name="Cakes", slug="cakes", image=fake_photo(), order=1)  # stays empty
        self.latte = Product.objects.create(category=self.hot, name="Latte", ingredients="Espresso, milk",
                                            price="6.99", price_large="8.99", image=fake_photo(), is_caffeine_free=False)
        self.soldout = Product.objects.create(category=self.hot, name="Mocha", ingredients="Chocolate",
                                              price="7.50", image=fake_photo(), available=False)
        self.vegan = Product.objects.create(category=self.hot, name="Oat flat white", ingredients="Espresso, oat milk",
                                            price="7.00", image=fake_photo(), is_vegan=True)

    def test_all_pages_load(self):
        for name, args in [("welcome", []), ("categories", []), ("category_detail", ["hot"]),
                           ("search", []), ("about", [])]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200)

    def test_unknown_category_shows_friendly_404(self):
        r = self.client.get("/menu/does-not-exist/")
        self.assertContains(r, "couldn't find that page", status_code=404)

    def test_sold_out_items_stay_visible_but_sink_to_the_bottom(self):
        r = self.client.get(reverse("category_detail", args=["hot"]))
        names = [p.name for p in r.context["products"]]
        self.assertEqual(names[-1], "Mocha")
        self.assertContains(r, "Sold out today")

    def test_vegan_filter(self):
        r = self.client.get(reverse("category_detail", args=["hot"]), {"diet": "vegan"})
        self.assertEqual([p.name for p in r.context["products"]], ["Oat flat white"])

    def test_unknown_filter_is_ignored(self):
        r = self.client.get(reverse("category_detail", args=["hot"]), {"diet": "nonsense"})
        self.assertEqual(len(r.context["products"]), 3)

    def test_empty_category_is_hidden_from_navbar_but_marked_coming_soon(self):
        r = self.client.get(reverse("categories"))
        self.assertEqual([c.slug for c in r.context["nav_categories"]], ["hot"])
        self.assertContains(r, "Coming soon")

    def test_categories_follow_the_order_set_in_admin(self):
        Category.objects.create(name="Tea", slug="tea", image=fake_photo(), order=5)
        Product.objects.create(category=Category.objects.get(slug="tea"), name="Black", ingredients="x", price="1", image=fake_photo())
        Category.objects.filter(slug="hot").update(order=9)          # Hot now sorts after Cakes and Tea
        r = self.client.get(reverse("categories"))
        self.assertEqual([c.slug for c in r.context["categories"]], ["cakes", "tea", "hot"])
        self.assertEqual([c.slug for c in r.context["nav_categories"]], ["tea", "hot"])   # Cakes is empty

    def test_search_matches_ingredients_and_includes_sold_out(self):
        r = self.client.get(reverse("search"), {"q": "chocolate"})
        self.assertEqual([p.name for p in r.context["products"]], ["Mocha"])

    def test_barista_pick_skips_sold_out_choice(self):
        DailyPick.objects.create(date=timezone.localdate(), product=self.soldout, note="x")
        product, _ = todays_pick()
        self.assertTrue(product.available)

    def test_barista_pick_uses_todays_choice(self):
        DailyPick.objects.create(date=timezone.localdate(), product=self.vegan, note="Cozy")
        product, note = todays_pick()
        self.assertEqual((product, note), (self.vegan, "Cozy"))

    def test_new_uploads_are_shrunk_and_converted_to_webp(self):
        p = Product.objects.create(category=self.hot, name="Big", ingredients="x", price="1",
                                   image=fake_photo(size=(3000, 2000), name="huge.png"))
        self.assertTrue(p.image.name.endswith(".webp"))
        with Image.open(p.image.path) as im:
            self.assertLessEqual(max(im.size), 1000)

    def test_resaving_does_not_recompress_the_photo(self):
        before = self.latte.image.name
        self.latte.name = "Latte (renamed)"
        self.latte.save()
        self.assertEqual(self.latte.image.name, before)

    def test_prices_show_both_sizes_only_when_there_is_a_large_price(self):
        r = self.client.get(reverse("category_detail", args=["hot"]))
        self.assertContains(r, "Large", count=1)


class OpeningHoursTests(TestCase):
    """2026-10-19 is a Monday (weekday 0)."""

    def open_at(self, shop, day, hour, minute=0):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, day, hour, minute)):
            return shop.is_open_now()

    def test_regular_hours_with_a_closed_day(self):
        shop = ShopInfo(open_time="09:00", close_time="23:00", closed_days="0")   # closed Mondays
        shop.open_time, shop.close_time = datetime(2026, 1, 1, 9).time(), datetime(2026, 1, 1, 23).time()
        self.assertTrue(self.open_at(shop, 20, 10))        # Tuesday 10:00
        self.assertFalse(self.open_at(shop, 20, 8, 59))    # before opening
        self.assertFalse(self.open_at(shop, 20, 23, 30))   # after closing
        self.assertFalse(self.open_at(shop, 19, 12))       # Monday: closed day

    def test_overnight_hours_belong_to_the_day_they_started(self):
        shop = ShopInfo(closed_days="1")                   # closed Tuesdays
        shop.open_time, shop.close_time = datetime(2026, 1, 1, 18).time(), datetime(2026, 1, 1, 2).time()
        self.assertTrue(self.open_at(shop, 19, 19))        # Monday evening
        self.assertTrue(self.open_at(shop, 20, 1))         # Tuesday 01:00 = Monday's session
        self.assertFalse(self.open_at(shop, 20, 19))       # Tuesday evening: closed day
        self.assertFalse(self.open_at(shop, 21, 1))        # Wednesday 01:00 = Tuesday's session (closed)
        self.assertFalse(self.open_at(shop, 19, 10))       # Monday midday: between sessions

    def test_open_all_day_respects_closed_days(self):
        shop = ShopInfo(open_all_day=True, closed_days="6")  # closed Sundays
        self.assertTrue(self.open_at(shop, 24, 3))           # Saturday 03:00
        self.assertFalse(self.open_at(shop, 25, 12))         # Sunday

    def test_text_summaries(self):
        self.assertEqual(ShopInfo(closed_days="").open_days_text, "Every day")
        self.assertEqual(ShopInfo(closed_days="0").open_days_text, "Every day except Monday")
        self.assertEqual(ShopInfo(phone="+98 (21) 123-456").phone_link, "+9821123456")
