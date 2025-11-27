from setuptools import setup

import wshell


def long_description():
    with open("README.md", encoding="utf8") as f:
        return f.read()


setup(
    name='wshell',
    version="0.2.10-beta.0",
    description=wshell.__doc__.strip(), # pyright: ignore[reportOptionalMemberAccess]
    long_description=long_description(),
    long_description_content_type="text/markdown",
    keywords="shell,webshell,command injection,security,ctf-tools,penetration testing,rce,remote code execution",
    url="https://github.com/unlock-security/wshell",
    project_urls={
        "Source Code": "https://github.com/unlock-security/wshell",
        "Issue Tracker": "https://github.com/unlock-security/wshell/issues"
    },
    author="Francesco Marano (@mrnfrancesco)",
    author_email="francesco.marano@unlock-security.it",
    license="GPLv3",
    package_dir={"wshell": "wshell"},
    entry_points={
        "console_scripts": [
            "wshell = wshell.__main__:main"
        ],
    },
    data_files=[
        ("", ["LICENSE"]),
        ("data", ["data/user-agents.txt"]),
    ],
    python_requires=">=3.12",
    install_requires=[
        "cmd2==2.7.0",
        "requests==2.32.4",
        "validator-collection==1.5.0",
        "colorlog==6.10.1",
        "packaging==24.2",
        "platformdirs==4.5.0"
    ],
    platforms=["posix"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security"
        "Topic :: Terminals",
        "Topic :: Utilities",
    ]
)
