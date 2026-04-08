"""
Sentra Python SDK — drop-in runtime control for any AI agent system.

Usage:
    from sentra.sdk.client import Sentra

    sentra = Sentra()

    result = sentra.evaluate(
        agent_id="my_agent",
        action="SEND_EMAIL",
        context={"verified": False}
    )

    if result.allowed:
        send_email()
    else:
        print(f"Blocked: {result.reason}")
"""

import requests
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SentraResult:
    allowed: bool
    decision: str
    reason: str
    risk_score: int
    raw: Optional[Dict[str, Any]] = None


class Sentra:
    def __init__(self, url: str = "http://127.0.0.1:8000"):
        self.url = url.rstrip("/")

    def evaluate(
        self,
        agent_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        target: Optional[str] = None,
        notification_type: Optional[str] = None,
    ) -> SentraResult:
        """
        Evaluate a proposed agent action against Sentra policies.

        Args:
            agent_id: Identifier for the agent (used for risk tracking)
            action: Action type (e.g. SEND_NOTIFICATION, EXPORT_DATA, FILE_WRITE)
            context: Policy context — any key/value pairs relevant to your domain
            target: Optional target of the action (e.g. email address, file path)
            notification_type: Optional notification type (e.g. approval, rejection)

        Returns:
            SentraResult with allowed, decision, reason, and risk_score
        """
        payload = {
            "agent_id": agent_id,
            "action_type": action,
            "target": target or "",
            "notification_type": notification_type or "",
            "policy_context": context or {},
        }

        try:
            resp = requests.post(
                f"{self.url}/agent-action", json=payload, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            decision = data.get("decision", "Blocked")
            return SentraResult(
                allowed=decision == "Allowed",
                decision=decision,
                reason=data.get("reason", ""),
                risk_score=data.get("risk", 0),
                raw=data,
            )

        except requests.ConnectionError:
            return SentraResult(
                allowed=False,
                decision="Blocked",
                reason="Sentra server unreachable — action blocked by default",
                risk_score=100,
            )
        except Exception as e:
            return SentraResult(
                allowed=False,
                decision="Blocked",
                reason=f"Sentra error: {e}",
                risk_score=100,
            )

    def guard(self, agent_id: str, action: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Decorator that blocks function execution if Sentra denies the action.

        Usage:
            @sentra.guard("my_agent", "SEND_EMAIL", {"verified": False})
            def send_email(to, subject, body):
                ...

        Raises:
            PermissionError if Sentra blocks the action.
        """
        def decorator(func):
            def wrapper(*args, **fn_kwargs):
                result = self.evaluate(agent_id, action, context, **kwargs)
                if not result.allowed:
                    raise PermissionError(f"Sentra blocked: {result.reason}")
                return func(*args, **fn_kwargs)
            wrapper.__name__ = func.__name__
            wrapper.sentra_result = None
            return wrapper
        return decorator

    def health(self) -> bool:
        """Check if Sentra server is reachable."""
        try:
            resp = requests.get(f"{self.url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def reset(self):
        """Reset all agent state and event logs."""
        requests.post(f"{self.url}/reset", timeout=5)
