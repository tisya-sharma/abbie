"""Unit tests for the corpus loader. Run without an API key:

    python3 -m unittest packages.corpus_loader.test_corpus_loader

This file did not exist until prerequisite expansion needed it. assemble_context
decides what every answer is composed from and had no direct test at all, so a
change to which attributes it renders would have broken nothing and been noticed
only in a paid eval run. The rendering tests below are the guard for that.

validate's error branches were untested for the same reason: the corpus has always
been valid, so nothing exercised the paths that fire when it is not.
"""

import unittest

from packages.corpus_loader import (
    Concept,
    assemble_context,
    extract_citations,
    load_corpus,
    reading_order,
    validate,
)


def concept(cid: str, **kw) -> Concept:
    """A minimal valid concept, so each test only states what it is about."""
    fields = {
        "id": cid,
        "title": cid.replace("-", " ").title(),
        "level": "core",
        "clearance": "public",
        "provenance": "established",
        "status": "draft",
        "body": f"Body of {cid}.",
    }
    fields.update(kw)
    return Concept(**fields)


def build(*concepts: Concept) -> dict[str, Concept]:
    return {c.id: c for c in concepts}


class AssembleContextTests(unittest.TestCase):
    """What the model is actually handed, attribute by attribute."""

    def test_prerequisites_render_in_frontmatter_order(self):
        corpus = build(
            concept("a", level="foundational"),
            concept("b", level="foundational"),
            concept("c", requires=["a", "b"], leads_to=["a"]),
        )
        self.assertIn('requires="a, b"', assemble_context(corpus))

    def test_a_concept_without_prerequisites_renders_none(self):
        corpus = build(concept("a", level="foundational", leads_to=["b"]), concept("b"))
        block = assemble_context(corpus).split("<concept ")[1]
        self.assertIn('requires="none"', block)

    def test_prerequisites_absent_from_the_build_are_filtered_out(self):
        """A pure renderer, so a dangling edge is dropped rather than raised.

        Rejecting the build is validate's job. Keeping that split means a
        clearance-filtered build still renders instead of crashing.
        """
        corpus = build(concept("a", requires=["gone"], leads_to=["b"]), concept("b"))
        rendered = assemble_context(corpus)
        self.assertIn('requires="none"', rendered)
        self.assertNotIn("gone", rendered)

    def test_follow_ups_are_filtered_to_targets_that_resolve(self):
        corpus = build(concept("a", leads_to=["b", "missing"]), concept("b"))
        self.assertIn('follow_ups="b"', assemble_context(corpus))

    def test_body_and_wrapper_are_present(self):
        rendered = assemble_context(build(concept("a", leads_to=["a"])))
        self.assertTrue(rendered.startswith("<corpus>"))
        self.assertTrue(rendered.endswith("</corpus>"))
        self.assertIn("Body of a.", rendered)

    def test_blocks_appear_in_reading_order(self):
        corpus = build(
            concept("late", requires=["early"], leads_to=["early"]),
            concept("early", level="foundational", leads_to=["late"]),
        )
        rendered = assemble_context(corpus)
        self.assertLess(rendered.index('id="early"'), rendered.index('id="late"'))

    def test_every_rendered_prerequisite_resolves_in_the_real_corpus(self):
        """Content-independent, so it does not rot as concepts are added."""
        corpus = load_corpus()
        rendered = assemble_context(corpus)
        for block in rendered.split("<concept ")[1:]:
            attrs = block.split(">", 1)[0]
            requires = attrs.split('requires="', 1)[1].split('"', 1)[0]
            if requires == "none":
                continue
            for cid in requires.split(", "):
                self.assertIn(cid, corpus)


class ReadingOrderTests(unittest.TestCase):
    def test_prerequisites_precede_the_concepts_that_need_them(self):
        corpus = build(
            concept("advanced", requires=["basic"]),
            concept("basic", level="foundational"),
        )
        order = reading_order(corpus)
        self.assertLess(order.index("basic"), order.index("advanced"))

    def test_a_cycle_yields_fewer_ids_than_concepts(self):
        """The property validate relies on to detect cycles at all."""
        corpus = build(concept("a", requires=["b"]), concept("b", requires=["a"]))
        self.assertLess(len(reading_order(corpus)), len(corpus))

    def test_order_is_deterministic(self):
        corpus = load_corpus()
        self.assertEqual(reading_order(corpus), reading_order(corpus))


class ValidateTests(unittest.TestCase):
    def assert_one_error(self, corpus, fragment):
        errors = validate(corpus)
        self.assertTrue(
            any(fragment in e for e in errors), f"{fragment!r} not in {errors}"
        )

    def test_the_shipping_corpus_is_valid(self):
        self.assertEqual(validate(load_corpus()), [])

    def test_foundational_concept_may_not_declare_prerequisites(self):
        corpus = build(
            concept("a", level="foundational", requires=["b"], leads_to=["b"]),
            concept("b", leads_to=["a"]),
        )
        self.assert_one_error(corpus, "foundational concept declares prerequisites")

    def test_prerequisite_absent_from_the_build_is_an_error(self):
        corpus = build(concept("a", requires=["gone"], leads_to=["a"]))
        self.assert_one_error(corpus, "absent from this build")

    def test_cycle_is_reported(self):
        corpus = build(
            concept("a", requires=["b"], leads_to=["b"]),
            concept("b", requires=["a"], leads_to=["a"]),
        )
        self.assert_one_error(corpus, "cycle")

    def test_summarized_concept_needs_sources(self):
        corpus = build(concept("a", provenance="summarized", leads_to=["a"]))
        self.assert_one_error(corpus, "summarized without sources")

    def test_ask_must_be_phrased_as_a_question(self):
        corpus = build(concept("a", ask="What this is", leads_to=["a"]))
        self.assert_one_error(corpus, "ask is not phrased as a question")

    def test_checklist_entry_missing_either_half_is_rejected(self):
        corpus = build(concept("a", checklist=[{"item": "x"}], leads_to=["a"]))
        self.assert_one_error(corpus, "missing proves")

    def test_a_concept_whose_follow_ups_all_dangle_is_a_dead_end(self):
        corpus = build(concept("a", leads_to=["missing"]))
        self.assert_one_error(corpus, "no follow-up target resolves")


class ExtractCitationsTests(unittest.TestCase):
    CORPUS = {"selectivity": None, "what-is-binding": None}

    def test_unknown_ids_are_dropped(self):
        found = extract_citations("[selectivity] and [not-a-concept]", self.CORPUS)
        self.assertEqual(found, ["selectivity"])

    def test_duplicates_collapse_and_first_appearance_wins(self):
        found = extract_citations(
            "[what-is-binding] then [selectivity] then [what-is-binding]", self.CORPUS
        )
        self.assertEqual(found, ["what-is-binding", "selectivity"])

    def test_grouped_citations_split(self):
        found = extract_citations("[selectivity, what-is-binding]", self.CORPUS)
        self.assertEqual(sorted(found), ["selectivity", "what-is-binding"])


if __name__ == "__main__":
    unittest.main()
