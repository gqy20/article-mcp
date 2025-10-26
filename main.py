# -*- coding: utf-8 -*-
"""
Article MCP CLI兼容层
保持向后兼容，逐步迁移用户到新的入口点

注意：这个文件现在只是一个兼容层，所有实际功能已经迁移到
src/article_mcp/cli.py。建议用户直接使用 article_mcp.cli:main
"""

def main():
    """兼容性入口 - 重定向到新的CLI"""
    try:
        from article_mcp.cli import main as _main
        _main()
    except ImportError:
        # 如果包导入失败，尝试直接导入
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
            from article_mcp.cli import main as _main
            _main()
        except ImportError as e:
            print(f"错误：无法导入 article_mcp.cli 模块: {e}")
            print("请确保已正确安装 article-mcp 包")
            sys.exit(1)

def create_mcp_server():
    """兼容性函数 - 重定向到新的实现"""
    from article_mcp.cli import create_mcp_server as _create_mcp_server
    return _create_mcp_server()


if __name__ == "__main__":
    main()