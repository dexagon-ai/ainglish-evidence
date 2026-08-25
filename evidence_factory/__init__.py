"""Reusable orchestration for Ainglish evidence campaigns.

The factory deliberately delegates measurement and attempt lifecycle semantics to
the released :mod:`ainglish.panel` harness.  Its job is to make the surrounding
artifact, live-state, resource, and no-rerun gates uniform.
"""

from .core import (
    CampaignError,
    CampaignIndex,
    CampaignRunner,
    GpuRequirement,
    canonical_json,
    content_sha256,
)

__all__ = [
    "CampaignError",
    "CampaignIndex",
    "CampaignRunner",
    "GpuRequirement",
    "canonical_json",
    "content_sha256",
]
