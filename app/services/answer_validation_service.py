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

    @staticmethod
    def _extract_cited_claims(
        answer: str,
        sources: list[str],
    ) -> list[tuple[str, list[str]]] | None:
        claims = []

        sentences = re.split(
            r"(?<=[.!?])\s+(?!\[Source\b)|(?<=\])\s+(?=[A-Z])",
            answer.strip(),
        )

        for sentence in sentences:
            if not sentence.strip():
                continue

            citations = re.findall(
                r"\[Source\b([^\]]*)(\]|$)",
                sentence,
            )

            if not citations:
                return None

            if any(
                not closing_bracket
                or not citation.strip().isdigit()
                for citation, closing_bracket in citations
            ):
                return None

            source_numbers = [
                int(citation.strip())
                for citation, _ in citations
            ]

            if any(
                number < 1 or number > len(sources)
                for number in source_numbers
            ):
                return None

            claim = re.sub(
                r"\s*\[Source\b[^\]]*\]",
                "",
                sentence,
            ).strip()

            if not claim:
                return None

            cited_sources = [
                sources[number - 1]
                for number in source_numbers
            ]

            claims.append((claim, cited_sources))

        return claims or None

    def are_citations_supported(
        self,
        answer: str,
        sources: list[str],
    ) -> bool:
        claims = self._extract_cited_claims(
            answer=answer,
            sources=sources,
        )

        if not claims:
            return False

        system_prompt = (
            "You are a strict claim-level citation verifier. "
            "Verify whether the provided evidence supports "
            "the specific claim.\n"
            "Rules:\n"
            "1. Use only the supplied cited evidence.\n"
            "2. Do not use outside knowledge or assumptions.\n"
            "3. Verify every factual detail in the claim.\n"
            "4. Check named services, models, dates, numbers, "
            "and project associations carefully.\n"
            "5. If the evidence is insufficient or ambiguous, "
            "return UNSUPPORTED.\n"
            "Reply with exactly one word: SUPPORTED or UNSUPPORTED."
        )

        for claim, cited_sources in claims:
            evidence = "\n\n".join(cited_sources)

            prompt = (
                f"Claim:\n{claim}\n\n"
                f"Cited evidence:\n{evidence}\n\n"
                "Does this evidence explicitly support the claim?"
            )

            try:
                verdict = self.llm_service.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                )
            except Exception:
                return False

            if verdict.strip().upper() != "SUPPORTED":
                return False

        return True

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
