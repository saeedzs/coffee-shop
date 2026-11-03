# -*- coding: utf-8 -*-
"""Load Persian text from a plain text file.

    python manage.py import_persian persian_menu.txt --dry-run
    python manage.py import_persian persian_menu.txt

One item per line, parts separated by |  (empty parts are skipped, # starts a note):

    category | Snacks | اسنک | توضیح (optional)
    product  | Brownie | براونی | آرد، شکر، تخم‌مرغ، کره، شکلات
    shop     | name | کافهٔ ما

Items are matched by their English name (capitals do not matter).
"""
from django.core.management.base import BaseCommand, CommandError

from coffee.models import Category, Product, ShopInfo

from ._persian_data import norm, say


class Command(BaseCommand):
    help = "Load Persian names and ingredients from a text file."

    def add_arguments(self, parser):
        parser.add_argument("file", help="The text file, saved as UTF-8.")
        parser.add_argument("--dry-run", action="store_true", help="Only show what would change.")
        parser.add_argument("--overwrite", action="store_true", help="Also replace Persian text that is already there.")

    def handle(self, *args, **opts):
        try:
            with open(opts["file"], encoding="utf-8-sig") as f:
                raw_lines = f.read().splitlines()
        except FileNotFoundError:
            raise CommandError(f"File not found: {opts['file']}")

        self.dry, self.overwrite = opts["dry_run"], opts["overwrite"]
        applied, problems = 0, []

        for number, raw in enumerate(raw_lines, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3 or parts[0].lower() not in ("category", "product", "shop"):
                problems.append(f"line {number}: not understood: {line[:60]}")
                continue
            kind, english = parts[0].lower(), parts[1]
            fa_name = parts[2]
            fa_more = parts[3] if len(parts) > 3 else ""

            if kind == "shop":
                field = norm(english)
                if field not in ("name", "address", "story"):
                    problems.append(f"line {number}: shop field must be name, address or story")
                    continue
                applied += self.apply(ShopInfo, [ShopInfo.load()], {f"{field}_fa": fa_name}, "Shop " + field)
                continue

            model, extra = (Category, "description_fa") if kind == "category" else (Product, "ingredients_fa")
            matches = [o for o in model.objects.all() if norm(o.name) == norm(english)]
            if not matches:
                problems.append(f"line {number}: no {kind} named “{english}” (check the English name)")
                continue
            applied += self.apply(model, matches, {"name_fa": fa_name, extra: fa_more}, english)

        verb = "would be written" if self.dry else "written"
        say(self, f"Done: Persian text {verb} for {applied} item(s).", self.style.SUCCESS)
        if problems:
            say(self, "Needs a look:", self.style.WARNING)
            for p in problems:
                say(self, f"  - {p}")

    def apply(self, model, objects, values, label):
        done = 0
        for obj in objects:
            new = {f: v for f, v in values.items() if v and (self.overwrite or not getattr(obj, f)) and getattr(obj, f) != v}
            if not new:
                continue
            done += 1
            say(self, f"  {label}:  " + "  |  ".join(f"{f} = {v}" for f, v in new.items()))
            if not self.dry:
                model.objects.filter(pk=obj.pk).update(**new)
        return done
