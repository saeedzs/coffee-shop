"""Image helpers: shrink and convert uploaded photos so pages load fast."""
import os
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def optimize_image(upload, max_side=1000, quality=80):
    """Return (filename, ContentFile): the image shrunk so neither side exceeds
    max_side pixels, and converted to WebP. Never enlarges small images."""
    img = Image.open(upload)
    img = ImageOps.exif_transpose(img)              # fixes sideways phone photos
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="WEBP", quality=quality, method=6)
    name = os.path.splitext(os.path.basename(upload.name))[0] + ".webp"
    return name, ContentFile(buf.getvalue())


def optimize_on_upload(field_file, max_side=1000):
    """Optimize a file only when it was just uploaded (not yet saved to storage),
    so re-saving a record never recompresses the same photo."""
    if field_file and not field_file._committed:
        name, data = optimize_image(field_file, max_side=max_side)
        field_file.save(name, data, save=False)
