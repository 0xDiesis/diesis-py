"""Retained RPC diagnostics and conservative versioned signed-action decoding."""

from __future__ import annotations

from typing import Any

SIGNED_ACTION_ERROR_REASONS = (
    "invalid_signed_action",
    "signed_action_route_mismatch",
    "signed_action_expired",
    "exchange_relayer_unconfigured",
    "exchange_replay_conflict",
    "exchange_principal_capacity",
    "exchange_global_capacity",
    "exchange_tracker_unavailable",
    "exchange_admission_failed",
    "exchange_submission_outcome_unknown",
)


class RpcError(RuntimeError):
    """A provider's original structured error, retained without message inference."""

    def __init__(self, error: Any):
        self.error = error
        self.code = error.get("code") if type(error) is dict else None
        self.message = error.get("message") if type(error) is dict else None
        self.data = error.get("data") if type(error) is dict else None
        super().__init__(f"RPC error: {error}")


def decode_signed_action_error(original: Any) -> dict[str, Any]:
    """Decode only the known wire contract. Never retries or grants admission authority."""
    raw = original.error if isinstance(original, RpcError) else original
    seen: set[int] = set()
    for _ in range(16):
        if id(raw) in seen:
            break
        seen.add(id(raw))
        if isinstance(raw, RpcError):
            raw = raw.error
            continue
        if type(raw) is dict:
            if "code" in raw or "cause" not in raw:
                break
            raw = raw["cause"]
        elif isinstance(raw, BaseException) and raw.__cause__ is not None:
            raw = raw.__cause__
        else:
            break
    code = raw.get("code") if type(raw) is dict else None
    message = raw.get("message") if type(raw) is dict else str(raw) if isinstance(raw, BaseException) else None
    data = raw.get("data") if type(raw) is dict else None
    result = {
        "status": "unknown",
        "original": original,
        "code": code,
        "message": message,
        "data": data,
        "cause": original.__cause__
        if isinstance(original, BaseException)
        else original.get("cause")
        if type(original) is dict
        else None,
        "retryable": False,
        "admission": "unknown",
    }
    if type(data) is not dict or set(data) != {"version", "kind", "reason", "retryable", "admission"}:
        return result
    reason = data["reason"]
    if (
        type(code) is not int
        or not isinstance(message, str)
        or type(data["version"]) is not int
        or data["version"] != 1
        or data["kind"] != "signed-action-error"
        or data["retryable"] is not False
        or data["admission"] != "unknown"
        or reason not in SIGNED_ACTION_ERROR_REASONS
    ):
        return result
    expected = (
        -32017
        if reason == "exchange_submission_outcome_unknown"
        else -32015
        if reason in SIGNED_ACTION_ERROR_REASONS[:3]
        else -32016
    )
    if code != expected:
        return result
    return {**result, "status": "known", "reason": reason}
