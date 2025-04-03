from setuptools import setup

import wshell


def long_description():
    with open("README.rst", encoding="utf8") as f:
        return f.read()


setup(
    name='wshell',
    version=wshell.__version__,
    description=wshell.__doc__.strip(),
    long_description=long_description(),
    keywords="shell,webshell,command injection,security,ctf-tools,penetration testing,rce,remote code execution",
    url="https://github.com/unlock-security/wshell",
    project_urls={
        "Source Code": "https://github.com/unlock-security/wshell",
        "Issue Tracker": "https://github.com/unlock-security/wshell/issues"
    },
    download_url=f"https://github.com/unlock-security/wshell/archive/{wshell.__version__}.tar.gz",
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
    python_requires=">=3.5",
    install_requires=[
        "cmd2>=1.3",
        "requests>=2.24",
        "validator-collection>=1.4",
        "colorlog>=4.6",
        "platformdirs>=4.3.7"
    ],
    platforms=["posix"],
    classifiers=[
        "Development Status :: 3 - Alpha",
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
