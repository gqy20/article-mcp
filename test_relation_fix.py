#!/usr/bin/env python3
"""
测试 get_literature_relations 参数修复效果
"""

import subprocess
import json
import time
import sys

def send_mcp_request(process, method, params=None, id=1):
    """发送 MCP 请求并等待响应"""
    request = {
        "jsonrpc": "2.0",
        "id": id,
        "method": method
    }
    if params:
        request["params"] = params

    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()

    # 读取响应
    start_time = time.time()
    response = ""
    timeout = 45

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            return {"error": f"Process ended with code {process.returncode}"}

        line = process.stdout.readline()
        if not line:
            break

        response += line.strip()
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            continue

    return {"error": f"Timeout after {timeout} seconds"}

def extract_mcp_result(response):
    """从 MCP 响应中提取实际结果"""
    if "error" in response:
        return {"success": False, "error": response["error"]}

    if "result" not in response:
        return {"success": False, "error": "No result field in response"}

    result = response["result"]

    # 检查是否有 content 字段
    if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
        content = result["content"][0]
        if "text" in content:
            try:
                # 尝试解析 JSON 文本
                actual_result = json.loads(content["text"])
                return actual_result
            except json.JSONDecodeError:
                # 如果不是 JSON，直接返回文本
                return {"success": True, "message": content["text"]}

    # 如果不是标准格式，直接返回 result
    return result

def test_relation_params():
    """测试 get_literature_relations 参数修复"""
    print("🧪 测试 get_literature_relations 参数修复效果")
    print("=" * 50)

    # 启动服务器
    try:
        process = subprocess.Popen(
            ["uvx", "--from", ".", "article-mcp", "server", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        time.sleep(3)

        # 初始化
        init_response = send_mcp_request(process, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        })

        if "error" in init_response:
            print(f"❌ 初始化失败: {init_response['error']}")
            return False

        print("✅ 服务器初始化成功")

        # 测试用例
        test_cases = [
            {
                "name": "测试 identifier 参数 (向后兼容)",
                "params": {
                    "identifier": "10.1016/j.cell.2021.01.014",
                    "id_type": "doi",
                    "relation_types": ["references"],
                    "max_results": 2
                }
            },
            {
                "name": "测试 identifiers 参数 (原方式)",
                "params": {
                    "identifiers": "10.1016/j.cell.2021.01.014",
                    "id_type": "doi",
                    "relation_types": ["references"],
                    "max_results": 2
                }
            },
            {
                "name": "测试 identifiers 列表参数 (批量)",
                "params": {
                    "identifiers": ["10.1016/j.cell.2021.01.014"],
                    "id_type": "doi",
                    "relation_types": ["references"],
                    "max_results": 2
                }
            }
        ]

        success_count = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*15} 测试 {i} {'='*15}")
            print(f"测试: {test_case['name']}")
            print(f"参数: {json.dumps(test_case['params'], ensure_ascii=False, indent=2)}")

            try:
                response = send_mcp_request(
                    process,
                    "tools/call",
                    {
                        "name": "get_literature_relations",
                        "arguments": test_case["params"]
                    }
                )

                result = extract_mcp_result(response)

                if result.get("success", False):
                    print(f"✅ 测试 {i} 通过")
                    if "relations" in result:
                        relations = result["relations"]
                        total_refs = sum(len(relations.get(key, [])) for key in ["references", "similar", "citing"] if isinstance(relations.get(key), list))
                        print(f"   📊 找到 {total_refs} 条关系数据")
                    elif "processing_time" in result:
                        print(f"   ⏱️ 处理时间: {result['processing_time']}s")
                    success_count += 1
                else:
                    print(f"❌ 测试 {i} 失败")
                    print(f"   错误: {result.get('error', '未知错误')}")

                    # 检查是否是参数验证错误
                    error_msg = result.get('error', '').lower()
                    if 'validation error' in error_msg or 'missing argument' in error_msg:
                        print(f"   ⚠️ 这可能是参数验证问题")

            except Exception as e:
                print(f"❌ 测试 {i} 异常: {e}")

            time.sleep(2)  # 测试间隔

        # 总结
        print("\n" + "=" * 50)
        print(f"📊 测试结果:")
        print(f"✅ 成功: {success_count}/{len(test_cases)} 个测试")
        print(f"❌ 失败: {len(test_cases) - success_count}/{len(test_cases)} 个测试")

        success_rate = (success_count / len(test_cases)) * 100
        print(f"📈 成功率: {success_rate:.1f}%")

        if success_rate == 100:
            print("🎉 所有测试通过！参数修复成功。")
        elif success_rate >= 66:
            print("⚠️ 大部分测试通过，参数基本修复。")
        else:
            print("❌ 多个测试失败，参数修复不完整。")

        return success_rate >= 66

    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        return False
    finally:
        # 清理进程
        if 'process' in locals():
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print("✅ 服务器进程已停止")
            except:
                pass

if __name__ == "__main__":
    success = test_relation_params()
    sys.exit(0 if success else 1)