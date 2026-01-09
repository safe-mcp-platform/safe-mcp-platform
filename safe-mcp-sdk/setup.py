"""
Setup configuration for mcp-bastion-sdk
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-bastion-sdk",
    version="1.0.0",
    author="MCP-Bastion Team",
    description="Security SDK for MCP Server Developers - 1-line integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mcp-bastion-security/mcp-bastion-security",
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
    ],
    python_requires=">=3.9",
    install_requires=[
        # Minimal dependencies - most Python installs have these
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio"],
    },
)

