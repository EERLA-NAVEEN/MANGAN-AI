"""
MANGAN-AI Recommendations State & Workflow Manager
Manages candidate actions, human-in-the-loop review statuses, auditor notes,
and ensures decisions remain strictly under human approval.
Scopes approvals by mine and section to prevent cross-scenario state leakage.

DISCLAIMER:
Recommendations are candidate actions for human review and are not autonomous mine-control instructions.
"""

from typing import List, Dict, Any

def _has_scopes(session_state) -> bool:
    if hasattr(session_state, "recommendation_scopes"):
        return True
    try:
        return "recommendation_scopes" in session_state
    except (TypeError, AttributeError):
        return False

def _get_scopes(session_state) -> dict:
    if hasattr(session_state, "recommendation_scopes"):
        val = getattr(session_state, "recommendation_scopes")
        if isinstance(val, dict):
            return val
    try:
        if "recommendation_scopes" in session_state and isinstance(session_state["recommendation_scopes"], dict):
            return session_state["recommendation_scopes"]
    except (TypeError, AttributeError):
        pass
    scopes = {}
    try:
        setattr(session_state, "recommendation_scopes", scopes)
    except Exception:
        pass
    try:
        session_state["recommendation_scopes"] = scopes
    except Exception:
        pass
    return scopes

def _set_recommendations(session_state, recs: list):
    try:
        setattr(session_state, "recommendations", recs)
    except Exception:
        pass
    try:
        session_state["recommendations"] = recs
    except Exception:
        pass

class RecommendationManager:
    @staticmethod
    def get_scope_key(mine_id: str, section: str) -> str:
        return f"{mine_id}_{section}"

    @staticmethod
    def initialize_session_recommendations(
        session_state,
        generated_recs: List[Dict[str, Any]],
        scope_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        Initializes or merges candidate recommendations scoped by mine/section.
        Prevents approval state leakage between different concession sections.
        """
        scopes = _get_scopes(session_state)
        key = scope_key or "default"

        if key not in scopes or not scopes[key]:
            scopes[key] = generated_recs
        else:
            # Preserve existing user decision statuses if any for this specific scope
            existing_statuses = {
                r["recommendation_id"]: (r["status"], r.get("decision_notes", ""))
                for r in scopes[key]
            }
            for rec in generated_recs:
                if rec["recommendation_id"] in existing_statuses:
                    rec["status"], rec["decision_notes"] = existing_statuses[rec["recommendation_id"]]
            scopes[key] = generated_recs

        _set_recommendations(session_state, scopes[key])
        return scopes[key]

    @staticmethod
    def update_status(session_state, rec_id: str, new_status: str, notes: str = "", scope_key: str = None):
        """Updates review status (Approved, Rejected, Deferred) and auditor notes for the target scope."""
        scopes = _get_scopes(session_state)
        key = scope_key or "default"
        if key in scopes:
            for rec in scopes[key]:
                if rec["recommendation_id"] == rec_id:
                    rec["status"] = new_status
                    if notes:
                        rec["decision_notes"] = notes
                    break

        _set_recommendations(session_state, scopes.get(key, []))

    @staticmethod
    def get_summary_stats(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculates status counts."""
        if not recommendations:
            return {"total": 0, "pending": 0, "approved": 0, "rejected": 0, "deferred": 0}
        total = len(recommendations)
        pending = sum(1 for r in recommendations if r.get("status") == "Pending Review")
        approved = sum(1 for r in recommendations if r.get("status") == "Approved")
        rejected = sum(1 for r in recommendations if r.get("status") == "Rejected")
        deferred = sum(1 for r in recommendations if r.get("status") == "Deferred")
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "deferred": deferred
        }
