"""
SAFE-MCP Client Package Setup
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="safe-mcp-client",
    version="1.0.0",
    author="SAFE-MCP Team",
    author_email="security@safe-mcp.org",
    description="Python client for SAFE-MCP Platform - Security for Model Context Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/safe-mcp-platform/safe-mcp-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "structlog>=23.1.0",
    ],
    entry_points={
        "console_scripts": [
            "safe-mcp-gateway=safe_mcp.gateway_client:main",
        ],
    },
    keywords="security mcp ai llm safety guardrails",
    project_urls={
        "Bug Reports": "https://github.com/safe-mcp-platform/safe-mcp-platform/issues",
        "Source": "https://github.com/safe-mcp-platform/safe-mcp-platform",
        "Documentation": "https://docs.safe-mcp.org",
    },
)

