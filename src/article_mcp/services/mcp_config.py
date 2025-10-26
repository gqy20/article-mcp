"""
MCP配置管理模块
用于从MCP客户端配置中读取API密钥等敏感信息
"""

import json
import logging
import os
from pathlib import Path
from typing import Any


class MCPConfigManager:
    """MCP配置管理器"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self._config_cache: dict[str, Any] | None = None
        self._config_paths = [
            # Claude Desktop 配置路径
            Path.home() / ".config" / "claude-desktop" / "config.json",
            Path.home() / ".config" / "claude" / "config.json",
            # 其他可能的配置路径
            Path.home() / ".claude" / "config.json",
            # 环境变量指定的路径
            Path(os.getenv("CLAUDE_CONFIG_PATH", "")) if os.getenv("CLAUDE_CONFIG_PATH") else None,
        ]
        # 过滤掉不存在的路径
        self._config_paths = [p for p in self._config_paths if p is not None and p.exists()]

    def load_mcp_config(self) -> dict[str, Any]:
        """加载MCP配置文件"""
        if self._config_cache is not None:
            return self._config_cache

        for config_path in self._config_paths:
            try:
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                # 查找 article-mcp 服务配置
                mcp_servers = config.get("mcpServers", {})
                article_mcp_config = mcp_servers.get("article-mcp", {})

                # 提取环境变量配置
                env_config = article_mcp_config.get("env", {})

                # 缓存配置
                self._config_cache = env_config

                self.logger.info(f"成功加载MCP配置: {config_path}")
                return env_config

            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                self.logger.debug(f"配置文件 {config_path} 读取失败: {e}")
                continue

        # 如果没有找到配置文件，返回空字典
        self._config_cache = {}
        self.logger.info("未找到MCP配置文件，将使用环境变量")
        return {}

    def get_easyscholar_key(self, param_key: str | None = None) -> str | None:
        """获取EasyScholar密钥，按优先级返回

        优先级顺序：
        1. MCP配置文件中的密钥
        2. 函数参数中的密钥
        3. 环境变量中的密钥
        """
        # 1. 从MCP配置获取
        mcp_config = self.load_mcp_config()
        config_key = mcp_config.get("EASYSCHOLAR_SECRET_KEY")

        if config_key:
            self.logger.info("使用MCP配置中的EasyScholar密钥")
            return config_key

        # 2. 从函数参数获取
        if param_key:
            self.logger.info("使用函数参数中的EasyScholar密钥")
            return param_key

        # 3. 从环境变量获取
        env_key = os.getenv("EASYSCHOLAR_SECRET_KEY")
        if env_key:
            self.logger.info("使用环境变量中的EasyScholar密钥")
            return env_key

        self.logger.debug("未找到EasyScholar密钥")
        return None

    def get_api_config(self, api_name: str) -> dict[str, Any]:
        """获取特定API配置"""
        mcp_config = self.load_mcp_config()
        return mcp_config.get(f"{api_name.upper()}_CONFIG", {})

    def get_search_preferences(self) -> dict[str, Any]:
        """获取搜索偏好配置"""
        mcp_config = self.load_mcp_config()
        return {
            "default_sources": mcp_config.get("DEFAULT_SOURCES", ["europe_pmc", "pubmed"]),
            "max_results": mcp_config.get("DEFAULT_MAX_RESULTS", 10),
            "enable_cache": mcp_config.get("ENABLE_CACHE", True),
        }

    def get_config_info(self) -> dict[str, Any]:
        """获取配置信息（用于调试）"""
        mcp_config = self.load_mcp_config()
        return {
            "config_paths": [str(p) for p in self._config_paths],
            "config_loaded": bool(mcp_config),
            "has_easyscholar_key": bool(mcp_config.get("EASYSCHOLAR_SECRET_KEY")),
            "easyscholar_key_from_env": bool(os.getenv("EASYSCHOLAR_SECRET_KEY")),
            "config_content": {
                k: "***" if "key" in k.lower() else v for k, v in mcp_config.items()
            },
        }


# 全局配置管理器实例
_config_manager: MCPConfigManager | None = None


def get_config_manager(logger: logging.Logger | None = None) -> MCPConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = MCPConfigManager(logger)
    return _config_manager


def get_easyscholar_key(
    param_key: str | None = None, logger: logging.Logger | None = None
) -> str | None:
    """获取EasyScholar密钥的便捷函数"""
    manager = get_config_manager(logger)
    return manager.get_easyscholar_key(param_key)


def reset_config_cache():
    """重置配置缓存（用于测试）"""
    global _config_manager
    _config_manager = None
