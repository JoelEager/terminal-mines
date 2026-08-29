from setuptools import setup, find_packages

with open("README.md") as file:
    # Long description is the readme minus the header line and last section
    long_description = file.read()
    start = long_description.find("\n") + 1
    end = long_description.rfind("\n## ")
    long_description = long_description[start:end].strip()

setup(
    name="terminal-mines",
    version="1.5",
    python_requires="~=3.6",
    license="MIT",
    author="Joel Eager",
    description="A command-line clone of Minesweeper in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JoelEager/terminal-mines",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "click>=7.0",
    ],
    entry_points="""
        [console_scripts]
        mines=terminal_mines.main:main
    """,
    classifiers=[
        "Topic :: Games/Entertainment :: Puzzle Games",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows"
    ]
)
