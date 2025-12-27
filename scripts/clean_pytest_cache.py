#!/usr/bin/env python3
"""清理 pytest 残留的临时文件和目录

用法:
    python scripts/clean_pytest_cache.py          # 预览清理
    python scripts/clean_pytest_cache.py --clean  # 执行清理
"""

import argparse
import os
import sys
from pathlib import Path


def find_pytest_artifacts(root_dir: Path) -> dict[str, list[Path]]:
    """查找所有 pytest 残留文件和目录"""
    artifacts = {
        "pytest_fixture_dirs": [],
        "pytest_cache": [],
        "pycache": [],
        "__pycache__": [],
    }

    # 查找 pytest_fixture 目录
    for item in root_dir.iterdir():
        if item.is_dir() and str(item.name).startswith("<pytest_fixture"):
            artifacts["pytest_fixture_dirs"].append(item)

    # 查找其他常见的 pytest 缓存
    for item in root_dir.rglob(".pytest_cache"):
        if item.is_dir():
            artifacts["pytest_cache"].append(item)

    for item in root_dir.rglob("*.pyc"):
        artifacts["pycache"].append(item.parent)

    for item in root_dir.rglob("__pycache__"):
        if item.is_dir():
            artifacts["__pycache__"].append(item)

    return artifacts


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def calculate_size(paths: list[Path]) -> int:
    """计算目录或文件的总大小"""
    total = 0
    for path in paths:
        if path.is_dir():
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except OSError:
                        pass
        elif path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                pass
    return total


def main():
    parser = argparse.ArgumentParser(description="清理 pytest 残留文件")
    parser.add_argument("--clean", action="store_true", help="执行清理（默认只预览）")
    parser.add_argument(
        "--all", action="store_true", help="清理所有残留（包括 .pytest_cache 和 __pycache__）"
    )
    args = parser.parse_args()

    root_dir = Path.cwd()
    artifacts = find_pytest_artifacts(root_dir)

    print(f"📁 扫描目录: {root_dir}")
    print("=" * 60)

    total_size = 0
    total_count = 0

    # 显示 pytest_fixture 目录
    if artifacts["pytest_fixture_dirs"]:
        size = calculate_size(artifacts["pytest_fixture_dirs"])
        count = len(artifacts["pytest_fixture_dirs"])
        total_size += size
        total_count += count
        print(f"\n🧹 pytest_fixture 目录: {count} 个, {format_size(size)}")
        for d in artifacts["pytest_fixture_dirs"]:
            print(f"  - {d.name}")

    # 显示其他缓存（如果使用 --all）
    if args.all:
        if artifacts["pytest_cache"]:
            size = calculate_size(artifacts["pytest_cache"])
            count = len(artifacts["pytest_cache"])
            total_size += size
            total_count += count
            print(f"\n🧹 .pytest_cache 目录: {count} 个, {format_size(size)}")

        if artifacts["__pycache__"]:
            size = calculate_size(artifacts["__pycache__"])
            count = len(artifacts["__pycache__"])
            total_size += size
            total_count += count
            print(f"\n🧹 __pycache__ 目录: {count} 个, {format_size(size)}")

    print("\n" + "=" * 60)
    print(f"📊 总计: {total_count} 项, {format_size(total_size)}")

    if not args.clean:
        print("\n💡 预览模式。使用 --clean 参数执行实际清理。")
        print("   使用 --all 参数清理所有残留（包括缓存）")
        return

    # 执行清理
    if not artifacts["pytest_fixture_dirs"] and not args.all:
        print("\n✅ 没有需要清理的文件")
        return

    print("\n🚀 开始清理...")

    # 清理 pytest_fixture 目录
    for d in artifacts["pytest_fixture_dirs"]:
        try:
            import shutil

            shutil.rmtree(d)
            print(f"  ✓ 已删除: {d.name}")
        except Exception as e:
            print(f"  ✗ 删除失败 {d.name}: {e}")

    # 清理其他缓存（如果使用 --all）
    if args.all:
        for d in artifacts["pytest_cache"]:
            try:
                import shutil

                shutil.rmtree(d)
                print(f"  ✓ 已删除: {d.relative_to(root_dir)}")
            except Exception as e:
                print(f"  ✗ 删除失败 {d}: {e}")

        for d in artifacts["__pycache__"]:
            try:
                import shutil

                shutil.rmtree(d)
                print(f"  ✓ 已删除: {d.relative_to(root_dir)}")
            except Exception as e:
                print(f"  ✗ 删除失败 {d}: {e}")

    print(f"\n✅ 清理完成！释放了 {format_size(total_size)} 空间")


if __name__ == "__main__":
    main()
