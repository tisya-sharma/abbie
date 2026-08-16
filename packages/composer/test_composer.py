"""Unit tests for reply composition. Run without an API key:

    python3 -m unittest packages.composer.test_composer
"""

import types
import unittest

from packages.composer import (
    DEFAULT_ABSTAIN_SUBJECT,
    PREREQUISITE_HINT,
    ComposerPrompts,
    _clean_subject,
    respond,
)
from packages.router import Route


def route(form: str | None) -> Route:
    return Route(
        behavior="answer", subject=None, fallback=False, fallback_reason=None,
        model="stub", prompt_tokens=0, completion_tokens=0, latency_ms=0, form=form,
    )


class RecordingClient:
    """Captures the message list instead of calling anything."""

    def __init__(self):
        self.messages: list[dict] = []
        usage = types.SimpleNamespace(
            prompt_tokens=0, completion_tokens=0,
            completion_tokens_details=types.SimpleNamespace(reasoning_tokens=0),
        )
        choice = types.SimpleNamespace(
            message=types.SimpleNamespace(content="ok"), finish_reason="stop"
        )
        response = types.SimpleNamespace(choices=[choice], usage=usage)
        outer = self

        class Completions:
            def create(self, **kwargs):
                outer.messages = kwargs["messages"]
                return response

        self.chat = types.SimpleNamespace(completions=Completions())


PROMPTS = ComposerPrompts(
    answer_system="answer system",
    redirect_system="redirect system",
    refuse_text="refuse",
    abstain_template="abstain {subject}",
)


class PrerequisiteHintTests(unittest.TestCase):
    """Prerequisite expansion is scoped to learning-mode questions.

    The scoping is the feature. A scientist asking a procedural question does not
    want a foundational term defined at them, so the hint must reach definitional
    turns and no others, and it must sit after history so later turns never
    replay it.
    """

    def hint_messages(self, form: str | None) -> list[dict]:
        client = RecordingClient()
        respond(
            client, route(form), "a question", PROMPTS, "stub", "low",
            history=[{"role": "user", "content": "earlier"}],
        )
        return client.messages

    def test_definitional_turn_receives_the_gloss_instruction(self):
        joined = " ".join(m["content"] for m in self.hint_messages("definitional"))
        self.assertIn(PREREQUISITE_HINT.strip(), joined)

    def test_procedural_turn_is_shaped_but_not_glossed(self):
        messages = self.hint_messages("procedural")
        joined = " ".join(m["content"] for m in messages)
        self.assertNotIn(PREREQUISITE_HINT.strip(), joined)
        self.assertIn("procedural answer", joined)

    def test_a_router_fallback_adds_no_post_history_system_message(self):
        """form None is the fallback path, which must reproduce prior behavior."""
        messages = self.hint_messages(None)
        self.assertEqual([m["role"] for m in messages], ["system", "user", "user"])

    def test_the_hint_sits_after_history(self):
        messages = self.hint_messages("definitional")
        hint_at = max(
            i for i, m in enumerate(messages)
            if m["role"] == "system" and PREREQUISITE_HINT.strip() in m["content"]
        )
        history_at = next(
            i for i, m in enumerate(messages) if m["content"] == "earlier"
        )
        self.assertGreater(hint_at, history_at)


class CleanSubjectTests(unittest.TestCase):
    """The abstain subject is the one visitor-supplied string that reaches a
    reply verbatim, with no model between the question and the page.
    """

    def test_named_reagent_passes_through(self):
        self.assertEqual(
            _clean_subject("clone 4B2 against STAT3"), "clone 4B2 against STAT3"
        )

    def test_catalog_number_passes_through(self):
        self.assertEqual(_clean_subject("AB-88231"), "AB-88231")

    def test_ipi_reagent_passes_through(self):
        # The guard must not fire on IPI's own products, which are exactly what
        # the abstention exists to talk about.
        self.assertEqual(
            _clean_subject("the IPI anti-TP53 rabbit antibody"),
            "the IPI anti-TP53 rabbit antibody",
        )

    def test_word_containing_a_document_word_passes_through(self):
        # "standardize" contains "standard"; matching whole words is what keeps
        # ordinary reagent phrasing out of the fallback.
        self.assertEqual(
            _clean_subject("the standardized control lot"),
            "the standardized control lot",
        )

    def test_manuscript_request_falls_back(self):
        self.assertEqual(_clean_subject("Deb's manuscript"), DEFAULT_ABSTAIN_SUBJECT)

    def test_draft_request_falls_back(self):
        self.assertEqual(
            _clean_subject("the IPI 4D framework draft"), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_internal_standard_request_falls_back(self):
        self.assertEqual(
            _clean_subject("the antibody QC standard"), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_internal_identifier_falls_back(self):
        self.assertEqual(_clean_subject("IPI-CHR-001"), DEFAULT_ABSTAIN_SUBJECT)

    def test_empty_subject_falls_back(self):
        self.assertEqual(_clean_subject(None), DEFAULT_ABSTAIN_SUBJECT)

    def test_overlong_subject_falls_back(self):
        self.assertEqual(
            _clean_subject(" ".join(["word"] * 13)), DEFAULT_ABSTAIN_SUBJECT
        )

    def test_brackets_are_stripped(self):
        self.assertEqual(_clean_subject("[what-is-binding]"), "what-is-binding")


if __name__ == "__main__":
    unittest.main()
