"""
MCP资源API - 提供静态和动态资源
"""

from .config_resources import register_config_resources
from .journal_resources import register_journal_resources

__all__ = ['register_config_resources', 'register_journal_resources']