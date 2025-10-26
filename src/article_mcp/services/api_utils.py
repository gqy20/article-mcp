"""
统一的API调用工具 - Linus风格：简单直接
"""

import logging
from functools import lru_cache
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


class UnifiedAPIClient:
    """统一的API客户端 - 简单直接"""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger(__name__)
        self.session = self._create_session()
        self.timeout = 30

    def _create_session(self) -> requests.Session:
        """创建带重试的会话"""
        session = requests.Session()

        # 统一的重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 1, 2, 4秒指数退避
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 统一的请求头
        session.headers.update(
            {
                "User-Agent": "Article-MCP/2.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
        )

        return session

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        统一的GET请求 - 一个方法搞定所有GET请求

        Args:
            url: 请求URL
            params: 查询参数
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            统一格式的响应
        """
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            response = self.session.get(
                url, params=params, headers=request_headers, timeout=timeout or self.timeout
            )
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers),
                "url": response.url,
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时", "error_type": "timeout", "url": url}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GET请求失败 {url}: {e}")
            return {"success": False, "error": str(e), "error_type": "request_error", "url": url}
        except Exception as e:
            self.logger.error(f"GET请求异常 {url}: {e}")
            return {"success": False, "error": str(e), "error_type": "unknown_error", "url": url}

    def post(
        self,
        url: str,
        data: dict | str | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        统一的POST请求 - 一个方法搞定所有POST请求

        Args:
            url: 请求URL
            data: 表单数据
            json: JSON数据
            headers: 额外请求头
            timeout: 超时时间

        Returns:
            统一格式的响应
        """
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            response = self.session.post(
                url, data=data, json=json, headers=request_headers, timeout=timeout or self.timeout
            )
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers),
                "url": response.url,
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "请求超时", "error_type": "timeout", "url": url}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"POST请求失败 {url}: {e}")
            return {"success": False, "error": str(e), "error_type": "request_error", "url": url}
        except Exception as e:
            self.logger.error(f"POST请求异常 {url}: {e}")
            return {"success": False, "error": str(e), "error_type": "unknown_error", "url": url}

    def close(self):
        """关闭会话"""
        if hasattr(self.session, "close"):
            self.session.close()


# 全局API客户端实例
_api_client: UnifiedAPIClient | None = None


def get_api_client(logger: logging.Logger | None = None) -> UnifiedAPIClient:
    """获取统一的API客户端"""
    global _api_client
    if _api_client is None:
        _api_client = UnifiedAPIClient(logger)
    return _api_client


@lru_cache(maxsize=5000)
def cached_get(url: str, params: str | None = None) -> dict[str, Any]:
    """
    带缓存的GET请求 - 简单直接

    Args:
        url: 请求URL
        params: 序列化的查询参数

    Returns:
        API响应
    """
    api_client = get_api_client()

    # 反序列化参数
    query_params = eval(params) if params else None

    return api_client.get(url, query_params)


def make_api_request(method: str, url: str, **kwargs) -> dict[str, Any]:
    """
    统一的API请求接口 - 简单直接

    Args:
        method: HTTP方法 ("GET" 或 "POST")
        url: 请求URL
        **kwargs: 其他请求参数

    Returns:
        统一格式的响应
    """
    api_client = get_api_client()

    if method.upper() == "GET":
        return api_client.get(url, **kwargs)
    elif method.upper() == "POST":
        return api_client.post(url, **kwargs)
    else:
        return {
            "success": False,
            "error": f"不支持的HTTP方法: {method}",
            "error_type": "invalid_method",
        }


# 便捷函数
def simple_get(url: str, **params) -> dict[str, Any]:
    """简单的GET请求"""
    return get_api_client().get(url, params)


def simple_post(url: str, **kwargs) -> dict[str, Any]:
    """简单的POST请求"""
    return get_api_client().post(url, **kwargs)
