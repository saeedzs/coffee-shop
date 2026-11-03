# -*- coding: utf-8 -*-
"""Make a list of everything that still has no Persian text.

    python manage.py persian_todo                    (writes persian_todo.txt next to manage.py)
    python manage.py persian_todo --file my_list.txt

Give the file to whoever translates for you. They fill in the empty parts after the | signs,
and you load the result with:   python manage.py import_persian persian_menu.txt
"""
from django.core.management.base import BaseCommand

from coffee.models import Category, Product, ShopInfo

from ._persian_data import say

HEADER = """# Persian text still missing.
# Fill in the empty parts after the | signs, keep one item per line, and save the file as UTF-8.
# Format:   category | English name | Persian name | Persian description (optional)
#           product  | English name | Persian name | Persian ingredients
#           shop     | name / address / story | Persian text
# Lines starting with # are only notes.
"""


class Command(BaseCommand):
    help = "List every item that still has no Persian text, ready to be translated."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="persian_todo.txt", help="Where to save the list (default: persian_todo.txt).")

    def handle(self, *args, **opts):
        lines = [HEADER]
        count = 0

        cats = [c for c in Category.objects.all() if not c.name_fa or (c.description and not c.description_fa)]
        if cats:
            lines.append("\n# ---- Categories ----")
        for c in cats:
            count += 1
            lines.append(f"category | {c.name} | {c.name_fa} | {c.description_fa}")
            if c.description:
                lines.append(f"# English description: {c.description}")

        prods = [p for p in Product.objects.select_related("category") if not p.name_fa or not p.ingredients_fa]
        if prods:
            lines.append("\n# ---- Products ----")
        for p in prods:
            count += 1
            lines.append(f"product | {p.name} | {p.name_fa} | {p.ingredients_fa}")
            lines.append(f"# {p.category.name}. English ingredients: {' '.join(p.ingredients.split())}")

        shop = ShopInfo.load()
        shop_lines = [(f, getattr(shop, f)) for f in ("name", "address", "story")
                      if getattr(shop, f).strip() and not getattr(shop, f"{f}_fa")]
        if shop_lines:
            lines.append("\n# ---- Shop details ----")
        for field, english in shop_lines:
            count += 1
            lines.append(f"shop | {field} | ")
            lines.append(f"# English {field}: {' '.join(english.split())}")

        text = "\n".join(lines) + "\n"
        with open(opts["file"], "w", encoding="utf-8-sig") as f:      # -sig: Windows Notepad opens it correctly
            f.write(text)
        say(self, f"{count} item(s) still need Persian text. List saved to: {opts['file']}", self.style.SUCCESS)
        if count:
            say(self, "Send that file's contents to your translator, then load the answer with:")
            say(self, "    python manage.py import_persian persian_menu.txt")
