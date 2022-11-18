from setuptools import setup

setup(
    name="bet",
    version="0.1.0",
    packages=["bet"],
    install_requires=[
        "typer",
        "rich",
        "dynaconf",
    ],
)
