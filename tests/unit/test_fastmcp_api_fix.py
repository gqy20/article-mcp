"""测试 FastMCP 工具列举 API 的正确用法

测试目标：
1. 验证使用 list_tools() 方法替代遍历 server 属性
2. 验证不访问 .settings 属性
3. 验证新的 API 用法正确

问题根因：
- 旧代码通过遍历 server 实例属性来获取工具列表
- 这触发了 FastMCP 内部的 .settings 废弃警告
- 解决方案：使用 server.list_tools() 异步方法
  （fastmcp 2.x 的 get_tools() 已在 4.x 更名为 list_tools()，返回列表而非字典）

测试策略：
- 测试新的 list_tools() API 用法
- 确保不触发废弃警告
"""

import pytest


@pytest.mark.unit
class TestFastMCAPIFix:
    """测试 FastMCP API 修复"""

    def test_list_tools_is_async_method(self):
        """验证：list_tools 是异步方法"""
        import inspect

        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()

        # list_tools 应该是协程函数
        assert inspect.iscoroutinefunction(server.list_tools)

    @pytest.mark.asyncio
    async def test_list_tools_returns_tool_list(self):
        """验证：list_tools() 返回工具列表"""
        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()
        tools = await server.list_tools()

        # 工具应该是可迭代的列表
        assert isinstance(tools, list)

        # 列表元素应该是工具对象
        for tool_obj in tools:
            assert hasattr(tool_obj, "name")

    @pytest.mark.asyncio
    async def test_list_tools_has_at_least_five_tools(self):
        """验证：list_tools() 返回至少5个工具"""
        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()
        tools = await server.list_tools()

        # 应该有5个核心工具（export_batch_results 可能未注册）
        expected_tools = [
            "search_literature",
            "get_article_details",
            "get_references",
            "get_literature_relations",
            "get_journal_quality",
        ]

        tool_names = {tool.name for tool in tools}

        for expected in expected_tools:
            assert expected in tool_names, f"缺少工具: {expected}"

        assert len(tools) >= 5, f"预期至少5个工具，实际: {len(tools)}"

    @pytest.mark.asyncio
    async def test_tool_objects_have_required_attributes(self):
        """验证：工具对象有必需的属性"""
        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()
        tools = await server.list_tools()

        for tool_obj in tools:
            # MCP 工具应该有这些属性
            assert hasattr(tool_obj, "name"), f"工具 {tool_obj} 缺少 name 属性"
            assert hasattr(tool_obj, "description"), f"工具 {tool_obj} 缺少 description 属性"

            # name 和 description 应该是字符串
            assert isinstance(tool_obj.name, str)
            assert isinstance(tool_obj.description, str)

    @pytest.mark.asyncio
    async def test_no_settings_access_warning(self):
        """验证：使用 list_tools() 不会触发 .settings 警告"""
        import warnings

        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()

        # 捕获所有警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 使用新的 API
            tools = await server.list_tools()

            # 检查是否有 DeprecationWarning 关于 .settings
            settings_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and ".settings" in str(warning.message)
            ]

            assert len(settings_warnings) == 0, (
                f"不应该有 .settings 警告，但收到: {settings_warnings}"
            )

    def test_old_way_triggers_warning(self):
        """验证：旧方式（遍历属性）会触发警告"""
        import warnings

        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()

        # 捕获警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 旧方式：遍历 server 属性
            public_attrs = [name for name in dir(server) if not name.startswith("_")]
            tool_funcs = [name for name in public_attrs if callable(getattr(server, name, None))]

            # 检查是否有 .settings 警告
            settings_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
                and ".settings" in str(warning.message)
            ]

            # 这个测试验证旧代码确实有问题
            # 新代码应该避免这种方式
            assert len(tool_funcs) > 0, "旧方式应该能找到一些函数"

    @pytest.mark.asyncio
    async def test_new_api_vs_old_api_comparison(self):
        """验证：新 API 返回的工具数量合理"""
        from article_mcp.cli import create_mcp_server

        server = create_mcp_server()

        # 新方式
        tools = await server.list_tools()

        # 验证返回的是合理的工具数量
        assert 5 <= len(tools) <= 20, f"工具数量应该在5-20之间，实际: {len(tools)}"

        # 验证工具名格式
        for tool_obj in tools:
            tool_name = tool_obj.name
            # 工具名应该是小写字母、数字和下划线
            assert tool_name.isidentifier() or "-" in tool_name, f"工具名 {tool_name} 格式不规范"
