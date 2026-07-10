from app.models.schemas import EnvironmentalInput
from app.knowledge.relationship_graph import match_relationships
from app.reasoning.synthesizer import generate_recommendations


def run_example_case():
    example_input = EnvironmentalInput(
        soil_organic_carbon_pct=0.3,
        rainfall="low",
        land_use_type="monoculture wheat",
        region_type="semi-arid",
    )

    matched = match_relationships(example_input)
    print(f"Relationships matched (deterministic layer): {len(matched)}")
    for rel in matched:
        print(f"  - {rel['id']}")
    print()

    result = generate_recommendations(example_input)
    print(f"Recommendations returned by LLM synthesis: {len(result.recommendations)}\n")

    if len(result.recommendations) < len(matched):
        print(f"WARNING: {len(matched) - len(result.recommendations)} matched relationship(s) "
              f"did not produce a recommendation.\n")
    elif len(result.recommendations) > len(matched):
        print(f"WARNING: synthesis returned MORE recommendations than relationships matched.\n")
    else:
        print("Matched count and returned count are equal — no drops or over-merges detected.\n")

    for i, rec in enumerate(result.recommendations, start=1):
        print(f"[{i}] {rec.action}")
        print(f"    Mechanism: {rec.mechanism}")
        print(f"    Impacted metrics: {rec.impacted_metrics}")
        print(f"    Estimated effect: {rec.estimated_effect}")
        print(f"    Time horizon: {rec.time_horizon}")
        print(f"    Confidence: {rec.confidence}")
        print(f"    Source: {rec.source}\n")

    actions_text = " ".join(r.action.lower() for r in result.recommendations)
    if "agroforestry" in actions_text or "intercrop" in actions_text:
        print("PASS: agroforestry/intercropping surfaced as expected.")
    else:
        print("CHECK: agroforestry/intercropping did NOT surface — review matching logic.")


if __name__ == "__main__":
    run_example_case()