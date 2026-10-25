from datetime import datetime
from unittest.mock import patch

from django.test import TestCase


class ThemeFollowsOpeningHoursTests(TestCase):
    """Default hours are 09:00-23:00 every day. 2026-10-20 is a Tuesday."""

    def page_at(self, hour, url="/menu/"):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, 20, hour, 0)):
            return self.client.get(url)

    def test_open_means_light_and_closed_means_dark(self):
        self.assertContains(self.page_at(12), 'data-theme="light"')
        self.assertContains(self.page_at(3), 'data-theme="dark"')

    def test_every_kind_of_page_follows_the_same_rule(self):
        for url in ["/", "/menu/", "/about/", "/search/"]:
            with self.subTest(url=url):
                self.assertContains(self.page_at(2, url), 'data-theme="dark"')
                self.assertContains(self.page_at(15, url), 'data-theme="light"')

    def test_there_is_no_theme_toggle_any_more(self):
        self.assertNotContains(self.page_at(12), "theme-toggle")
