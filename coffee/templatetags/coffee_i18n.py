from django import template
from django.urls import reverse, translate_url
from django.utils import translation

from .. import i18n

register = template.Library()

# {{ product|tr:"name" }}  -> the Persian name on Persian pages (English if not written yet)
register.filter("tr", i18n.localized)
# {{ shop.phone|digits }}  -> ۰۹۱۲... on Persian pages
register.filter("digits", i18n.digits)
# {{ shop.open_time|clock }} -> 9:00 AM / ۰۹:۰۰
register.filter("clock", i18n.clock)
# {{ product.price|money }}  -> $7.99 / ۷٫۹۹ $
register.filter("money", i18n.money)


@register.simple_tag(takes_context=True)
def switch_url(context, lang):
    """Address of the page you are on, in another language ('en' or 'fa')."""
    request = context["request"]
    current = request.get_full_path()
    url = translate_url(current, lang)
    if url == current:                      # e.g. the 404 page: send them to the home page
        with translation.override(lang):
            return reverse("welcome")
    return url
