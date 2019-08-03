from setuptools import setup, find_packages

with open("README.md") as file:
    long_description = file.read()

setup(
    name="terminal-mines",
    version="0.1",
    python_requires="~=3.4",
    license="MIT",
    author="Joel Eager",
    description="A command-line clone of Minesweeper in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JoelEager/terminal-mines",
    packages=find_packages(),
    install_requires=[
        "click==7.0",
    ],
    entry_points="""
        [console_scripts]
        mines=terminal_mines.mines:main
    """,
    classifiers=[
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows"
    ]
)
