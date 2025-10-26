"""
向后兼容工具模块 - 保留旧版本工具接口
提供向后兼容性，确保现有MCP客户端配置不受影响
"""

import logging

def register_legacy_tools(mcp, services, logger):
    """注册向后兼容的工具

    注意：这些工具是旧版本接口，建议迁移到新的核心工具：
    - search_literature (工具1)
    - get_article_details (工具2)
    - get_references (工具3)
    - get_literature_relations (工具4)
    - get_journal_quality (工具5)
    - batch_search_literature (工具6)
    """
    logger.info("注册向后兼容工具...")

    # 这里可以保留一些关键的旧版本工具
    # 或者提供重定向到新工具的包装器

    logger.warning("使用的是向后兼容工具，建议迁移到新的6工具架构")

    return []