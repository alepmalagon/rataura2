"""
Setup script for the rataura2 package.
"""
from setuptools import setup, find_packages

setup(
    name="rataura2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy",
        "pydantic",
        "business-rules",
        "networkx",
    ],
    author="alepmalagon",
    author_email="alepmalagon@example.com",
    description="A Livekit conversational agent with tools for EVE Online",
    keywords="livekit, conversational agent, eve online",
    python_requires=">=3.8",
)

