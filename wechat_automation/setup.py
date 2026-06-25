# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

setup(
    name="wechat-auto",
    version="0.1.0",
    description="微信桌面版自动化工具（Python + pywinauto）",
    author="",
    python_requires=">=3.7",
    packages=find_packages(exclude=("examples", "tests")),
    install_requires=[
        "pywinauto>=0.6.8",
        "pyperclip>=1.8.2",
        "comtypes>=1.1.14",
    ],
    extras_require={
        "win32": ["pywin32>=305"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
)
