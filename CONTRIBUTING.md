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

### Automatic releases

Pushing to `main` runs the release workflow, including after merging `dev` locally
or merging a pull request on GitHub. It tests `main`, updates `wshell/__init__.py`,
commits the new version, and publishes a GitHub tag and release with generated
release notes.
Each release uses the highest change level among commits since the previous
stable release:

- `fix:` or `perf:` increments the patch version.
- `feat:` increments the minor version.
- `!` after the type or scope, or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer,
  increments the major version, including for versions below `1.0.0`.
- Other types, such as `docs:`, `chore:`, and `test:`, do not trigger a release.

Use a merge commit or rebase merge to preserve individual commit messages. With
squash merges, the final squash commit must use the appropriate Conventional
Commit message, including any breaking-change footer.

The workflow uses the built-in `GITHUB_TOKEN`; no separate secret is needed when
these writes are permitted. If branch rules require a different actor, set the
`RELEASE_TOKEN` repository secret to a token for an actor allowed to push the
version commit and tags. That token needs repository Contents read/write permission.
After a release, merge `main` back into `dev` to keep the version commit in sync.

To preview the next release locally without changing files, run:

```sh
python .github/scripts/prepare_release.py --dry-run
```

If publishing fails after the tag is pushed, rerun the failed workflow to finish
creating that release without another version bump.
You can also start the Release workflow manually from GitHub's Actions tab by
selecting Run workflow with `main` as the branch.
