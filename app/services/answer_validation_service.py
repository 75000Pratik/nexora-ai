import re
from app.services.llm_service import LLMService


class AnswerValidationService:
    def __init__(self) -> None:
        self.llm_service = LLMService()

    def _has_unsupported_named_entities(
        self,
        answer: str,
        context: str,
    ) -> bool:
        pattern = (
            r"\b(?:Amazon\s+)?"
            r"[A-Z][a-zA-Z0-9]*(?:[-.][A-Za-z0-9]+)*\b"
        )

        answer_entities = {
            match.group(0).casefold()
            for match in re.finditer(pattern, answer, re.IGNORECASE)
        }
        context_entities = {
            match.group(0).casefold()
            for match in re.finditer(pattern, context, re.IGNORECASE)
        }

        return not answer_entities.issubset(context_entities)

    def is_supported(
        self,
        query: str,
        answer: str,
        context: str,
    ) -> bool:
        if self._has_unsupported_named_entities(
            answer=answer,
            context=context,
        ):
            return False

        if self._has_unrelated_project_claim(
            answer=answer,
            context=context,
        ):
            return False

        system_prompt = (
            "You are a strict factual claim verifier. "
            "Your job is to detect unsupported information.\n"
            "Follow these rules carefully:\n"
            "1. Verify EVERY factual claim in the answer.\n"
            "2. The context is the ONLY source of truth.\n"
            "3. If the answer adds even ONE factual detail "
            "not supported by the context, return UNSUPPORTED.\n"
            "4. A fact about a different project does not "
            "support a claim about the project being asked about.\n"
            "5. Check which project, system, or component each "
            "service and model belongs to. A name appearing "
            "somewhere in the context is NOT sufficient evidence.\n"
            "6. Do not combine facts from separate projects "
            "to construct an answer about one project.\n"
            "7. Do not assume that a claim is true because it "
            "sounds plausible or is technically common.\n"
            "8. If the context is insufficient or ambiguous, "
            "return UNSUPPORTED.\n"
            "9. Return SUPPORTED only when every factual claim "
            "is explicitly supported and correctly associated "
            "with the project in the question.\n"
            "Reply with exactly one word: SUPPORTED or UNSUPPORTED."
        )

        prompt = (
            f"Question:\n{query}\n\n"
            f"Evidence context:\n{context}\n\n"
            f"Answer to verify:\n{answer}\n\n"
            "Does the evidence support every factual claim in "
            "the answer, including each named service, model, "
            "date, and project association?"
        )

        try:
            verdict = self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )
        except Exception:
            return False

        return verdict.strip().upper() == "SUPPORTED"

    def _has_unrelated_project_claim(
        self,
        answer: str,
        context: str,
    ) -> bool:
        separate_project_pattern = (
            r"(?i)\b(?:a separate project|another project|"
            r"a different project)\b[^.]*\."
        )

        unrelated_sentences = re.findall(
            separate_project_pattern,
            context,
        )

        return any(
            any(
                entity.casefold() in sentence.casefold()
                for entity in re.findall(
                    r"\bAmazon\s+[A-Z][A-Za-z0-9]*\b",
                    answer,
                )
            )
            for sentence in unrelated_sentences
        )
