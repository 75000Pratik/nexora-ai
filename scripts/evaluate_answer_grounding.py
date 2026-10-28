
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

from answer_grounding_dataset import ANSWER_GROUNDING_DATASET
from app.services.answer_validation_service import (
    AnswerValidationService,
)


def main() -> None:
    validator = AnswerValidationService()

    total = len(ANSWER_GROUNDING_DATASET)
    correct = 0
    false_accepts = 0
    false_rejections = 0

    print(
        f"Evaluating {total} cases with the configured Ollama model...\n"
    )

    for case in ANSWER_GROUNDING_DATASET:
        print(f"\nAnswer under test: {case['answer']}")
        print(f"Context under test: {case['context']}")

        predicted = validator.is_supported(
            query=case["query"],
            answer=case["answer"],
            context=case["context"],
        )

        expected = case["expected_supported"]
        passed = predicted == expected

        if passed:
            correct += 1
        elif predicted and not expected:
            false_accepts += 1
        elif not predicted and expected:
            false_rejections += 1

        status = "PASS" if passed else "FAIL"
        verdict = "SUPPORTED" if predicted else "UNSUPPORTED"

        print(
            f"[{status}] {case['name']}: "
            f"expected={expected}, predicted={verdict}"
        )

    unsupported_cases = sum(
        not case["expected_supported"]
        for case in ANSWER_GROUNDING_DATASET
    )
    supported_cases = total - unsupported_cases

    accuracy = correct / total if total else 0.0
    false_accept_rate = (
        false_accepts / unsupported_cases
        if unsupported_cases else 0.0
    )
    false_rejection_rate = (
        false_rejections / supported_cases
        if supported_cases else 0.0
    )

    print("\n--- Evaluation summary ---")
    print(f"Correct: {correct}/{total}")
    print(f"Accuracy: {accuracy:.1%}")
    print(f"False acceptance rate: {false_accept_rate:.1%}")
    print(f"False rejection rate: {false_rejection_rate:.1%}")


if __name__ == "__main__":
    main()
