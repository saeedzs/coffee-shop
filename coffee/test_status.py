from datetime import datetime
from unittest.mock import patch

from django.test import TestCase

from .models import ShopInfo


class StatusTextTests(TestCase):
    """Default hours 09:00-23:00. 2026-10-20 is a Tuesday, 2026-10-25 a Sunday."""

    def text_at(self, shop, day, hour, minute=0):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, day, hour, minute)):
            return shop.next_opening_text

    def test_opens_later_today_when_it_is_still_early(self):
        self.assertEqual(self.text_at(ShopInfo(), 20, 7), "Opens today at 9:00 AM")

    def test_opens_tomorrow_after_closing_time(self):
        self.assertEqual(self.text_at(ShopInfo(), 20, 23, 30), "Opens tomorrow at 9:00 AM")

    def test_skips_closed_days_and_names_the_day(self):
        shop = ShopInfo(closed_days="2")                      # closed Wednesdays
        self.assertEqual(self.text_at(shop, 20, 23, 30), "Opens Thursday at 9:00 AM")

    def test_all_day_cafe_has_no_time(self):
        shop = ShopInfo(open_all_day=True, closed_days="6")   # closed Sundays
        self.assertEqual(self.text_at(shop, 25, 12), "Opens tomorrow")

    def test_closed_every_day_gives_nothing(self):
        self.assertEqual(self.text_at(ShopInfo(closed_days="0,1,2,3,4,5,6"), 20, 12), "")

    def test_open_until_text(self):
        self.assertEqual(ShopInfo().open_until_text, "Open until 11:00 PM")
        self.assertEqual(ShopInfo(open_all_day=True).open_until_text, "Open 24 hours")
