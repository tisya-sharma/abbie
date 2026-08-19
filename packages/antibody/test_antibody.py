"""Unit tests for the placeholder catalog tools. Run without an API key:

    python3 -m unittest packages.antibody.test_antibody
"""

import subprocess
import sys
import unittest
from pathlib import Path

from packages.antibody import (
    MAX_SEARCH_LIMIT,
    PLACEHOLDER_NOTICE,
    Application,
    Species,
    get_antibody,
    search_antibodies,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# The transports the tool library may never acquire. The widget calls it in
# process and the MCP server and the Slack app are meant to stay thin adapters
# over the same functions, which stops being true the moment one of these
# appears in an import.
FORBIDDEN_IMPORTS = ("fastapi", "fastmcp", "starlette", "openai", "slack_bolt")


class TransportFreedomTests(unittest.TestCase):
    def test_the_library_imports_no_transport(self):
        """Checked in a subprocess, since this one has already imported plenty.

        Written as a test rather than left to convention because the constraint
        is cheap while the library is small and a rewrite afterwards.
        """
        script = (
            "import sys; import packages.antibody; "
            f"print(','.join(m for m in {FORBIDDEN_IMPORTS!r} if m in sys.modules))"
        )
        found = subprocess.run(
            [sys.executable, "-c", script],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(found, "")


class GetAntibodyTests(unittest.TestCase):
    def test_a_known_identifier_returns_its_record(self):
        lookup = get_antibody("PLACEHOLDER-0001")
        self.assertTrue(lookup.found)
        self.assertEqual(lookup.record.target, "EXAMPLEGENE1")

    def test_matching_ignores_case_and_surrounding_space(self):
        self.assertTrue(get_antibody("  placeholder-0001 ").found)

    def test_an_unknown_identifier_is_a_structured_miss(self):
        lookup = get_antibody("AB-88231")
        self.assertFalse(lookup.found)
        self.assertIsNone(lookup.record)

    def test_every_row_carries_provenance(self):
        record = get_antibody("PLACEHOLDER-0001").record
        self.assertTrue(record.provenance.source_url)
        self.assertTrue(record.provenance.manifest_version)
        self.assertTrue(record.provenance.built_at)

    def test_the_placeholder_notice_travels_with_the_row(self):
        """The model reads this payload, so the warning has to be in it."""
        record = get_antibody("PLACEHOLDER-0001").record
        self.assertEqual(record.notice, PLACEHOLDER_NOTICE)


class SearchAntibodiesTests(unittest.TestCase):
    def test_no_filters_lists_the_catalog(self):
        self.assertEqual(len(search_antibodies().hits), 3)

    def test_target_matching_ignores_case(self):
        hits = search_antibodies(target="examplegene1").hits
        self.assertEqual(
            {h.identifier for h in hits},
            {"PLACEHOLDER-0001", "PLACEHOLDER-0002"},
        )

    def test_filters_intersect(self):
        hits = search_antibodies(
            target="EXAMPLEGENE1", application=Application.ELISA
        ).hits
        self.assertEqual([h.identifier for h in hits], ["PLACEHOLDER-0002"])

    def test_species_filters_on_reactivity(self):
        hits = search_antibodies(species=Species.RAT).hits
        self.assertEqual([h.identifier for h in hits], ["PLACEHOLDER-0003"])

    def test_an_unassessed_application_returns_nothing_rather_than_failing(self):
        """A schema that rejects IHC cannot say that absence is not failure."""
        result = search_antibodies(application=Application.IMMUNOHISTOCHEMISTRY)
        self.assertEqual(result.hits, [])
        self.assertFalse(result.truncated)

    def test_the_limit_truncates_and_says_so(self):
        result = search_antibodies(limit=1)
        self.assertEqual(len(result.hits), 1)
        self.assertTrue(result.truncated)

    def test_an_oversized_limit_is_clamped_rather_than_rejected(self):
        self.assertEqual(len(search_antibodies(limit=MAX_SEARCH_LIMIT * 10).hits), 3)

    def test_a_nonsense_limit_still_returns_something(self):
        self.assertEqual(len(search_antibodies(limit=0).hits), 1)


if __name__ == "__main__":
    unittest.main()
