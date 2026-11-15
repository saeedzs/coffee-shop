[README.md](https://github.com/user-attachments/files/34872505/README.md)
# ☕ Café Menu

A bilingual (**English / Persian**) menu website for a small café, built with Django. Customers scan a QR code or open the link, browse the menu, and see at a glance whether the café is open. The owner manages everything from the Django admin: no code, no database tools.

> Online ordering and payments are left out on purpose: this is a fast, calm, mobile-first menu, not a shop.

<!-- Replace with your own screenshots (see the "Screenshots" section) -->
<!-- ![Welcome page](docs/screenshots/welcome.png) -->

## Features

**For customers**

- Welcome page with a full-screen photo and a hanging **OPEN / CLOSED** door sign that shows today's hours ("Opens tomorrow at 9:00 AM")
- Menu by category, with photo, name, ingredients and **two sizes and prices** (medium / large)
- **Product pop-up** with the whole photo, next / previous, swipe, keyboard arrows, a working Back button, and a shareable link for every item
- **Dietary and allergen labels** (vegan, caffeine-free, contains nuts / dairy), diet filters, and "sold out today" items that stay visible but greyed out
- **Barista's pick** of the day, **New / Popular / Seasonal** badges, and a small hanging **seasonal tag** for announcements
- Search across names, ingredients and categories (in both languages)
- About page: story, hours, address, phone, social links, embedded map, and quick call / directions buttons
- The whole site switches to a **dark evening look when the café is closed**, and back to light when it opens
- **English and Persian versions** with a language button; the Persian version is fully right-to-left with Persian digits, 24-hour times, Persian-calendar dates and the currency shown after the amount (e.g. `۸۵٬۰۰۰ تومان`)

**For the owner (Django admin)**

- Categories, products, photos (automatically resized and converted to WebP), prices, labels, badges
- One screen for the café details: name, story, address, phone, links, map, **opening hours** (open time, close time, open all day, closed days, hours that run past midnight)
- Daily barista pick (or automatic rotation), seasonal tags with start / end dates and an optional link
- Bulk "mark as sold out", photo thumbnails, and a **Persian ✓ column** that shows which items still need a Persian translation

**Under the hood**

- Plain Django templates with vanilla CSS and JavaScript: no framework, no build step, no CDN
- Self-hosted fonts (Nunito, Playfair Display, Vazirmatn) and optimized WebP images; lazy-loaded photos
- Accessibility: skip link, keyboard focus styles, reduced-motion support, checked text contrast
- Social sharing tags (Open Graph), `hreflang` alternates, favicon
- A test suite covering the pages, opening-hours logic, translations, commands and layout rules

## Screenshots

Add pictures to `docs/screenshots/` and link them here, for example:

| Welcome (open) | Menu | Product pop-up | Persian (right-to-left) |
|---|---|---|---|
| `welcome.png` | `menu.png` | `popup.png` | `persian.png` |

## Quick start

Requirements: **Python 3.12 or newer**.

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. It redirects to `/en/` or `/fa/` depending on the browser's language. The admin is at <http://127.0.0.1:8000/admin/> (always in English).

> The repository does not contain a database or photos. You start with an empty menu and add your own.

## First steps after installing

1. In the admin, open **Shop info** and fill in the café name, address, phone, links and **opening hours**. Set the Persian fields too.
2. Add **Categories**, then **Products** with photos. Write names and ingredients in English in the main fields and in Persian in the **"Persian version (فارسی)"** section of the same form.
3. Tick the dietary labels honestly: the site only shows what is ticked.
4. Optional: add a **Daily pick** and a **Seasonal tag**.
5. Change the welcome picture (see [Commands](#management-commands)).

## Configuration

Edit `mycoffeeshop/settings.py`:

| Setting | What it does |
|---|---|
| `TIME_ZONE` | The café's time zone. The open / closed status and the day / night look follow it. |
| `LANGUAGE_CODE` | Language for visitors whose browser doesn't say (`'en'` by default; use `'fa'` for Persian). |
| `CURRENCY_SYMBOL` | Currency on the English pages, for example `'$'` or `'Toman'`. |
| `CURRENCY_SYMBOL_BEFORE` | `True`: `$7.99`. `False`: `85,000 Toman`. |
| `CURRENCY_SYMBOL_FA` | Currency word on the Persian pages, for example `'تومان'`. |

Environment variables (needed when you publish the site, harmless locally):

| Variable | Meaning |
|---|---|
| `DJANGO_DEBUG` | `1` (default) for development, `0` in production. |
| `DJANGO_SECRET_KEY` | A long random secret. **Required** when `DJANGO_DEBUG=0`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domains, e.g. `yourcafe.com,www.yourcafe.com`. |
| `DJANGO_CSRF_ORIGINS` | Comma-separated trusted origins, e.g. `https://yourcafe.com`. |

## Languages

The public site lives under `/en/…` and `/fa/…`. Interface words are translated in `coffee/locale/fa/`. Anything the owner types (names, ingredients, story, address, seasonal tags…) has an optional Persian field; if it is empty, the English text is shown instead, so nothing is ever blank.

To translate new menu items quickly:

```bash
python manage.py fill_persian      # translates the items it recognises
python manage.py persian_todo      # writes persian_todo.txt with everything still missing
# get that file translated, save the answer as persian_menu.txt (UTF-8), then:
python manage.py import_persian persian_menu.txt
```

If you change interface text in a template, update `coffee/locale/fa/LC_MESSAGES/django.po` and run `python manage.py compilemessages` (needs [GNU gettext](https://www.gnu.org/software/gettext/)). The compiled `django.mo` is committed, so a normal install needs no extra tools.

## Management commands

| Command | Purpose |
|---|---|
| `python manage.py set_hero "path\to\photo.jpg"` | Change the welcome page background (add `--welcome-only` to leave the other pages alone). Makes the large and the phone-sized WebP files for you. |
| `python manage.py optimize_media` | Shrink photos uploaded earlier (`--dry-run` to preview). New uploads are optimized automatically. |
| `python manage.py fill_persian` | Fill in Persian names and ingredients for recognised items (`--dry-run`, `--overwrite`). |
| `python manage.py persian_todo` | List everything that still has no Persian text. |
| `python manage.py import_persian file.txt` | Load Persian names and ingredients from a text file. |

## Tests

```bash
python manage.py test coffee
```

## Project structure

```
.
├── manage.py
├── requirements.txt
├── mycoffeeshop/              # project settings and URLs
└── coffee/                    # the café app
    ├── models.py              # categories, products, shop info, daily picks, seasonal tags
    ├── views.py, urls.py, admin.py
    ├── i18n.py                # Persian digits, Persian-calendar dates, currency formatting
    ├── images.py              # photo resizing and WebP conversion
    ├── templatetags/          # {{ item|tr:"name" }}, {% switch_url 'fa' %} ...
    ├── templates/coffee/      # pages and small partials
    ├── static/                # css, js, img (hero pictures, icons) and fonts
    ├── locale/fa/             # Persian interface translations (.po and compiled .mo)
    ├── management/commands/   # the commands above
    └── test_*.py, tests.py    # automated tests
```

`media/` (uploaded photos) and `db.sqlite3` are created at run time and are not part of the repository.

## Deploying

Before going live:

1. Set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` (see above). With debug off, HTTPS redirects and secure cookies are switched on automatically.
2. Run `python manage.py collectstatic` (files are gathered into `staticfiles/`).
3. Let your web server serve `/static/` and `/media/`. Django does not serve uploaded photos when debug is off.
4. Use HTTPS, and keep regular backups of `db.sqlite3` and `media/`: together they are the café's whole menu.

See Django's [deployment checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/) for the rest.

## Credits and licenses

- **Code:** [MIT](LICENSE) <!-- add a LICENSE file, or change this line to the license you prefer -->
- **Fonts:** Nunito, Playfair Display and Vazirmatn, all under the SIL Open Font License 1.1 (license texts are in `coffee/static/fonts/`).
- **Photos and logos:** the pictures you upload belong to you or their photographers, so make sure you may use them. The Instagram logo is a trademark of Meta and is used only to link to a profile.

---

## توضیح کوتاه (فارسی)

وب‌سایت منوی یک کافه، ساخته‌شده با Django، در دو نسخهٔ جداگانهٔ انگلیسی و فارسی (راست‌به‌چپ). مشتری منوی دسته‌بندی‌شده را با عکس، مواد و قیمت دو سایز می‌بیند، می‌تواند جستجو کند، برچسب‌های حساسیت غذایی را ببیند و بداند کافه همین حالا باز است یا نه. صاحب کافه همهٔ بخش‌ها را از پنل مدیریت (`/admin/`) تنظیم می‌کند. برای نصب، بخش «Quick start» را ببینید.
