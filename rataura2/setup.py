from setuptools import setup, find_packages

setup(
    name="rataura2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy",
        "pydantic",
        "livekit",
        "networkx",
        "matplotlib",
    ],
    python_requires=">=3.8",
    description="Livekit 1.x project for AI conversational agents specialized in the EVE Online universe",
    author="alepmalagon",
    author_email="",
    url="https://github.com/alepmalagon/rataura2",
)

