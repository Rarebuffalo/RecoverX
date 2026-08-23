import os
import json
from typing import Dict, Any
from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics & Benchmark"])


@router.get("/benchmark")
async def get_benchmark_analytics() -> Dict[str, Any]:
    """Returns the verified Phase 7A 25,000 synthetic benchmark results and threshold frontier."""
    json_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../../benchmarks/results/phase7a_analysis.json")
    )
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fallback default snapshot
    return {
        "status": "DEFAULT_SNAPSHOT",
        "metadata": {
            "total_cases": 25000,
            "revenue_at_risk_inr": 297652385.45,
            "seed": 42,
        },
        "economic_frontier": [],
        "pareto_thresholds": [20, 30, 40, 50, 60, 70, 80, 90],
    }
