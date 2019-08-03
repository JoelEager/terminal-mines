from setuptools import setup

setup(
    name="terminal-mines",
    version="0.1",
    py_modules=["mines"],
    install_requires=[
        "click==7.0",
    ],
    entry_points='''
        [console_scripts]
        mines=mines:main
    ''',
)
