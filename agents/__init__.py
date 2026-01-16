"""
AI Agent System - Agents Package

This package contains all agent implementations following the
Scout-Maker-Checker-Curator pattern.
"""

from .base import Agent, AgentOutput, AgentStatus, AgentCapability
from .scout import ScoutAgent
from .maker import MakerAgent
from .checker import CheckerAgent
from .curator import CuratorAgent

__all__ = [
    "Agent",
    "AgentOutput",
    "AgentStatus",
    "AgentCapability",
    "ScoutAgent",
    "MakerAgent",
    "CheckerAgent",
    "CuratorAgent",
]
