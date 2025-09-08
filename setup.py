from setuptools import setup, find_packages

setup(
    name='article-mcp',
    version='0.2.0',
    packages=find_packages(),
    py_modules=['main'],
    package_data={'': ['*.json']},
    include_package_data=True,
    install_requires=[
        'fastmcp>=2.0.0',
        'requests>=2.25.0',
        'python-dateutil>=2.8.0',
        'urllib3>=1.26.0',
        'aiohttp>=3.9.0',
        'markdownify>=0.12.0',
    ],
    entry_points={
        'console_scripts': [
            'article-mcp=main:main',
        ],
    },
    python_requires='>=3.10',
)