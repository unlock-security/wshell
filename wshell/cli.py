from base64 import b64decode
from binascii import Error as BinasciiError

import cmd2

from wshell.injectors import CommandInjector


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class WShellCmd(cmd2.Cmd):
    """ The wshell command loop shell """

    # Disable cmd2.Cmd advanced features we do not need (for now)
    del cmd2.Cmd.do__relative_run_script
    del cmd2.Cmd.do_run_pyscript
    del cmd2.Cmd.do_run_script
    del cmd2.Cmd.do_shortcuts
    del cmd2.Cmd.do_edit

    def __init__(
            self,
            injector: CommandInjector
    ):
        super().__init__(
            allow_cli_args=False,     # To avoid using URL and HTTP parameters from the command line as commands
            allow_redirection=False,  # Disable output redirection ('>', '>>' and '|') to forward it to the target
            allow_clipboard=False,    # Disable clipboard support (it may interfere with commands sent to the target)
            shortcuts={'?': 'help', '!': 'shell'}
        )

        # It seems that cmd2's alias and macro cannot be disabled at class level
        # due to some reference in the __init__() function
        del cmd2.Cmd.do_alias
        del cmd2.Cmd.do_macro

        self.injector = injector
        self.prompt = self.injector.get_prompt()

        # Command aliases
        self.do_exit = self.do_quit
        self.do_logout = self.do_quit


        # Overwrite `cat` (in Linux and Windows PSH) and `type` (in Windows CMD)
        # to get file content as base64 to avoid some issues when manipulating
        # the output (eg. escape \n)
        if self.injector.is_windows_cmd():
            self.do_type = self.base64_cat
            self.hidden_commands.append("type")
        else:
            self.do_cat = self.base64_cat
            self.hidden_commands.append("cat")

    def default(self, statement: cmd2.Statement) -> None:
        """ In case the user typed a non-builtin command, send it to the target. """
        self.history.append(statement)
        cmd_output = self.injector.execute(cmd=statement.raw)
        self.poutput(cmd_output)

    def emptyline(self) -> bool:
        """ Do nothing on empty command """

    def do_cd(self, line):
        """ Change directory command implementation """
        actual_directory = self.injector.change_directory(line)
        self.poutput(actual_directory)
        self.prompt = self.injector.get_prompt()

    def base64_cat(self, line):
        """ Print file content using base64 intermediate step """
        base64_output = self.injector.base64_cat(line)

        # If the output is a valid base64 we got file content, if not we encountered an error
        # (eg. no permission on the file, file not exists, etc.). In this cases we just print
        # the error message to the user.
        try:
            # Merge all the lines in one to avoid base64 validation errors
            self.poutput(b64decode("".join(base64_output.splitlines()), validate=True).decode(encoding='utf-8'))
        except BinasciiError:
            self.poutput(base64_output)
