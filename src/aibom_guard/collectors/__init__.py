"""Read-only evidence collectors for live compliance data (Milestone 5).

All collectors are strictly read-only: they never write to, modify, or
trigger actions on the target systems. Credentials are taken from environment
variables only — never hardcoded or stored by this tool.

Available collectors:
  github_collector  — branch protection, SAST, secret scanning (GITHUB_TOKEN)
  huggingface_collector — model metadata, license, training datasets (public, no auth)
"""
from .github_collector import collect_github
from .huggingface_collector import collect_hf_models

__all__ = ["collect_github", "collect_hf_models"]
