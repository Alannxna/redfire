"""
RedFire Trading Platform - Application Core

This package contains the core application components including
configuration, middleware, and lifecycle management.
"""

__version__ = "2.0.0"
__author__ = "RedFire Team"

from app.config.settings import get_settings
from app.main import app

__all__ = ["get_settings", "app"]
