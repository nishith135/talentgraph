"""
Quick sanity check — prints all test cases in the golden dataset.
Run this to confirm the dataset loaded correctly before building the harness.
"""

from eval.golden_dataset import GOLDEN_DATASET


def main():
    print(f"Golden dataset loaded — {len(GOLDEN_DATASET)} test cases\n")
    print(f"{'ID':<8} {'Notes':<60} {'Min Jobs':<10} {'Retries'}")
    print("-" * 90)

    for tc in GOLDEN_DATASET:
        print(
            f"{tc['id']:<8} "
            f"{tc['notes'][:58]:<60} "
            f"{tc['expected_min_jobs']:<10} "
            f"{tc['expected_retry_count']}"
        )

    # Coverage summary
    happy_path = [tc for tc in GOLDEN_DATASET if tc["expected_retry_count"] == 0]
    retry_cases = [tc for tc in GOLDEN_DATASET if tc["expected_retry_count"] > 0]
    edge_cases = [tc for tc in GOLDEN_DATASET if tc["expected_min_jobs"] == 0]

    print(f"\nCoverage:")
    print(f"  Happy path cases : {len(happy_path)}")
    print(f"  Retry loop cases : {len(retry_cases)}")
    print(f"  Edge cases (0 jobs expected): {len(edge_cases)}")


if __name__ == "__main__":
    main()