import shutil
import tempfile
from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

from .models import Category, Product, SeasonalTag

TEMP_MEDIA = tempfile.mkdtemp()


def photo():
    buf = BytesIO()
    Image.new("RGB", (400, 300), (120, 80, 50)).save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


def on(day):
    """Pretend today is `day`."""
    return patch("coffee.models.timezone.localdate", return_value=day)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class SeasonalTagTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.tea = Category.objects.create(name="Tea", slug="tea", image=photo())
        self.latte = Product.objects.create(category=self.tea, name="Pumpkin latte", ingredients="x", price="6", image=photo())

    def tag(self, **kw):
        defaults = dict(title="Autumn special", text="Pumpkin latte")
        defaults.update(kw)
        return SeasonalTag.objects.create(**defaults)

    # ---- where it shows ----
    def test_nothing_is_shown_when_there_is_no_tag(self):
        self.assertNotContains(self.client.get("/menu/"), "season-tag")

    def test_shown_on_the_menu_page_only(self):
        self.tag()
        self.assertContains(self.client.get("/menu/"), "Pumpkin latte")
        for url in ["/", "/menu/tea/", "/about/", "/search/"]:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), "season-tag")

    # ---- when it shows ----
    def test_date_window(self):
        self.tag(start_date=date(2026, 11, 1), end_date=date(2026, 11, 30))
        for day, shown in [(date(2026, 10, 31), False), (date(2026, 11, 1), True),
                           (date(2026, 11, 30), True), (date(2026, 12, 1), False)]:
            with self.subTest(day=day), on(day):
                self.assertEqual(SeasonalTag.current() is not None, shown)

    def test_switched_off_tag_is_hidden(self):
        self.tag(active=False)
        self.assertIsNone(SeasonalTag.current())

    def test_newest_tag_wins_when_two_are_running(self):
        self.tag(text="Old")
        self.tag(text="New one")
        self.assertEqual(SeasonalTag.current().text, "New one")

    def test_end_date_cannot_be_before_start_date(self):
        with self.assertRaises(ValidationError):
            SeasonalTag(title="a", text="b", start_date=date(2026, 11, 5), end_date=date(2026, 11, 1)).clean()

    # ---- what it says / where it goes ----
    def test_bottom_line_is_made_from_the_end_date_unless_written(self):
        self.assertEqual(self.tag(end_date=date(2026, 11, 30)).note_text, "until Nov 30")
        self.assertEqual(self.tag(end_date=date(2026, 11, 30), note="While it lasts").note_text, "While it lasts")
        self.assertEqual(self.tag().note_text, "")

    def test_link_to_an_item_opens_its_pop_up(self):
        t = self.tag(product=self.latte)
        self.assertEqual(t.link_url, f"/menu/tea/#p{self.latte.id}")
        self.assertContains(self.client.get("/menu/"), f'href="/menu/tea/#p{self.latte.id}"')

    def test_link_to_a_category(self):
        self.assertEqual(self.tag(category=self.tea).link_url, "/menu/tea/")

    def test_without_a_link_it_is_not_clickable(self):
        self.tag()
        r = self.client.get("/menu/")
        self.assertContains(r, '<div class="season-tag">')
        self.assertNotContains(r, '<a class="season-tag"')

    def test_deleting_the_linked_item_keeps_the_tag(self):
        t = self.tag(product=self.latte)
        self.latte.delete()
        t.refresh_from_db()
        self.assertIsNone(t.product)
        self.assertEqual(t.link_url, "")

    # ---- admin ----
    def test_admin_pages_work(self):
        owner = get_user_model().objects.create_superuser("owner", "o@example.com", "pw12345!")
        self.client.force_login(owner)
        self.tag(end_date=date(2026, 11, 30))
        for url in ["/admin/coffee/seasonaltag/", "/admin/coffee/seasonaltag/add/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
