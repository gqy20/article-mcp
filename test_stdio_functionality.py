#!/usr/bin/env python3
"""
测试 Article MCP 在 stdio 模式下的所有功能
"""

import subprocess
import json
import sys
import time

def send_mcp_request(process, method, params=None, id=1):
    """发送 MCP 请求并等待响应"""
    request = {
        "jsonrpc": "2.0",
        "id": id,
        "method": method
    }
    if params:
        request["params"] = params

    # 发送请求
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json.encode())
    process.stdin.flush()

    # 读取响应（增加超时和更好的错误处理）
    start_time = time.time()
    response_lines = []
    timeout = 30  # 30秒超时

    while time.time() - start_time < timeout:
        try:
            # 检查进程是否还在运行
            if process.poll() is not None:
                stderr_output = process.stderr.read().decode() if process.stderr else ""
                return {"error": f"Process ended with code {process.returncode}. stderr: {stderr_output}"}

            # 设置非阻塞读取
            import select
            ready, _, _ = select.select([process.stdout], [], [], 0.1)

            if ready:
                line = process.stdout.readline()
                if not line:
                    break

                line = line.strip().decode()
                if line:
                    response_lines.append(line)
                    # 尝试解析JSON
                    try:
                        response = json.loads("\n".join(response_lines))
                        return response
                    except json.JSONDecodeError:
                        # 如果不是完整的JSON，继续读取
                        continue
        except Exception as e:
            print(f"读取响应时出错: {e}")
            continue

    return {"error": f"Timeout after {timeout} seconds. Received lines: {response_lines}"}

def test_tool(process, tool_name, params, test_description):
    """测试单个工具"""
    print(f"\n🧪 测试: {test_description}")
    print(f"工具: {tool_name}")
    print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")

    try:
        response = send_mcp_request(
            process,
            "tools/call",
            {
                "name": tool_name,
                "arguments": params
            }
        )

        if "error" in response:
            print(f"❌ 错误: {response['error']}")
            return False
        elif "result" in response:
            result = response["result"]
            if result.get("success", False):
                print(f"✅ 成功: {result.get('message', '操作完成')}")
                if "articles" in result:
                    print(f"📊 找到 {len(result['articles'])} 篇文献")
                elif "article" in result:
                    print(f"📄 获取到文献详情")
                elif "references" in result:
                    print(f"📚 找到 {len(result['references'])} 条参考文献")
                elif "relations" in result:
                    print(f"🔗 分析了文献关系")
                elif "quality_metrics" in result:
                    print(f"⭐ 获取了期刊质量指标")
                return True
            else:
                print(f"❌ 失败: {result.get('message', '未知错误')}")
                return False
        else:
            print(f"❌ 未知响应格式: {response}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 Article MCP v0.1.5 在 stdio 模式下的功能")
    print("=" * 60)

    # 启动 MCP 服务器
    try:
        process = subprocess.Popen(
            ["uvx", "--from", ".", "article-mcp", "server", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )

        # 等待服务器启动
        time.sleep(2)

        # 首先获取可用工具列表
        print("\n📋 获取可用工具列表...")
        response = send_mcp_request(process, "tools/list")

        if "error" in response:
            print(f"❌ 无法获取工具列表: {response['error']}")
            return

        tools = response.get("result", [])
        print(f"✅ 发现 {len(tools)} 个可用工具:")
        for tool in tools:
            print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")

        # 测试用例
        test_cases = [
            {
                "tool": "search_literature",
                "params": {"keyword": "machine learning", "max_results": 3},
                "description": "文献搜索功能"
            },
            {
                "tool": "get_article_details",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi"},
                "description": "文献详情获取功能"
            },
            {
                "tool": "get_references",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi", "max_results": 5},
                "description": "参考文献获取功能"
            },
            {
                "tool": "get_literature_relations",
                "params": {"identifier": "10.1016/j.cell.2021.01.014", "id_type": "doi", "relation_types": ["references", "similar"], "max_results": 3},
                "description": "文献关系分析功能"
            },
            {
                "tool": "get_journal_quality",
                "params": {"journal_name": "Nature"},
                "description": "期刊质量评估功能"
            },
            {
                "tool": "batch_search_literature",
                "params": {"queries": ["artificial intelligence", "cancer research"], "max_results_per_query": 3},
                "description": "批量文献搜索功能"
            }
        ]

        # 执行测试
        success_count = 0
        total_count = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            success = test_tool(
                process,
                test_case["tool"],
                test_case["params"],
                f"{i}. {test_case['description']}"
            )
            if success:
                success_count += 1
            time.sleep(1)  # 避免请求过快

        # 总结测试结果
        print("\n" + "=" * 60)
        print(f"📊 测试完成！")
        print(f"✅ 成功: {success_count}/{total_count} 个功能")
        print(f"❌ 失败: {total_count - success_count}/{total_count} 个功能")

        if success_count == total_count:
            print("🎉 所有功能测试通过！Article MCP v0.1.5 在 stdio 模式下工作正常。")
        else:
            print("⚠️ 部分功能存在问题，需要进一步检查。")

    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        return
    finally:
        # 清理进程
        if 'process' in locals():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

if __name__ == "__main__":
    main()