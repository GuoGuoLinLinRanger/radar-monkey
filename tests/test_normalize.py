"""Run: python -m unittest discover tests"""
import unittest

from radar import normalize as N
from radar.sources import job_id, new_job


class Countries(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(N.countries_of(["Waterloo, ON"]), ["CA"])
        self.assertEqual(N.countries_of(["San Jose, CA"]), ["US"])  # CA = California
        self.assertEqual(N.countries_of(["NYC", "Toronto, ON, Canada"]), ["CA", "US"])
        self.assertEqual(N.countries_of(["London, UK"]), ["Other"])
        self.assertEqual(N.countries_of(["Remote"]), ["US"])


class Pay(unittest.TestCase):
    def test_hourly(self):
        p = N.pay_from_text("The hourly pay range is $42 - $55 USD per hour.")
        self.assertEqual((p["hourly_min"], p["hourly_max"]), (42, 55))

    def test_salary_k(self):
        self.assertEqual(N.pay_from_text("Salary $95k-$120k")["annual_max"], 120000)

    def test_cad(self):
        self.assertEqual(N.pay_from_text("Compensation: CA$30-35/hr")["currency"], "CAD")

    def test_not_pay(self):
        self.assertEqual(N.pay_from_text("We raised $50M in Series B"), {})


class Misc(unittest.TestCase):
    def test_ats(self):
        self.assertEqual(N.ats_of("https://acme.wd5.myworkdayjobs.com/x"), "Workday")
        self.assertEqual(N.ats_of("https://job-boards.greenhouse.io/acme/jobs/1"), "Greenhouse")

    def test_flags(self):
        self.assertIn("senior", N.title_flags("Senior Software Engineer"))
        self.assertIn("coop", N.title_flags("Software Co-op"))

    def test_sponsorship(self):
        self.assertEqual(N.sponsorship_of("", "Must be a U.S. citizen"), "citizen")
        self.assertEqual(N.sponsorship_of("", "We are unable to sponsor visas"), "no")

    def test_id_stable_across_sources(self):
        a = job_id("Stripe", "Software Engineer Intern (Summer 2027)", "intern")
        b = job_id("stripe", "Software Engineer Intern", "intern")
        self.assertEqual(a, b)

    def test_new_job(self):
        j = new_job(source="simplify", native_id="1", kind="intern", title="SWE Intern - Summer 2027",
                    company="Acme", locations=["Toronto, ON"], url="https://x.com/j?utm_source=a",
                    posted_at="2026-10-01T00:00:00+00:00")
        self.assertEqual(j["countries"], ["CA"])
        self.assertEqual(j["terms"], ["Summer 2027"])
        self.assertNotIn("utm", j["url"])


if __name__ == "__main__":
    unittest.main()
