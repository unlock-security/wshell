# Contributing to WShell

We accept contributions of any kind, including bug reports, code patches, feature requests,
new input/output scripts or custom commands. You can help this project also by using the
development version of WShell and by reporting any bugs you might encounter.

## Reporting bugs

**It's important that you provide the full command argument list
as well as the output of the failing command.**

Use the `--log=debug` flag and copy&paste both the command and its output
to your bug report, e.g.:

```sh
$ wshell --log=debug <COMPLETE ARGUMENT LIST THAT TRIGGERS THE ERROR>
<COMPLETE OUTPUT>
```

## Contributing code

Before working on a new feature or a bug, please browse [existing issues](https://github.com/unlock-security/wshell/issues)
to see whether it has previously been discussed.

If your change alters WShell's behaviour or interface, it's a good idea to
discuss it before you start working on it.

If you are fixing an issue not yet reported, the first step should be to create a
new issue that documents the incorrect behaviour. That will also help you to build an
understanding of the issue at hand.

### Development environment

#### Getting the code

Go to <https://github.com/unlock-security/wshell> and fork the project repository.

```sh
# Clone your fork
$ git clone git@github.com:<your-username>/wshell.git

# Enter the project directory
$ cd wshell

# Enter the development branch
$ git checkout dev

# Create a branch for your changes
$ git checkout -b my_topical_branch
```

#### Setup

To get started, run the commands below:

```sh
# Creates an isolated Python virtual environment inside .venv
$ python3 -m virtualenv .venv

# Enter the Python virtual environment
$ source .venv/bin/activate

# installs all dependencies and also installs WShell
# (in editable mode so that the wshell command will point to your working copy).
$ pip install -e .
```

### Making changes

Please make sure your changes conform to [Style Guide for Python Code](https://python.org/dev/peps/pep-0008/) (PEP8).

### Submitting changes

When you open a Pull Request, please make sure to follow the following rules:

- Write a clear and descriptive title
- In the description, write a clear and detailed explanation of the changes
- There are no conflicts in merging your branch on `dev`
- If you are fixing a bug, please reference the issue number
