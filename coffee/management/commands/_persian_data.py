# -*- coding: utf-8 -*-
"""Persian words used by the fill_persian / persian_todo / import_persian commands."""
import re

# ---- categories: English name (lower case) -> Persian name ----
CATEGORIES = {
    "hot-drinks": "نوشیدنی‌های گرم", "hot drinks": "نوشیدنی‌های گرم", "hot beverages": "نوشیدنی‌های گرم",
    "iced-drinks": "نوشیدنی‌های سرد", "iced drinks": "نوشیدنی‌های سرد", "cold drinks": "نوشیدنی‌های سرد",
    "cakes": "کیک", "cake": "کیک", "cakes and desserts": "کیک و دسر", "desserts": "دسر",
    "tea": "چای", "teas": "چای", "coffee": "قهوه", "coffees": "قهوه",
    "herbal drinks": "دمنوش‌ها", "herbal teas": "دمنوش‌ها", "herbal tea": "دمنوش‌ها",
    "snacks": "اسنک", "snack": "اسنک", "light meals": "غذای سبک",
    "sandwiches": "ساندویچ‌ها", "salads": "سالاد", "breakfast": "صبحانه",
    "cookies": "کوکی", "pastries": "شیرینی", "bakery": "نان و شیرینی", "sweets": "شیرینی",
    "smoothies": "اسموتی", "milkshakes": "میلک‌شیک", "juices": "آبمیوه", "fresh juices": "آبمیوهٔ طبیعی",
}
DESCRIPTIONS = {
    "home-made cakes": "کیک‌های خانگی", "homemade cakes": "کیک‌های خانگی",
    "freshly baked": "تازه پخته‌شده", "fresh every day": "هر روز تازه",
}

# ---- the starter menu: exact items with their ingredients ----
_STARTER = [
    (("espresso", "esspersso", "essperso"), "اسپرسو", "اسپرسو"),
    (("white chocolate mocha", "white chocolate moca"), "موکای شکلات سفید", "شکلات سفید"),
    (("hot chocolate",), "هات چاکلت", "شکلات، شیر"),
    (("caramel macchiato",), "کارامل ماکیاتو", "کارامل ماکیاتو: یک نوشیدنی کلاسیک"),
    (("turkish coffee",), "قهوهٔ ترک", "قهوهٔ ترک"),
    (("latte",), "لاته", "لاته"),
    (("iced mocha",), "موکای سرد", "موکای سرد"),
    (("lemonade", "lemonde"), "لیموناد", "لیموناد"),
    (("masala tea", "masala chai"), "چای ماسالا", "چای ماسالا"),
    (("black tea",), "چای سیاه", "چای لاهیجان"),
    (("green tea",), "چای سبز", "چای سبز"),
]
STARTER = {alias: (name, ing) for aliases, name, ing in _STARTER for alias in aliases}

# ---- common café items: English name (lower case) -> Persian name ----
NAMES = {
    # cakes and sweets
    "cheesecake": "چیزکیک", "basque cheesecake": "چیزکیک باسک", "new york cheesecake": "چیزکیک نیویورکی",
    "chocolate cake": "کیک شکلاتی", "carrot cake": "کیک هویج", "lemon cake": "کیک لیمو",
    "banana cake": "کیک موز", "banana bread": "نان موز", "vanilla cake": "کیک وانیلی",
    "coffee cake": "کیک قهوه", "orange cake": "کیک پرتقال", "apple cake": "کیک سیب",
    "walnut cake": "کیک گردو", "honey cake": "کیک عسل", "date cake": "کیک خرما",
    "pistachio cake": "کیک پسته", "almond cake": "کیک بادام", "strawberry cake": "کیک توت‌فرنگی",
    "red velvet": "رد ولوت", "red velvet cake": "کیک رد ولوت", "tiramisu": "تیرامیسو",
    "brownie": "براونی", "chocolate brownie": "براونی شکلاتی", "pound cake": "کیک ساده",
    "cake slice": "یک تکه کیک", "cupcake": "کاپ‌کیک", "cupcakes": "کاپ‌کیک",
    "cookie": "کوکی", "cookies": "کوکی", "chocolate chip cookie": "کوکی چیپس شکلاتی",
    "chocolate chip cookies": "کوکی چیپس شکلاتی", "oatmeal cookie": "کوکی جو دوسر",
    "muffin": "مافین", "chocolate muffin": "مافین شکلاتی", "blueberry muffin": "مافین بلوبری",
    "donut": "دونات", "doughnut": "دونات", "waffle": "وافل", "pancake": "پنکیک", "pancakes": "پنکیک",
    "macaron": "ماکارون", "macarons": "ماکارون", "eclair": "اکلر", "profiterole": "پروفیترول",
    "cinnamon roll": "رول دارچین", "ice cream": "بستنی", "affogato": "آفوگاتو",
    # bakery and snacks
    "croissant": "کروسان", "chocolate croissant": "کروسان شکلاتی", "almond croissant": "کروسان بادام",
    "cheese croissant": "کروسان پنیر", "bagel": "بیگل", "granola": "گرانولا", "yogurt": "ماست",
    "fruit salad": "سالاد میوه", "french fries": "سیب‌زمینی سرخ‌کرده", "fries": "سیب‌زمینی سرخ‌کرده",
    "sandwich": "ساندویچ", "chicken sandwich": "ساندویچ مرغ", "cheese sandwich": "ساندویچ پنیر",
    "tuna sandwich": "ساندویچ تن ماهی", "club sandwich": "کلاب ساندویچ", "panini": "پانینی",
    "toast": "تست", "cheese toast": "تست پنیر", "salad": "سالاد", "caesar salad": "سالاد سزار",
    "pizza": "پیتزا", "pizza slice": "اسلایس پیتزا",
    # drinks
    "cappuccino": "کاپوچینو", "americano": "آمریکانو", "flat white": "فلت وایت", "macchiato": "ماکیاتو",
    "mocha": "موکا", "cortado": "کورتادو", "cold brew": "کلد برو", "iced latte": "لاته سرد",
    "iced coffee": "قهوهٔ سرد", "iced americano": "آمریکانو سرد", "frappe": "فراپه",
    "milkshake": "میلک‌شیک", "hot milk": "شیر داغ", "herbal tea": "دمنوش", "chamomile tea": "دمنوش بابونه",
    "mint tea": "چای نعناع", "earl grey": "چای ارل گری", "jasmine tea": "چای یاسمن",
    "orange juice": "آب پرتقال", "fresh orange juice": "آب پرتقال تازه", "mojito": "موهیتو",
    "smoothie": "اسموتی", "water": "آب", "sparkling water": "آب گازدار",
}

# ---- ingredient words: the Persian text is only written when EVERY word is known ----
GLOSSARY = {
    "milk": "شیر", "steamed milk": "شیر بخارداده", "sugar": "شکر", "brown sugar": "شکر قهوه‌ای",
    "flour": "آرد", "egg": "تخم‌مرغ", "butter": "کره", "cream": "خامه", "whipped cream": "خامه فرم‌گرفته",
    "cheese": "پنیر", "cream cheese": "پنیر خامه‌ای", "mascarpone": "ماسکارپونه", "mozzarella": "موزارلا",
    "parmesan": "پارمزان", "chocolate": "شکلات", "dark chocolate": "شکلات تلخ", "milk chocolate": "شکلات شیری",
    "white chocolate": "شکلات سفید", "cocoa": "کاکائو", "vanilla": "وانیل", "cinnamon": "دارچین",
    "honey": "عسل", "nuts": "آجیل", "almond": "بادام", "walnut": "گردو", "pistachio": "پسته",
    "hazelnut": "فندق", "peanut": "بادام‌زمینی", "coffee": "قهوه", "espresso": "اسپرسو",
    "caramel": "کارامل", "lemon": "لیمو", "orange": "پرتقال", "apple": "سیب", "banana": "موز",
    "strawberry": "توت‌فرنگی", "blueberry": "بلوبری", "carrot": "هویج", "yogurt": "ماست",
    "oats": "جو دوسر", "raisin": "کشمش", "date": "خرما", "ice": "یخ", "water": "آب", "tea": "چای",
    "green tea": "چای سبز", "black tea": "چای سیاه", "mint": "نعناع", "cardamom": "هل",
    "saffron": "زعفران", "ginger": "زنجبیل", "chicken": "مرغ", "tuna": "تن ماهی", "tomato": "گوجه‌فرنگی",
    "lettuce": "کاهو", "cucumber": "خیار", "olive": "زیتون", "bread": "نان", "ham": "ژامبون",
    "salt": "نمک", "yeast": "مخمر", "baking powder": "بیکینگ پودر", "oil": "روغن",
    "olive oil": "روغن زیتون", "potato": "سیب‌زمینی", "mushroom": "قارچ", "spinach": "اسفناج",
    "pesto": "پستو", "sausage": "سوسیس", "jam": "مربا", "syrup": "شربت", "coconut": "نارگیل",
}
_SPLIT = re.compile(r"\s*(?:,|;|/|&|\+|\band\b)\s*", re.I)


def translate_ingredients(text):
    """'Flour, sugar, eggs' -> 'آرد، شکر، تخم‌مرغ'. Returns None if any word is not in the
    glossary, so a wrong guess is never written (ingredients matter for allergies)."""
    parts = [p.strip(" .").lower() for p in _SPLIT.split(text or "") if p.strip(" .")]
    result = []
    for p in parts:
        fa = GLOSSARY.get(p)
        if not fa and p.endswith("es"):
            fa = GLOSSARY.get(p[:-2])
        if not fa and p.endswith("s"):
            fa = GLOSSARY.get(p[:-1])
        if not fa:
            return None
        result.append(fa)
    return "، ".join(dict.fromkeys(result)) if result else None


# ---- the shop details of the starter site: only filled when the English text is exactly this ----
SHOP = {
    "name": {"our café": "کافهٔ ما", "our cafe": "کافهٔ ما"},
    "address": {"tehran province, tehran, parsiya, iran": "استان تهران، تهران، پارسیا، ایران"},
    "story": {"we serve you with love": "با عشق از شما پذیرایی می‌کنیم"},
}


def say(command, text, style=None):
    """Print, even on a Windows console that cannot show Persian letters."""
    try:
        command.stdout.write(style(text) if style else text)
    except UnicodeEncodeError:
        safe = text.encode("ascii", "backslashreplace").decode("ascii")
        command.stdout.write(style(safe) if style else safe)


def norm(text):
    return " ".join((text or "").lower().split())
