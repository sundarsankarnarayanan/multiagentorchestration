"""
AI Agent System - Scout-Maker-Checker-Curator Pattern

A modular system for document processing using specialized agents.
"""

__version__ = "1.0.0"
__author__ = "AI Agent System"

from agents import ScoutAgent, MakerAgent, CheckerAgent, CuratorAgent
from models.document import Document, DocumentType
from workflows import WorkflowEngine, WorkflowDefinition

__all__ = [
    "ScoutAgent",
    "MakerAgent",
    "CheckerAgent",
    "CuratorAgent",
    "Document",
    "DocumentType",
    "WorkflowEngine",
    "WorkflowDefinition",
]
