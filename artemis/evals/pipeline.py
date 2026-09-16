from dataclasses import dataclass


@dataclass
class EvalResult:
    candidate_id: str
    precision: float
    recall: float
    latency_ms_p95: int
    pass_gate: bool


def evaluate_candidate(candidate_id: str, baseline: dict, challenger: dict) -> EvalResult:
    precision = challenger["precision"] - baseline["precision"]
    recall = challenger["recall"] - baseline["recall"]
    latency_delta = challenger["latency_ms_p95"] - baseline["latency_ms_p95"]

    passed = precision >= 0.01 and recall >= 0 and latency_delta <= 40

    return EvalResult(
        candidate_id=candidate_id,
        precision=challenger["precision"],
        recall=challenger["recall"],
        latency_ms_p95=challenger["latency_ms_p95"],
        pass_gate=passed,
    )
