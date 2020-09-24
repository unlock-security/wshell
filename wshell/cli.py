import cmd2
from typing import Union

from wshell import settings
from wshell.injectors import LinuxCommandInjector, WindowsCmdCommandInjector, WindowsPshCommandInjector


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class WShellCmd(cmd2.Cmd):
    """ The wshell command loop shell """

    # Disable cmd2.Cmd advanced features we do not need (for now)
    delattr(cmd2.Cmd, "do__relative_run_script")
    delattr(cmd2.Cmd, "do_run_pyscript")
    delattr(cmd2.Cmd, "do_run_script")
    delattr(cmd2.Cmd, "do_shortcuts")
    delattr(cmd2.Cmd, "do_py")

    def __init__(
            self,
            injector: Union[LinuxCommandInjector, WindowsCmdCommandInjector, WindowsPshCommandInjector],
            command_prompt: str = None
    ):
        super().__init__(
            allow_cli_args=False,     # To avoid using URL and HTTP parameters from the command line as commands
            allow_redirection=False,  # Disable output redirection ('>', '>>' and '|') to forward it to the target
            shortcuts={'?': 'help', '!': 'shell'}
        )

        self.injector = injector
        self.current_directory = self.injector.current_directory()

        if not command_prompt:
            self.prompt = self.injector.get_prompt()
        # Add an ending single blank space to the command prompt if not already present
        self.prompt = f"{self.prompt.strip()} "

    def default(self, statement: cmd2.Statement) -> None:
        """ In case the user typed a non-builtin command, send it to the target. """
        self.history.append(statement)
        cmd_output = self.injector.execute(cmd=statement.raw, directory=self.current_directory)
        self.poutput(cmd_output)

    def do_exit(self, line) -> bool:
        """ Exit from wshell """
        return True

    # noinspection PyPep8Naming
    def do_EOF(self, line) -> bool:
        """ Exit from wshell by pressing CTRL+D """
        self.poutput("^D")
        return True

    def emptyline(self) -> bool:
        """ Do nothing on empty command """

    def do_cd(self, line):
        """ Change directory command implementation """
        if line.startswith("."):
            # To make `cd .` and `cd ..` works we need to prepend the current directory
            line = f"{self.current_directory}{self.injector.PATH_DELIMITER}{line}"
        self.current_directory = self.injector.change_directory(line)
        self.poutput(self.current_directory)
