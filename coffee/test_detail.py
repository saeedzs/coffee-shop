import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Category, Product

TEMP_MEDIA = tempfile.mkdtemp()


def photo():
    buf = BytesIO()
    Image.new("RGB", (400, 300), (120, 80, 50)).save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProductDetailMarkupTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.cat = Category.objects.create(name="Hot", slug="hot", image=photo())
        self.latte = Product.objects.create(category=self.cat, name="Latte", ingredients="Espresso, milk", price="6", image=photo())

    def test_cards_are_tap_targets_with_their_product_id(self):
        r = self.client.get(reverse("category_detail", args=["hot"]))
        self.assertContains(r, f'data-product="{self.latte.id}"')
        self.assertContains(r, 'class="card-open"')

    def test_dialog_is_on_category_and_search_pages(self):
        for url in [reverse("category_detail", args=["hot"]), reverse("search") + "?q=latte"]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), 'id="product-dialog"')

    def test_barista_pick_links_straight_to_the_item(self):
        r = self.client.get(reverse("categories"))
        self.assertContains(r, f"#p{self.latte.id}")
