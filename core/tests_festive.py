"""Checks for the automatic festival dressing.

Run:  python manage.py test core
"""
import datetime as dt

from django.test import SimpleTestCase

from core.festive import (
    FESTIVALS, LUNAR_DATES, resolve, theme_for_date, theme_payload,
)


class FestivalCalendarTests(SimpleTestCase):
    def test_fixed_dates_dress_the_shop(self):
        self.assertEqual(theme_for_date(dt.date(2026, 12, 25)), "christmas")
        self.assertEqual(theme_for_date(dt.date(2026, 12, 18)), "christmas")  # lead-up
        self.assertEqual(theme_for_date(dt.date(2026, 2, 14)), "valentine")

    def test_new_year_window_survives_the_year_boundary(self):
        self.assertEqual(theme_for_date(dt.date(2026, 12, 30)), "newyear")
        self.assertEqual(theme_for_date(dt.date(2027, 1, 2)), "newyear")

    def test_lunar_dates_come_from_the_table(self):
        for year, festivals in LUNAR_DATES.items():
            for slug, (month, day) in festivals.items():
                self.assertEqual(
                    theme_for_date(dt.date(year, month, day)), slug,
                    f"{slug} {year} should dress the shop on its own main day",
                )

    def test_ordinary_days_are_left_alone(self):
        self.assertIsNone(theme_for_date(dt.date(2026, 6, 17)))
        self.assertIsNone(theme_for_date(dt.date(2026, 9, 2)))

    def test_overlapping_windows_pick_the_nearer_festival(self):
        # Christmas closes 26 Dec, New Year opens 29 Dec — the day between
        # belongs to whichever main day is closer.
        self.assertEqual(theme_for_date(dt.date(2026, 12, 24)), "christmas")
        self.assertEqual(theme_for_date(dt.date(2026, 12, 31)), "newyear")

    def test_every_slug_has_copy(self):
        for year in LUNAR_DATES:
            for slug in LUNAR_DATES[year]:
                self.assertIn(slug, FESTIVALS, f"{slug} has no label/announcement")
        for slug, data in FESTIVALS.items():
            self.assertTrue(data["label"] and data["note"], f"{slug} is missing copy")

    def test_lunar_table_still_covers_the_road_ahead(self):
        """Fails a year before the table runs dry — that is the reminder to
        add next year's panchang dates in core/festive.py."""
        next_year = dt.date.today().year + 1
        self.assertIn(
            next_year, LUNAR_DATES,
            f"LUNAR_DATES has no entry for {next_year}: add Holi/Eid/Akshaya/"
            f"Rakhi/Diwali dates for {next_year} in core/festive.py",
        )


class ThemeOverrideTests(SimpleTestCase):
    def test_payload_shape(self):
        payload = theme_payload("diwali")
        self.assertEqual(payload["slug"], "diwali")
        self.assertTrue(payload["note"])

    def test_unknown_slug_is_ignored(self):
        self.assertIsNone(theme_payload("not-a-festival"))

    def test_query_param_forces_and_clears(self):
        class FakeRequest:
            def __init__(self, theme=None):
                self.GET = {"theme": theme} if theme else {}
                self.session = {}

        req = FakeRequest("diwali")
        self.assertEqual(resolve(req, today=dt.date(2026, 6, 17))["slug"], "diwali")

        req.GET = {"theme": "off"}
        self.assertIsNone(resolve(req, today=dt.date(2026, 12, 25)))

        req.GET = {"theme": "auto"}
        self.assertEqual(resolve(req, today=dt.date(2026, 12, 25))["slug"], "christmas")
