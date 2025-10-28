#!/usr/bin/env python3
"""
精确测试 get_literature_relations 参数问题是否修复
"""

import subprocess
import json
import time
import sys

def test_parameter_validation():
    """测试参数验证问题是否修复"""
    print("🔍 精确测试 get_literature_relations 参数问题修复")
    print("=" * 60)

    # 启动服务器
    try:
        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "article_mcp", "server", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        time.sleep(3)

        # 初始化
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }

        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # 等待初始化响应
        init_response = ""
        start_time = time.time()
        while time.time() - start_time < 10:
            if process.poll() is not None:
                print(f"❌ 服务器初始化失败，返回码: {process.returncode}")
                return False

            line = process.stdout.readline()
            if line:
                init_response += line.strip()
                try:
                    parsed = json.loads(init_response)
                    if "result" in parsed:
                        print("✅ 服务器初始化成功")
                        break
                except json.JSONDecodeError:
                    continue

        # 测试 1: 使用 identifier 参数
        print("\n🧪 测试 1: 使用 identifier 参数")
        test1_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_literature_relations",
                "arguments": {
                    "identifier": "10.1016/j.cell.2021.01.014",
                    "id_type": "doi",
                    "relation_types": ["references"],
                    "max_results": 1
                }
            }
        }

        process.stdin.write(json.dumps(test1_request) + "\n")
        process.stdin.flush()

        # 读取测试1响应
        test1_response = ""
        start_time = time.time()
        timeout = 30

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                break

            line = process.stdout.readline()
            if line:
                test1_response += line.strip()
                try:
                    parsed = json.loads(test1_response)

                    # 检查是否有参数验证错误
                    print(f"🔍 完整响应: {json.dumps(parsed, indent=2, ensure_ascii=False)}")

                    if "error" in parsed:
                        error = parsed["error"]
                        error_str = str(error)
                        if "validation error" in error_str or "missing argument" in error_str:
                            print(f"❌ 测试 1 失败 - 仍有参数验证错误:")
                            print(f"   错误: {error}")
                            return False
                        else:
                            print(f"⚠️ 测试 1 有其他错误: {error}")
                    elif "result" in parsed:
                        result = parsed["result"]
                        if "content" in result:
                            content = result["content"][0]["text"]
                            try:
                                actual_result = json.loads(content)
                                if actual_result.get("success", False):
                                    print("✅ 测试 1 通过 - identifier 参数正常工作")
                                    break
                                else:
                                    print(f"❌ 测试 1 失败 - 功能错误: {actual_result.get('error', '未知错误')}")
                            except json.JSONDecodeError:
                                print("❌ 测试 1 失败 - 响应格式错误")
                                print(f"   内容: {content[:200]}...")
                        else:
                            print("❌ 测试 1 失败 - 响应格式不正确")
                    break
                except json.JSONDecodeError:
                    continue

        # 测试 2: 使用 identifiers 参数
        print("\n🧪 测试 2: 使用 identifiers 参数")
        test2_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_literature_relations",
                "arguments": {
                    "identifiers": "10.1016/j.cell.2021.01.014",
                    "id_type": "doi",
                    "relation_types": ["references"],
                    "max_results": 1
                }
            }
        }

        process.stdin.write(json.dumps(test2_request) + "\n")
        process.stdin.flush()

        # 读取测试2响应
        test2_response = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if process.poll() is not None:
                break

            line = process.stdout.readline()
            if line:
                test2_response += line.strip()
                try:
                    parsed = json.loads(test2_response)

                    if "error" in parsed:
                        error = parsed["error"]
                        error_str = str(error)
                        if "validation error" in error_str or "missing argument" in error_str:
                            print(f"❌ 测试 2 失败 - 仍有参数验证错误:")
                            print(f"   错误: {error}")
                        else:
                            print(f"⚠️ 测试 2 有其他错误: {error}")
                    elif "result" in parsed:
                        result = parsed["result"]
                        if "content" in result:
                            content = result["content"][0]["text"]
                            try:
                                actual_result = json.loads(content)
                                if actual_result.get("success", False):
                                    print("✅ 测试 2 通过 - identifiers 参数正常工作")
                                else:
                                    print(f"❌ 测试 2 失败 - 功能错误: {actual_result.get('error', '未知错误')}")
                            except json.JSONDecodeError:
                                print("❌ 测试 2 失败 - 响应格式错误")
                        else:
                            print("❌ 测试 2 失败 - 响应格式不正确")
                    break
                except json.JSONDecodeError:
                    continue

        print("\n" + "=" * 60)
        print("📊 参数验证测试完成")
        print("🔧 如果没有看到参数验证错误，说明修复成功！")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
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
            except:
                pass

if __name__ == "__main__":
    test_parameter_validation()