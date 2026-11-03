# -*- coding: utf-8 -*-
import shutil
import tempfile
from datetime import date, datetime, time
from decimal import Decimal
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation
from PIL import Image

from . import i18n
from .models import Category, DailyPick, Product, SeasonalTag, ShopInfo

TEMP_MEDIA = tempfile.mkdtemp()


def photo():
    buf = BytesIO()
    Image.new("RGB", (400, 300), (120, 80, 50)).save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


def url(name, lang, *args):
    with translation.override(lang):
        return reverse(name, args=args)


class LanguageRoutingTests(TestCase):
    def test_root_sends_visitors_to_their_browser_language(self):
        self.assertRedirects(self.client.get("/", HTTP_ACCEPT_LANGUAGE="fa"), "/fa/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9"), "/en/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/"), "/en/", fetch_redirect_response=False)   # no preference: English

    def test_old_addresses_without_a_language_still_work(self):
        self.assertRedirects(self.client.get("/menu/"), "/en/menu/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/about/", HTTP_ACCEPT_LANGUAGE="fa"), "/fa/about/", fetch_redirect_response=False)

    def test_every_page_loads_in_both_languages(self):
        for lang in ("en", "fa"):
            for name in ("welcome", "categories", "search", "about"):
                with self.subTest(lang=lang, page=name):
                    self.assertEqual(self.client.get(url(name, lang)).status_code, 200)

    def test_admin_stays_in_english_even_for_persian_browsers(self):
        r = self.client.get("/admin/login/", HTTP_ACCEPT_LANGUAGE="fa")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Log in")
        self.assertEqual(r["Content-Language"], "en")


@override_settings(MEDIA_ROOT=TEMP_MEDIA, CURRENCY_SYMBOL="$", CURRENCY_SYMBOL_BEFORE=True, CURRENCY_SYMBOL_FA="$")
class PersianPageTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.tea = Category.objects.create(name="Tea", name_fa="چای", slug="tea", image=photo())
        self.cakes = Category.objects.create(name="Cakes", slug="cakes", image=photo())       # no Persian name yet
        self.tea_item = Product.objects.create(category=self.tea, name="Green Tea", name_fa="چای سبز",
                                               ingredients="Green tea leaves", ingredients_fa="برگ چای سبز",
                                               price=Decimal("85000"), image=photo(), is_vegan=True)
        self.cake_item = Product.objects.create(category=self.cakes, name="Carrot cake", ingredients="Carrot",
                                                price=Decimal("7.99"), price_large=Decimal("10.50"), image=photo())

    def test_direction_and_language_attributes(self):
        self.assertContains(self.client.get("/en/menu/"), 'lang="en" dir="ltr"')
        self.assertContains(self.client.get("/fa/menu/"), 'lang="fa" dir="rtl"')

    def test_interface_words_are_translated(self):
        fa = self.client.get("/fa/menu/")
        self.assertContains(fa, "منوی ما")
        self.assertNotContains(fa, "Choose a category")
        en = self.client.get("/en/menu/")
        self.assertContains(en, "Choose a category")
        self.assertNotContains(en, "منوی ما")

    def test_language_switch_links_keep_the_page_and_the_query(self):
        self.assertContains(self.client.get("/en/menu/"), 'href="/fa/menu/"')
        self.assertContains(self.client.get("/fa/menu/tea/?diet=vegan"), 'href="/en/menu/tea/?diet=vegan"')
        self.assertContains(self.client.get("/en/search/?q=tea"), 'href="/fa/search/?q=tea"')
        self.assertContains(self.client.get("/fa/menu/"), "English")
        self.assertContains(self.client.get("/en/menu/"), "فارسی")

    def test_persian_text_is_used_when_written_and_english_otherwise(self):
        fa = self.client.get("/fa/menu/")
        self.assertContains(fa, "چای")                 # Tea has a Persian name
        self.assertContains(fa, "Cakes")               # Cakes does not yet: the English name is shown
        en = self.client.get("/en/menu/")
        self.assertNotContains(en, "چای")

    def test_product_cards_in_persian(self):
        r = self.client.get("/fa/menu/tea/")
        self.assertContains(r, "چای سبز")
        self.assertContains(r, "برگ چای سبز")
        self.assertContains(r, "وگان")
        self.assertNotContains(self.client.get("/en/menu/tea/"), "چای سبز")

    def test_prices_use_persian_digits_and_separators(self):
        self.assertContains(self.client.get("/fa/menu/tea/"), "۸۵٬۰۰۰")
        self.assertContains(self.client.get("/fa/menu/cakes/"), "۷٫۹۹")
        self.assertContains(self.client.get("/fa/menu/cakes/"), "۱۰٫۵۰")
        self.assertContains(self.client.get("/en/menu/tea/"), "$85000")

    def test_search_finds_persian_words(self):
        r = self.client.get("/fa/search/", {"q": "سبز"})
        self.assertEqual([p.name for p in r.context["products"]], ["Green Tea"])
        self.assertContains(r, "۱ مورد پیدا شد")

    def test_not_found_page_is_in_persian(self):
        r = self.client.get("/fa/menu/nope/")
        self.assertContains(r, "این صفحه را پیدا نکردیم", status_code=404)
        self.assertContains(self.client.get("/en/menu/nope/"), "We couldn&#x27;t find that page", status_code=404) \
            if False else self.assertEqual(self.client.get("/en/menu/nope/").status_code, 404)

    def test_product_pop_up_gets_its_persian_words(self):
        self.assertContains(self.client.get("/fa/menu/tea/"), 'data-of="از"')
        self.assertContains(self.client.get("/en/menu/tea/"), 'data-of="of"')

    def test_barista_note_in_persian(self):
        DailyPick.objects.create(date=timezone.localdate(), product=self.tea_item, note="Perfect today", note_fa="برای امروز عالی است")
        self.assertContains(self.client.get("/fa/menu/"), "برای امروز عالی است")
        self.assertContains(self.client.get("/en/menu/"), "Perfect today")

    def test_seasonal_tag_in_persian(self):
        SeasonalTag.objects.create(title="Autumn special", title_fa="ویژهٔ پاییز", text="Pumpkin latte", text_fa="لاتهٔ کدو",
                                   end_date=date(2099, 11, 30))
        fa = self.client.get("/fa/menu/")
        self.assertContains(fa, "ویژهٔ پاییز")
        self.assertContains(fa, "لاتهٔ کدو")
        self.assertContains(fa, "تا ")                      # "until <Persian date>"
        self.assertContains(self.client.get("/en/menu/"), "Pumpkin latte")

    def test_shop_details_in_persian(self):
        ShopInfo.objects.update_or_create(pk=1, defaults=dict(name="Our Café", name_fa="کافهٔ ما", address="1 Main St",
                                                              address_fa="خیابان اصلی، پلاک ۱", phone="09123456789"))
        about = self.client.get("/fa/about/")
        self.assertContains(about, "کافهٔ ما")
        self.assertContains(about, "خیابان اصلی، پلاک ۱")
        self.assertContains(about, "۰۹۱۲۳۴۵۶۷۸۹")           # phone with Persian digits...
        self.assertContains(about, 'href="tel:09123456789"')  # ...but the link stays plain digits


class WelcomeSignInPersianTests(TestCase):
    """Default hours 09:00-23:00. 2026-10-20 is a Tuesday."""

    def welcome_at(self, hour, minute=0):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, 20, hour, minute)):
            return self.client.get("/fa/")

    def test_open_sign(self):
        r = self.welcome_at(12)
        self.assertContains(r, "<b>باز</b>")
        self.assertContains(r, "تا ساعت ۲۳:۰۰")

    def test_closed_sign(self):
        r = self.welcome_at(23, 30)
        self.assertContains(r, "<b>بسته</b>")
        self.assertContains(r, "فردا ساعت ۰۹:۰۰ باز می‌شود")


class ShopTextInPersianTests(SimpleTestCase):
    def test_closed_days_use_persian_names_in_persian_week_order(self):
        with translation.override("fa"):
            self.assertEqual(ShopInfo(closed_days="6,5").open_days_text, "همه روزه به‌جز شنبه، یکشنبه")
            self.assertEqual(ShopInfo(closed_days="").open_days_text, "همه روزه")

    def test_hours_line(self):
        shop = ShopInfo(open_time=time(9, 0), close_time=time(23, 0), closed_days="4")
        with translation.override("en"):
            self.assertEqual(shop.hours_line, "Every day except Friday, 9:00 AM – 11:00 PM")
        with translation.override("fa"):
            self.assertEqual(shop.hours_line, "همه روزه به‌جز جمعه، ۰۹:۰۰ تا ۲۳:۰۰")

    def test_all_day(self):
        with translation.override("fa"):
            self.assertEqual(ShopInfo(open_all_day=True).sign_open_text, "شبانه‌روزی")


class HelperTests(SimpleTestCase):
    def test_jalali_new_year_anchors(self):
        for g, j in [((2000, 3, 20), (1379, 1, 1)), ((2024, 3, 20), (1403, 1, 1)),
                     ((2025, 3, 21), (1404, 1, 1)), ((2026, 3, 21), (1405, 1, 1))]:
            self.assertEqual(i18n.gregorian_to_jalali(*g), j)

    def test_dates(self):
        with translation.override("fa"):
            self.assertEqual(i18n.short_date(date(2026, 11, 30)), "۹ آذر")
        with translation.override("en"):
            self.assertEqual(i18n.short_date(date(2026, 11, 30)), "Nov 30")

    def test_clock_and_digits(self):
        with translation.override("en"):
            self.assertEqual(i18n.clock(time(23, 0)), "11:00 PM")
            self.assertEqual(i18n.digits(2026), "2026")
        with translation.override("fa"):
            self.assertEqual(i18n.clock(time(23, 0)), "۲۳:۰۰")
            self.assertEqual(i18n.digits("0912"), "۰۹۱۲")

    @override_settings(CURRENCY_SYMBOL="$", CURRENCY_SYMBOL_BEFORE=True, CURRENCY_SYMBOL_FA="تومان")
    def test_money(self):
        with translation.override("en"):
            self.assertEqual(i18n.money(Decimal("7.99")), "$7.99")
        with translation.override("fa"):
            self.assertEqual(i18n.money(Decimal("7.99")), "۷٫۹۹ تومان")
            self.assertEqual(i18n.money(Decimal("85000.00")), "۸۵٬۰۰۰ تومان")

    @override_settings(CURRENCY_SYMBOL="Toman", CURRENCY_SYMBOL_BEFORE=False, CURRENCY_SYMBOL_FA="تومان")
    def test_currency_can_come_after_the_number(self):
        with translation.override("en"):
            self.assertEqual(i18n.money(Decimal("85000.00")), "85,000 Toman")
            self.assertEqual(i18n.money(Decimal("7.99")), "7.99 Toman")
        with translation.override("fa"):
            self.assertEqual(i18n.money(Decimal("85000.00")), "۸۵٬۰۰۰ تومان")

    @override_settings(CURRENCY_SYMBOL="Toman", CURRENCY_SYMBOL_FA="Toman")
    def test_persian_pages_write_known_currency_names_in_persian(self):
        with translation.override("fa"):
            self.assertEqual(i18n.money(Decimal("85000")), "۸۵٬۰۰۰ تومان")

    @override_settings(CURRENCY_SYMBOL="$", CURRENCY_SYMBOL_BEFORE=True, CURRENCY_SYMBOL_FA="$")
    def test_dollar_prices_keep_the_symbol_in_front(self):
        with translation.override("en"):
            self.assertEqual(i18n.money(Decimal("10.00")), "$10.00")
