"""
pipelines package
=================
Production Task Pipelines for Stage 5.
"""
from __future__ import annotations

import importlib
from typing import Any

def get_leetcode_archiver() -> Any:
    mod = importlib.import_module("pipelines.01_leetcode_archiver")
    return mod.LeetCodeArchiverPipeline()

def get_social_media_pipeline() -> Any:
    mod = importlib.import_module("pipelines.02_social_media_pipeline")
    return mod.SocialMediaPipeline()

def get_secured_snapshot_forensics() -> Any:
    mod = importlib.import_module("pipelines.03_secured_snapshot_forensics")
    return mod.SecuredSnapshotForensicsPipeline()

__all__ = [
    "get_leetcode_archiver",
    "get_social_media_pipeline",
    "get_secured_snapshot_forensics",
]
