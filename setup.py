from setuptools import find_packages, setup

setup(
    name="duxos-node-registry",
    version="0.1.0",
    description="Dux OS Node Registry Management CLI",
    long_description="""
    A comprehensive CLI tool for managing node registries in the Dux OS ecosystem.
    Features include:
    - Node registration and deregistration
    - Node health monitoring
    - Reputation tracking
    - Advanced filtering and listing
    """,
    author="Dux OS Team",
    author_email="support@duxos.org",
    url="https://duxos.org/node-registry",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "duxos-node-registry=duxos.registry.cli:main",
        ],
    },
    install_requires=[
        "argparse",
        "ipaddress",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
)
