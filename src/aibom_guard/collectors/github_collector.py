"""Read-only GitHub repository compliance evidence collector.

Collects compliance-relevant repository settings:
  - Default branch protection (required reviews, status checks)
  - Code scanning / SAST activity
  - Secret scanning alert status
  - Dependency review enablement

All operations are READ-ONLY and use the GitHub REST API.
Credentials: GITHUB_TOKEN environment variable (fine-grained PAT with
``repo:read`` scope is sufficient; classic PAT with ``repo`` also works).

Findings are mapped to ISO 42001 / EU AI Act controls in the output so they
can be attached to a compliance report as live evidence.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


_GH_API = "https://api.github.com"
_TIMEOUT = 10
_SAFE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._\-]{0,99}$')


def _validate_repo_slug(owner: str, repo: str) -> bool:
    """Return True only if owner and repo contain safe characters.

    Prevents path-traversal in the constructed API URL (e.g. owner='../').
    """
    return bool(_SAFE_NAME.match(owner) and _SAFE_NAME.match(repo))


def collect_github(
    owner: str,
    repo: str,
    *,
    token: str | None = None,
) -> dict:
    """Collect read-only compliance evidence from a GitHub repository.

    Args:
        owner: GitHub repository owner (user or org).
        repo:  Repository name.
        token: GitHub PAT. Falls back to ``GITHUB_TOKEN`` env var.

    Returns:
        Dict with ``source``, ``controls`` (control ID → evidence), and
        optionally ``error`` if the token is missing.
    """
    if not _validate_repo_slug(owner, repo):
        return {
            "source": f"github:{owner}/{repo}",
            "error": "Invalid owner or repo name — only alphanumeric, '.', '-', '_' allowed",
            "controls": {},
        }

    token = token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return {
            "source": f"github:{owner}/{repo}",
            "error": "GITHUB_TOKEN not set",
            "note": (
                "Set GITHUB_TOKEN env var with repo read scope. "
                "No evidence collected."
            ),
            "controls": {},
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aibom-guard",
    }

    evidence: dict = {
        "source": f"github:{owner}/{repo}",
        "controls": {},
    }

    # --- Repo info + default branch ---
    repo_data = _get(f"{_GH_API}/repos/{owner}/{repo}", headers)
    if "error" in repo_data:
        evidence["error"] = repo_data["error"]
        return evidence

    default_branch = repo_data.get("default_branch", "main")
    evidence["default_branch"] = default_branch
    evidence["visibility"] = repo_data.get("visibility", "unknown")

    # Control A.6.1.3 — Secure development lifecycle (branch protection)
    bp = _get(
        f"{_GH_API}/repos/{owner}/{repo}/branches/{default_branch}/protection",
        headers,
    )
    if "error" not in bp:
        required_reviews = (
            bp.get("required_pull_request_reviews", {}) or {}
        ).get("required_approving_review_count", 0)
        evidence["controls"]["A.6.1.3"] = {
            "title": "Secure development lifecycle",
            "source": "branch_protection",
            "evidence": {
                "branch_protection_enabled": True,
                "required_approving_reviews": required_reviews,
                "required_status_checks": bool(bp.get("required_status_checks")),
                "enforce_admins": bool(
                    (bp.get("enforce_admins") or {}).get("enabled")
                ),
            },
            "iso42001_note": (
                "Branch protection with required reviews supports controlled "
                "AI system deployment (A.6.2.5) and change management."
            ),
        }
    else:
        evidence["controls"]["A.6.1.3"] = {
            "title": "Secure development lifecycle",
            "evidence": {"branch_protection_enabled": False},
            "note": bp.get("error", "Branch protection not configured or not accessible"),
        }

    # Control A.6.2.4 — AI system verification and validation (code scanning)
    scans = _get(
        f"{_GH_API}/repos/{owner}/{repo}/code-scanning/analyses?per_page=1",
        headers,
    )
    if isinstance(scans, list):
        evidence["controls"]["A.6.2.4"] = {
            "title": "AI system verification and validation",
            "source": "code_scanning",
            "evidence": {
                "code_scanning_active": bool(scans),
                "latest_analysis": scans[0].get("created_at") if scans else None,
                "tool": (scans[0].get("tool") or {}).get("name") if scans else None,
                "ref": scans[0].get("ref") if scans else None,
            },
        }
    else:
        evidence["controls"]["A.6.2.4"] = {
            "title": "AI system verification and validation",
            "evidence": {"code_scanning_active": False},
            "note": "Code scanning not active or not accessible",
        }

    # Control A.6.1.3 (secret scanning) — also covers A.4.4 tooling security
    secrets = _get(
        f"{_GH_API}/repos/{owner}/{repo}/secret-scanning/alerts?per_page=5&state=open",
        headers,
    )
    if isinstance(secrets, list):
        evidence["controls"]["A.6.1.3_secrets"] = {
            "title": "Secret scanning (tooling security)",
            "source": "secret_scanning",
            "evidence": {
                "secret_scanning_active": True,  # nosec B105 — boolean flag, not a password
                "open_alerts": len(secrets),
                "secrets_found": bool(secrets),
            },
            "iso42001_note": "Prevents credential leakage affecting AI component supply chain.",
        }
    else:
        evidence["controls"]["A.6.1.3_secrets"] = {
            "title": "Secret scanning",
            "evidence": {"secret_scanning_active": False},  # nosec B105
            "note": "Secret scanning not active or alerts not accessible",
        }

    # Control A.6.2.5 — AI system deployment (dependency review)
    dep_review = _get(
        f"{_GH_API}/repos/{owner}/{repo}/dependency-graph/compare/"
        f"{default_branch}...{default_branch}",
        headers,
    )
    evidence["controls"]["A.6.2.5"] = {
        "title": "AI system deployment (dependency review)",
        "source": "dependency_graph",
        "evidence": {
            "dependency_graph_accessible": "error" not in dep_review,
        },
        "iso42001_note": "Dependency review detects new vulnerable AI library versions pre-merge.",
    }

    return evidence


def _get(url: str, headers: dict) -> dict | list:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # nosec B310 — HTTPS to api.github.com only
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}
