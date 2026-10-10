from setuptools import setup, find_packages

setup(
    name="apex-agentic-memory",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "agentic-memory = apex_agentic_memory.cli:main",
        ],
    },
)
