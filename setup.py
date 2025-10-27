from setuptools import find_packages, setup

setup(
    name="article-mcp",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"": ["*.json"]},
    include_package_data=True,
    install_requires=[
        "fastmcp>=2.0.0",
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
        "urllib3>=1.26.0",
        "aiohttp>=3.9.0",
        "markdownify>=0.12.0",
    ],
    entry_points={
        "console_scripts": [
            "article-mcp=article_mcp.cli:main",
        ],
    },
    python_requires=">=3.10",
)
