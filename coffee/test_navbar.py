from django.test import TestCase


class NavbarScriptTests(TestCase):
    def test_navbar_script_is_loaded_on_pages_that_have_a_navbar(self):
        for url in ["/menu/", "/about/", "/search/"]:
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), "js/navbar.js")
