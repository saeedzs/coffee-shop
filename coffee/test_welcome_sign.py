from datetime import datetime
from unittest.mock import patch

from django.test import TestCase


class WelcomeDoorSignTests(TestCase):
    """Default hours 09:00-23:00. 2026-10-20 is a Tuesday."""

    def welcome_at(self, hour):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, 20, hour, 0)):
            return self.client.get("/")

    def test_open_sign_says_until_when(self):
        r = self.welcome_at(12)
        self.assertContains(r, 'class="door-sign open"')
        self.assertContains(r, "<b>OPEN</b>")
        self.assertContains(r, "until 11:00 PM")

    def test_closed_sign_says_when_it_opens(self):
        r = self.welcome_at(2)
        self.assertContains(r, 'class="door-sign closed"')
        self.assertContains(r, "<b>CLOSED</b>")
        self.assertContains(r, "Opens today at 9:00 AM")

    def test_sign_leads_to_the_about_page(self):
        self.assertContains(self.welcome_at(12), 'href="/about/"')

    def test_the_old_status_pill_is_gone_from_the_welcome_page(self):
        self.assertNotContains(self.welcome_at(12), 'class="status')

    def test_sign_is_only_on_the_welcome_page(self):
        with patch("coffee.models.timezone.localtime", return_value=datetime(2026, 10, 20, 12, 0)):
            for url in ["/menu/", "/about/"]:
                self.assertNotContains(self.client.get(url), "door-sign")
