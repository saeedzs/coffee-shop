# -*- coding: utf-8 -*-
import shutil
import tempfile
from io import BytesIO, StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from .models import Category, Product, ShopInfo

TEMP_MEDIA = tempfile.mkdtemp()


def photo():
    buf = BytesIO()
    Image.new("RGB", (400, 300), (120, 80, 50)).save(buf, "PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class FillPersianTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.hot = Category.objects.create(name="Hot Drinks", slug="hot-drinks", image=photo())
        self.cakes = Category.objects.create(name="Cakes", slug="cakes", description="Home-made cakes", image=photo())
        mk = lambda name, ing: Product.objects.create(category=self.hot, name=name, ingredients=ing, price="5", image=photo())
        self.espresso = mk("Esspersso", "Essperso")             # the typo in the real menu
        self.latte = mk("Latte", "Latte")
        self.lemonade = mk("Lemonade", "Lemonde")
        self.mystery = mk("Dragon fruit fizz", "Dragon fruit")  # not in the starter menu

    def run_command(self, *args):
        out = StringIO()
        call_command("fill_persian", *args, stdout=out)
        return out.getvalue()

    def test_dry_run_changes_nothing(self):
        text = self.run_command("--dry-run")
        self.assertIn("would be written", text)
        self.espresso.refresh_from_db()
        self.assertEqual(self.espresso.name_fa, "")

    def test_fills_names_and_ingredients_including_misspelled_ones(self):
        self.run_command()
        for obj in (self.espresso, self.latte, self.lemonade, self.hot, self.cakes):
            obj.refresh_from_db()
        self.assertEqual((self.espresso.name_fa, self.espresso.ingredients_fa), ("اسپرسو", "اسپرسو"))
        self.assertEqual(self.lemonade.name_fa, "لیموناد")
        self.assertEqual(self.hot.name_fa, "نوشیدنی‌های گرم")
        self.assertEqual((self.cakes.name_fa, self.cakes.description_fa), ("کیک", "کیک‌های خانگی"))

    def test_persian_ingredients_never_add_anything_new(self):
        self.run_command()
        self.latte.refresh_from_db()
        self.assertEqual(self.latte.ingredients_fa, "لاته")        # English says just "Latte": no invented milk or espresso

    def test_unknown_items_are_reported_and_left_alone(self):
        text = self.run_command()
        self.assertIn("Dragon fruit fizz", text)
        self.mystery.refresh_from_db()
        self.assertEqual((self.mystery.name_fa, self.mystery.ingredients_fa), ("", ""))

    def test_running_twice_changes_nothing_the_second_time(self):
        self.run_command()
        self.assertIn("for 0 item(s)", self.run_command())

    def test_existing_persian_text_is_kept_unless_overwrite(self):
        Product.objects.filter(pk=self.latte.pk).update(name_fa="لاتهٔ من")
        self.run_command()
        self.latte.refresh_from_db()
        self.assertEqual(self.latte.name_fa, "لاتهٔ من")
        self.run_command("--overwrite")
        self.latte.refresh_from_db()
        self.assertEqual(self.latte.name_fa, "لاته")

    def test_shop_details_filled_only_when_english_is_the_starter_text(self):
        ShopInfo.objects.update_or_create(pk=1, defaults=dict(name="Our Café", address="12 Real Street", story="We serve you with love"))
        self.run_command()
        shop = ShopInfo.load()
        self.assertEqual(shop.name_fa, "کافهٔ ما")
        self.assertEqual(shop.story_fa, "با عشق از شما پذیرایی می‌کنیم")
        self.assertEqual(shop.address_fa, "")                          # custom address: left for the owner


# ---------------------------------------------------------------- more items, ingredients, the todo list and the import
import os

from django.core.management import CommandError
from django.core.management.base import OutputWrapper
from io import TextIOWrapper

from .management.commands import _persian_data as data


class IngredientTranslationTests(TestCase):
    def test_every_word_known(self):
        self.assertEqual(data.translate_ingredients("Flour, sugar, eggs, butter, chocolate"), "آرد، شکر، تخم‌مرغ، کره، شکلات")
        self.assertEqual(data.translate_ingredients("Milk and Honey"), "شیر، عسل")

    def test_one_unknown_word_means_nothing_is_written(self):
        self.assertIsNone(data.translate_ingredients("Flour, dragonfruit"))
        self.assertIsNone(data.translate_ingredients(""))

    def test_console_that_cannot_show_persian_does_not_crash(self):
        class FakeCommand:
            stdout = OutputWrapper(TextIOWrapper(BytesIO(), encoding="ascii"))
        data.say(FakeCommand(), "نام: کیک")             # would raise UnicodeEncodeError without the fallback


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class NewItemsWorkflowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.snacks = Category.objects.create(name="Snacks", slug="snacks", description="Fresh every day", image=photo())
        self.odd = Category.objects.create(name="Chef's corner", slug="chefs-corner", image=photo())
        mk = lambda name, ing: Product.objects.create(category=self.snacks, name=name, ingredients=ing, price="5", image=photo())
        self.brownie = mk("Brownie", "Flour, sugar, eggs, butter, chocolate")
        self.croissant = mk("Croissant", "Butter, flour, secret spice")       # one unknown ingredient word
        self.special = mk("Grandma's special", "Family recipe")                # not a known item

    def run_cmd(self, name, *args):
        out = StringIO()
        call_command(name, *args, stdout=out)
        return out.getvalue()

    def test_common_items_and_their_ingredients_are_recognised(self):
        self.run_cmd("fill_persian")
        for o in (self.snacks, self.brownie):
            o.refresh_from_db()
        self.assertEqual(self.snacks.name_fa, "اسنک")
        self.assertEqual(self.snacks.description_fa, "هر روز تازه")
        self.assertEqual((self.brownie.name_fa, self.brownie.ingredients_fa), ("براونی", "آرد، شکر، تخم‌مرغ، کره، شکلات"))

    def test_an_unknown_ingredient_word_fills_the_name_only(self):
        text = self.run_cmd("fill_persian")
        self.croissant.refresh_from_db()
        self.assertEqual(self.croissant.name_fa, "کروسان")
        self.assertEqual(self.croissant.ingredients_fa, "")
        self.assertIn("need a translator", text)
        self.assertIn("Croissant", text)

    def test_descriptions_are_never_guessed(self):
        Category.objects.filter(pk=self.odd.pk).update(description="Whatever the chef feels like")
        self.run_cmd("fill_persian")
        self.odd.refresh_from_db()
        self.assertEqual(self.odd.description_fa, "")

    def test_todo_list_contains_only_what_is_missing_and_shows_the_english(self):
        self.run_cmd("fill_persian")
        path = os.path.join(tempfile.mkdtemp(), "todo.txt")
        text = self.run_cmd("persian_todo", "--file", path)
        self.assertIn("still need Persian text", text)
        body = open(path, encoding="utf-8-sig").read()
        self.assertIn("product | Croissant | کروسان |", body)            # name done, ingredients still empty
        self.assertIn("product | Grandma's special |  |", body)
        self.assertIn("English ingredients: Family recipe", body)
        self.assertNotIn("product | Brownie", body)                         # fully translated: not listed
        self.assertIn("category | Chef's corner", body)

    def write_file(self, content, bom=False):
        path = os.path.join(tempfile.mkdtemp(), "persian_menu.txt")
        with open(path, "w", encoding="utf-8-sig" if bom else "utf-8") as f:
            f.write(content)
        return path

    def test_import_fills_items_matched_by_english_name(self):
        path = self.write_file(
            "# a note\n\n"
            "product | grandma's SPECIAL | ویژهٔ مادربزرگ | دستور خانوادگی\n"
            "category | Chef's corner | گوشهٔ سرآشپز |\n"
            "shop | story | با عشق\n", bom=True)
        text = self.run_cmd("import_persian", path)
        self.special.refresh_from_db()
        self.odd.refresh_from_db()
        self.assertEqual((self.special.name_fa, self.special.ingredients_fa), ("ویژهٔ مادربزرگ", "دستور خانوادگی"))
        self.assertEqual(self.odd.name_fa, "گوشهٔ سرآشپز")
        self.assertEqual(ShopInfo.load().story_fa, "با عشق")
        self.assertIn("for 3 item(s)", text)

    def test_import_reports_unknown_and_broken_lines_and_keeps_going(self):
        path = self.write_file("product | No such item | الف | ب\nthis line is wrong\nproduct | Brownie | براونی | آرد\n")
        text = self.run_cmd("import_persian", path)
        self.assertIn("no product named “No such item”", text)
        self.assertIn("line 2: not understood", text)
        self.brownie.refresh_from_db()
        self.assertEqual(self.brownie.name_fa, "براونی")

    def test_import_dry_run_and_overwrite_rules(self):
        path = self.write_file("product | Brownie | براونی | آرد\n")
        self.run_cmd("import_persian", path, "--dry-run")
        self.brownie.refresh_from_db()
        self.assertEqual(self.brownie.name_fa, "")
        self.run_cmd("import_persian", path)
        other = self.write_file("product | Brownie | براونی جدید |\n")
        self.run_cmd("import_persian", other)                    # existing Persian text is kept...
        self.brownie.refresh_from_db()
        self.assertEqual(self.brownie.name_fa, "براونی")
        self.run_cmd("import_persian", other, "--overwrite")    # ...unless asked to replace it
        self.brownie.refresh_from_db()
        self.assertEqual((self.brownie.name_fa, self.brownie.ingredients_fa), ("براونی جدید", "آرد"))   # an empty part never erases

    def test_import_missing_file_gives_a_clear_error(self):
        with self.assertRaises(CommandError):
            call_command("import_persian", "no_such_file.txt")
