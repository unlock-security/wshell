
import cmd2

from wshell import validators
from wshell.commands import load_commands
from wshell.commands.registry import command_registry
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
            injector: CommandInjector,
            persistent_history_file: str=''
    ):
        super().__init__(
            allow_cli_args=False,     # To avoid using URL and HTTP parameters from the command line as commands
            allow_redirection=False,  # Disable output redirection ('>', '>>' and '|') to forward it to the target
            allow_clipboard=False,    # Disable clipboard support (it may interfere with commands sent to the target)
            shortcuts={'?': 'help', '!': 'shell'},
            persistent_history_file=persistent_history_file
        )

        # It seems that cmd2's alias and macro cannot be disabled at class level
        # due to some reference in the __init__() function
        del cmd2.Cmd.do_alias
        del cmd2.Cmd.do_macro

        # Hide most of built-in settings (unused by wshell)
        interesting_settings = [ "debug", "timing" ]
        for setting in set(self.settables) - set(interesting_settings):
            self.remove_settable(setting)

        # Add wshell-specific settings
        self.add_settable(
            cmd2.Settable("timeout", validators.timeout, "Connection timeout in seconds (0 to disable)", injector)
        )

        self.injector = injector
        self.prompt = self.injector.get_prompt()

        # Command aliases
        self.do_exit = self.do_quit
        self.do_logout = self.do_quit

        # Hide alias and overridden commands from help menu
        self.hidden_commands.extend(["cd", "exit", "logout"])

        # Discover, validate, and load all modular commands
        load_commands()
        for command_set_class in command_registry.get_command_sets():
            self.register_command_set(command_set_class())

    def default(self, statement: cmd2.Statement) -> None:
        """ In case the user typed a non-builtin command, send it to the target. """
        self.history.append(statement)
        cmd_output = self.injector.execute(cmd=statement.raw)
        self.poutput(cmd_output)

    def emptyline(self) -> bool:
        """ Do nothing on empty command """
        return True

    def do_cd(self, line: str):
        """ Change directory command implementation """
        actual_directory = self.injector.change_directory(line)
        self.poutput(actual_directory)
        self.prompt = self.injector.get_prompt()
