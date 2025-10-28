#!/usr/bin/env python3
"""
版本同步工具

从pyproject.toml读取版本号，同步到所有相关文件。
这是最简单直接的版本管理方案。
"""

import re
import sys
from pathlib import Path


def get_version_from_pyproject():
    """从pyproject.toml获取版本号"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding='utf-8')
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    return match.group(1) if match else None


def update_file_content(file_path: Path, old_pattern: str, new_content: str):
    """更新文件内容"""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding='utf-8')

    # 使用正则表达式进行更精确的替换
    import re
    # 转义特殊字符
    escaped_pattern = re.escape(old_pattern)
    # 创建正则表达式，匹配版本号部分
    pattern = f'{escaped_pattern}["\'][^"\']*["\']'
    new_pattern = new_content

    new_content = re.sub(pattern, new_pattern, content)

    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        return True
    return False


def sync_version():
    """同步版本号到所有文件"""
    version = get_version_from_pyproject()
    if not version:
        print("❌ 无法获取版本号")
        return False

    print(f"🔄 同步版本号: {version}")

    # 定义文件更新规则
    updates = [
        # __init__.py文件
        (Path("src/article_mcp/__init__.py"),
         f'__version__ = "',
         f'__version__ = "{version}"'),

        # cli.py文件
        (Path("src/article_mcp/cli.py"),
         'FastMCP("Article MCP Server", version="',
         f'FastMCP("Article MCP Server", version="{version}"'),

        # config_resources.py文件
        (Path("src/article_mcp/resources/config_resources.py"),
         '"version": "',
         f'"version": "{version}"'),

        # tests/__init__.py文件
        (Path("tests/__init__.py"),
         f'__version__ = "',
         f'__version__ = "{version}"'),
    ]

    success_count = 0
    for file_path, old_start, new_content in updates:
        try:
            content = file_path.read_text(encoding='utf-8')
            # 查找包含旧模式的行
            lines = content.split('\n')
            updated = False
            new_lines = []

            for line in lines:
                if old_start in line and ('"' in line or '"' in line):
                    # 替换版本号
                    new_line = re.sub(rf'{re.escape(old_start)}["\'][^"\']*["\']', new_content, line)
                    new_lines.append(new_line)
                    updated = True
                else:
                    new_lines.append(line)

            if updated:
                file_path.write_text('\n'.join(new_lines), encoding='utf-8')
                print(f"✅ {file_path}")
                success_count += 1
            else:
                print(f"⚠️  {file_path}: 未找到版本号")
        except Exception as e:
            print(f"❌ {file_path}: {e}")

    print(f"📊 更新完成: {success_count}/{len(updates)} 个文件")
    return success_count > 0


def check_version():
    """检查版本号一致性"""
    version = get_version_from_pyproject()
    if not version:
        print("❌ 无法获取基准版本号")
        return False

    print(f"📦 基准版本: {version}")

    files_to_check = [
        ("src/article_mcp/__init__.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
        ("src/article_mcp/cli.py", r'version\s*=\s*["\']([^"\']+)["\']'),
        ("src/article_mcp/resources/config_resources.py", r'"version":\s*["\']([^"\']+)["\']'),
        ("tests/__init__.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
    ]

    all_consistent = True
    for file_path, pattern in files_to_check:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️  {file_path}: 文件不存在")
            continue

        try:
            content = path.read_text(encoding='utf-8')
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                file_version = match.group(1)
                if file_version == version:
                    print(f"✅ {file_path}: {file_version}")
                else:
                    print(f"❌ {file_path}: {file_version} (期望: {version})")
                    all_consistent = False
            else:
                print(f"⚠️  {file_path}: 未找到版本号")
                all_consistent = False
        except Exception as e:
            print(f"❌ {file_path}: {e}")
            all_consistent = False

    if all_consistent:
        print("✅ 所有文件版本号一致")
    return all_consistent


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  uv run python sync_version.py sync    # 同步版本号")
        print("  uv run python sync_version.py check   # 检查一致性")
        sys.exit(1)

    command = sys.argv[1]

    if command == "sync":
        success = sync_version()
        sys.exit(0 if success else 1)
    elif command == "check":
        success = check_version()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()