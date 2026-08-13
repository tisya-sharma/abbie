"""Unit tests for the checklist export. Run without an API key:

    python3 -m unittest packages.export.test_export
"""

import unittest
from dataclasses import replace

from packages.corpus_loader import load_corpus
from packages.export import (
    CHECKLIST_FILENAME,
    _published_sources,
    checklist_concepts,
    render_checklist,
)

CITED = ["controls-in-validation", "application-western-blot"]


class ChecklistSelectionTests(unittest.TestCase):
    def setUp(self):
        self.concepts = load_corpus()

    def test_only_concepts_carrying_a_checklist_are_selected(self):
        selected = checklist_concepts(self.concepts, CITED + ["selectivity"])
        self.assertTrue(selected)
        self.assertNotIn("selectivity", [c.id for c in selected])

    def test_no_document_when_nothing_cited_carries_a_checklist(self):
        self.assertIsNone(
            render_checklist(self.concepts, ["selectivity"], "13 August 2026")
        )

    def test_selection_follows_corpus_order_not_citation_order(self):
        forward = checklist_concepts(self.concepts, CITED)
        reversed_ = checklist_concepts(self.concepts, list(reversed(CITED)))
        self.assertEqual([c.id for c in forward], [c.id for c in reversed_])


class FilenameTests(unittest.TestCase):
    def test_filename_carries_no_concept_id(self):
        # A filename built from concept ids would carry them out of the server
        # in Content-Disposition, which is the one thing no surface may do.
        document = render_checklist(load_corpus(), CITED, "13 August 2026")
        self.assertEqual(document.filename, CHECKLIST_FILENAME)
        for concept_id in CITED:
            self.assertNotIn(concept_id, document.filename)

    def test_filename_is_stable_across_different_selections(self):
        concepts = load_corpus()
        a = render_checklist(concepts, CITED, "13 August 2026")
        b = render_checklist(concepts, ["controls-in-validation"], "13 August 2026")
        self.assertEqual(a.filename, b.filename)


class PublishedSourcesTests(unittest.TestCase):
    def setUp(self):
        self.concepts = load_corpus()

    def test_internal_source_absent_even_carrying_a_url(self):
        # The divergence this guards: the reference list once filtered on url
        # alone, so an internal label gaining a url would print on paper while
        # the widget still withheld it on screen.
        concept = self.concepts["controls-in-validation"]
        internal = {
            "label": "D. Moshinsky, chatbot kickoff notes, 14 July 2026",
            "url": "https://example.org",
            "short": "Moshinsky 2026",
        }
        spiked = replace(concept, sources=[internal] + list(concept.sources))
        listed = _published_sources([spiked])
        self.assertTrue(listed)
        for line in listed:
            self.assertNotIn("Moshinsky", line)

    def test_published_sources_are_listed_once_each(self):
        selected = checklist_concepts(self.concepts, CITED)
        listed = _published_sources(selected)
        self.assertEqual(len(listed), len(set(listed)))

    def test_sources_without_a_url_are_absent(self):
        concept = self.concepts["controls-in-validation"]
        spiked = replace(
            concept,
            sources=[{"label": "Unpublished internal note", "short": "Internal"}],
        )
        self.assertEqual(_published_sources([spiked]), [])


if __name__ == "__main__":
    unittest.main()
