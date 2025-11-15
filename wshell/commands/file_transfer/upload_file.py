import argparse
import base64
import math
import os

from cmd2 import with_argparser

from wshell import utils, validators
from wshell.commands import WShellCommandSet
from wshell.log import logger


class UploadFileCommandSet(WShellCommandSet):

    argument_parser = argparse.ArgumentParser(description="Upload local file")
    argument_parser.add_argument(
        "-l", "--local",
        metavar="FILENAME",
        required=True,
        help="Local file to upload",
        dest="local_filename"
    )
    argument_parser.add_argument(
        "-r", "--remote",
        metavar="FILENAME",
        help="Remote file where to store the uploaded file (default: current folder, same name as local)",
        dest="remote_filename"
    )
    chunk_size_group = argument_parser.add_mutually_exclusive_group()
    chunk_size_group.add_argument(
        "-c", "--chunk",
        metavar="SIZE",
        type=validators.positive_integer,
        default=1024,
        help="Size of the chunk to upload in bytes (default: %(default)s)",
        dest="chunk_size"
    )
    chunk_size_group.add_argument(
        "-n", "--no-chunk",
        action="store_false",
        help="Do not split into chunks",
        dest="use_chunks",
        default=True
    )

    @with_argparser(argument_parser)
    def do_upload(self, args) -> None:
        if args.remote_filename is None:
            args.remote_filename = os.path.basename(args.local_filename)

        try:
            file_size = os.path.getsize(args.local_filename)
            with open(args.local_filename, "rb") as local_file:
                if not args.use_chunks:
                    if file_size > 6000:
                        logger.warning("Uploading large files without chunking might fail due to command length limits.")
                    base64_encoded_content = base64.b64encode(local_file.read()).decode('utf-8')
                    self._dispatch("upload_file_content", args.remote_filename, base64_encoded_content)
                else:
                    total_chunks = math.ceil(file_size / args.chunk_size)
                    logger.info(f"Uploading {file_size} bytes as {total_chunks} chunks ({args.chunk_size} bytes each)")

                    # Ensure the remote file is empty before starting
                    self._dispatch("truncate_remote_file", args.remote_filename)

                    for chunk_index in range(total_chunks):
                        self._cmd.poutput(f"Uploading chunk {chunk_index + 1}/{total_chunks}", end="\r")
                        chunk = local_file.read(args.chunk_size)
                        base64_encoded_chunk = base64.b64encode(chunk).decode('utf-8')
                        self._dispatch("upload_chunk", args.remote_filename, base64_encoded_chunk)

            logger.info(f"File '{args.local_filename}' uploaded to '{args.remote_filename}'")
        except FileNotFoundError:
            logger.error(f"Local file not found: '{args.local_filename}'")
        except OSError as error:
            logger.error(f"Error accessing local file '{args.local_filename}': {error.strerror}")

    #
    # Linux implementation
    #

    def _linux_truncate_remote_file(self, filename: str) -> None:
        self._cmd.injector.execute(f"truncate -s 0 {filename}")

    def _linux_upload_file_content(self, filename: str, content: str) -> None:
        self._linux_upload_chunk(filename, content)

    def _linux_upload_chunk(self, filename: str, chunk: str) -> None:
        self._cmd.injector.execute(f"echo -n '{chunk}' | base64 -d >> {filename}")

    #
    # Windows PSH implementation
    #

    def _win_psh_truncate_remote_file(self, filename: str) -> None:
        self._cmd.injector.execute(f"Clear-Content {filename}")

    def _win_psh_upload_file_content(self, filename: str, content: str) -> None:
        self._cmd.injector.execute(f"[System.Convert]::FromBase64String('{content}') | Set-Content -Path {filename} -Encoding Byte -NoNewline")

    def _win_psh_upload_chunk(self, filename: str, chunk: str) -> None:
        filename = filename.strip("'\"")
        command = (
            f"$path = '{filename}'; "
            f"$bytes = [System.Convert]::FromBase64String('{chunk}'); "
            f"$fileStream = [System.IO.FileStream]::new($path, [System.IO.FileMode]::Append); "
            f"$fileStream.Write($bytes, 0, $bytes.Length); "
            f"$fileStream.Close()"
        )
        self._cmd.injector.execute(command)

    #
    # Windows CMD implementation
    #

    def _win_cmd_truncate_remote_file(self, filename: str) -> None:
        self._cmd.injector.execute(f"type nul > {filename}")

    def _win_cmd_upload_file_content(self, filename: str, content: str) -> None:
        self._win_cmd_upload_chunk(filename, content)
    
    def _win_cmd_upload_chunk(self, filename: str, chunk: str) -> None:
        temp_b64_filename = f"%TEMP%\\{utils.random_string()}"
        self._cmd.injector.execute(f"(echo {chunk})>{temp_b64_filename}")
        self._cmd.injector.execute(f"certutil -decode {temp_b64_filename} -append {filename} > nul && del {temp_b64_filename}")