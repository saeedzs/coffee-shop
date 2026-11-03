# -*- coding: utf-8 -*-
"""Fill in Persian (فارسی) names and ingredients automatically, where the item is recognised.

    python manage.py fill_persian --dry-run     (show what would be written, change nothing)
    python manage.py fill_persian               (write the Persian text where it is still empty)
    python manage.py fill_persian --overwrite   (also replace Persian text that is already there)

It knows the starter menu plus many common café cakes, snacks and drinks. Anything it does not
recognise is listed and left alone; run "python manage.py persian_todo" to get a list you can
have translated and load with "python manage.py import_persian".

The Persian ingredients are only written when every ingredient word is known, so a wrong
guess never reaches your menu (ingredients matter for allergies).
"""
from django.core.management.base import BaseCommand

from coffee.models import Category, Product, ShopInfo

from ._persian_data import (CATEGORIES, DESCRIPTIONS, NAMES, SHOP, STARTER, norm, say,
                            translate_ingredients)


class Command(BaseCommand):
    help = "Fill in Persian names and ingredients for recognised items (only where still empty)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only show what would change.")
        parser.add_argument("--overwrite", action="store_true", help="Also replace Persian text that is already there.")

    def handle(self, *args, **opts):
        self.dry, self.overwrite = opts["dry_run"], opts["overwrite"]
        self.changed = 0
        self.unknown, self.partial = [], []

        for c in Category.objects.all():
            name = CATEGORIES.get(c.slug) or CATEGORIES.get(norm(c.name))
            if not name:
                self.unknown.append(f"category “{c.name}”")
                continue
            self.apply(Category, c, {"name_fa": name, "description_fa": DESCRIPTIONS.get(norm(c.description), "")}, c.name)

        for p in Product.objects.all():
            key = norm(p.name)
            if key in STARTER:
                name, ingredients = STARTER[key]
            elif key in NAMES:
                name, ingredients = NAMES[key], translate_ingredients(p.ingredients)
                if ingredients is None:
                    self.partial.append(f"{p.name}: ingredients “{p.ingredients[:50]}”")
            else:
                self.unknown.append(f"product “{p.name}”")
                continue
            self.apply(Product, p, {"name_fa": name, "ingredients_fa": ingredients or ""}, p.name)

        shop = ShopInfo.load()
        values = {}
        for field, table in SHOP.items():
            fa = table.get(norm(getattr(shop, field)))
            if fa:
                values[f"{field}_fa"] = fa
            elif getattr(shop, field).strip() and not getattr(shop, f"{field}_fa"):
                self.unknown.append(f"shop {field} “{getattr(shop, field)[:40]}”")
        if values:
            self.apply(ShopInfo, shop, values, "Shop info")

        verb = "would be written" if self.dry else "written"
        say(self, f"Done: Persian text {verb} for {self.changed} item(s).", self.style.SUCCESS)
        if self.partial:
            say(self, "Names filled, but the ingredients need a translator (unknown words):", self.style.WARNING)
            for u in self.partial:
                say(self, f"  - {u}")
        if self.unknown:
            say(self, "Not recognised, left as they are:", self.style.WARNING)
            for u in self.unknown:
                say(self, f"  - {u}")
            say(self, "Next step: python manage.py persian_todo   (makes a list you can have translated)")

    def apply(self, model, obj, values, label):
        new = {f: v for f, v in values.items() if v and (self.overwrite or not getattr(obj, f))}
        new = {f: v for f, v in new.items() if getattr(obj, f) != v}
        if not new:
            return
        self.changed += 1
        say(self, f"  {label}:  " + "  |  ".join(f"{f} = {v}" for f, v in new.items()))
        if not self.dry:
            model.objects.filter(pk=obj.pk).update(**new)
