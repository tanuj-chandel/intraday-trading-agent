from typing import Dict, Any

class OverfittingDetector:
    """
    Quantifies strategy overfitting risk (Score 0-100) based on Out-of-Sample (OOS) performance degradation.
    """

    @classmethod
    def calculate_overfitting_score(
        cls,
        train_pf: float,
        val_pf: float,
        oos_pf: float,
        train_return: float,
        oos_return: float
    ) -> Dict[str, Any]:
        # Calculate degradation percentages
        pf_degradation = 0.0
        if train_pf > 0:
            pf_degradation = max(0.0, ((train_pf - oos_pf) / train_pf) * 100.0)

        ret_degradation = 0.0
        if train_return > 0:
            ret_degradation = max(0.0, ((train_return - oos_return) / train_return) * 100.0)

        # Composite score from 0 (No Overfitting) to 100 (Severe Overfitting)
        overfitting_score = round(min(100.0, (pf_degradation * 0.6) + (ret_degradation * 0.4)), 1)

        if overfitting_score >= 50.0:
            risk_level = "HIGH_OVERFITTING_RISK"
            assessment = "Severe performance drop between in-sample training and out-of-sample test. Likely curve-fitted."
        elif overfitting_score >= 25.0:
            risk_level = "MODERATE_RISK"
            assessment = "Noticeable degradation in out-of-sample conditions. Parameter robustness is fragile."
        else:
            risk_level = "LOW_RISK"
            assessment = "Out-of-sample performance is consistent with in-sample expectations."

        return {
            "overfitting_risk_score": overfitting_score,
            "risk_level": risk_level,
            "assessment": assessment,
            "metrics_comparison": {
                "train_profit_factor": round(train_pf, 2),
                "val_profit_factor": round(val_pf, 2),
                "oos_profit_factor": round(oos_pf, 2),
                "train_return_pct": round(train_return, 2),
                "oos_return_pct": round(oos_return, 2),
                "oos_degradation_pct": round(pf_degradation, 1)
            }
        }
