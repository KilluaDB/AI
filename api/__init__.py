"""
SchemaAgent API Module

This module provides a FastAPI REST API for the SchemaAgent database design system.
"""

from .app import app, start_server

__all__ = ['app', 'start_server']
