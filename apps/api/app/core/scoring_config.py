from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ScoreBandConfig:
    HIGH_MIN: int = 80
    MEDIUM_MIN: int = 60
    LOW_MIN: int = 40
    # 0 - 39 is VERY_LOW


@dataclass(frozen=True)
class RecoveryScoringConfig:
    """Configurable weights and thresholds for the interpretable scoring model."""

    BASE_SCORE: int = 30

    # Failure Category Points
    FAILURE_CATEGORY_POINTS: Dict[str, int] = None

    # Score Bands
    SCORE_BANDS: ScoreBandConfig = ScoreBandConfig()

    def __post_init__(self):
        if self.FAILURE_CATEGORY_POINTS is None:
            object.__setattr__(
                self,
                "FAILURE_CATEGORY_POINTS",
                {
                    "TRANSIENT": 30,
                    "CUSTOMER_ACTION_REQUIRED": 20,
                    "INSUFFICIENT_FUNDS": 10,
                    "PAYMENT_METHOD_ISSUE": 5,
                    "UNKNOWN": 0,
                    "PERMANENT": -40,
                },
            )


# Default Singleton Configuration
scoring_config = RecoveryScoringConfig()
