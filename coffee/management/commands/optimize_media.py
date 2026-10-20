"""One-time cleanup: shrink the photos that were uploaded before automatic
optimization existed.

    python manage.py optimize_media --dry-run     (just report, change nothing)
    python manage.py optimize_media               (do it)
"""
from django.core.management.base import BaseCommand
from PIL import Image

from coffee.images import optimize_image
from coffee.models import Category, Product, ShopInfo

MAX_SIDE = 1000
MAX_KB = 150


class Command(BaseCommand):
    help = "Convert existing oversized or non-WebP photos to optimized WebP files."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only report what would change.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        saved_total = changed = 0

        targets = [(Category, "image"), (Product, "image"), (ShopInfo, "photo")]
        for model, field in targets:
            for obj in model.objects.all():
                f = getattr(obj, field)
                if not f:
                    continue
                try:
                    size_kb = f.size / 1024
                    with Image.open(f.path) as im:
                        width, height = im.size
                except (FileNotFoundError, OSError, ValueError):
                    self.stdout.write(self.style.WARNING(f"  skipped (file missing/unreadable): {obj}"))
                    continue

                needs = (not f.name.lower().endswith(".webp")) or max(width, height) > MAX_SIDE or size_kb > MAX_KB
                if not needs:
                    continue

                label = f"{model.__name__}: {obj}  ({width}x{height}, {size_kb:.0f} KB)"
                if dry:
                    self.stdout.write(f"  would optimize  {label}")
                    continue

                old_name = f.name
                new_name, data = optimize_image(f, max_side=MAX_SIDE)
                if max(width, height) <= MAX_SIDE and data.size >= size_kb * 1024 * 0.9:
                    self.stdout.write(f"  kept as is (already compact)  {label}")
                    continue
                f.save(new_name, data, save=False)          # stores the new file
                obj.save(update_fields=[field])              # points the record at it
                f.storage.delete(old_name)                   # removes the heavy original
                new_kb = getattr(obj, field).size / 1024
                saved_total += size_kb - new_kb
                changed += 1
                self.stdout.write(f"  optimized  {label}  ->  {new_kb:.0f} KB")

        if dry:
            self.stdout.write("Dry run only, nothing changed.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Done: {changed} photo(s) optimized, about {saved_total/1024:.1f} MB saved."))
