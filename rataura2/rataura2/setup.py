from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="rataura2",
    version="0.1.0",
    author="Alejandro Perez Malagon",
    author_email="your.email@example.com",
    description="A Livekit conversational agent with tools for EVE Online using directed graphs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alepmalagon/rataura2",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Livekit dependencies
        "livekit-agents[google,elevenlabs,openai,silero,deepgram,cartesia,turn-detector,rag,noise-cancellation]~=1.0rc",
        "livekit-api",
        
        # Database
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        
        # Graph management
        "networkx>=3.0",
        "matplotlib>=3.5.0",
        
        # Utilities
        "python-dotenv>=0.19.0",
        "loguru>=0.5.3",
    ],
    entry_points={
        "console_scripts": [
            "rataura2=rataura2.__main__:main",
        ],
    },
)

