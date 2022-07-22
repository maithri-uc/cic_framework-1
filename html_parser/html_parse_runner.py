"""
    - run this file with args state_key and path
    -  all the commandline args are mandatory
    - path can be given for single file, all files of single release and all files of state accordingly.
"""

import argparse
import concurrent
import glob
import importlib
import multiprocessing
import re
import traceback
from concurrent.futures import ProcessPoolExecutor
import os
import logging


def start_parsing(arguments):
    """
        - checking all arguments
        - checking the path and based on given path the files are parsed
        - files are parsed : single file , all files of particular release and
        all files of particular state.
    """

    cpu_count = multiprocessing.cpu_count()
    file_list = []
    state_key = arguments.state_key
    path = arguments.path
    run_after_release = arguments.run_after_release

    script = f'{state_key.lower()}_html_parser'
    class_name = f'{state_key}ParseHtml'
    parser_obj = getattr(importlib.import_module(script), class_name)

    if os.path.exists(path):  # validation for path
        if os.path.isfile(path):  # checking given path is file or not.
            input_file_name = os.path.basename(path)
            release_number = re.search(r'/r(?P<rid>\d+)', os.path.dirname(path)).group("rid")
            parser_obj(state_key, path, release_number, input_file_name).run()

        else:
            subdirectories_files = [x for x in glob.glob(f'{path}/**', recursive=True) if os.path.isfile(x)]
            if run_after_release:
                run_after_release = int(run_after_release)
                for file in subdirectories_files:
                    release_number = int(re.search(r'(?P<rnum>\d+)$', os.path.dirname(file)).group("rnum"))
                    if release_number >= run_after_release:
                        file_list.append(file)
            else:
                file_list += subdirectories_files
    else:
        logging.exception("Invalid path", f'{path}')

    with ProcessPoolExecutor(cpu_count) as executor:
        final_list = []
        for file in file_list:
            release_number = re.search(r'(?P<r_num>\d+)$', os.path.dirname(file)).group("r_num")
            f = executor.submit(parser_obj(state_key, file, release_number, os.path.basename(file)).run)
            # final_list.append({"":f:\\})

        for f in concurrent.futures.as_completed(final_list):
            try:
                f.result()
            except Exception as exc:
                exception_on = f'{exc}\n------------------------\n' \
                               f'{f}'
                logging.exception(exception_on, traceback.format_exc())


if __name__ == '__main__':
    """
        - Parse the command line args
        - set environment variables using parsed command line args
        - Call start parsing method with args as arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--state_key", help="State of which parser should be run", required=True, type=str)
    parser.add_argument("--path", help="file path which needs to be parsed", required=True, type=str)
    parser.add_argument("--run_after_release", help="particular files which needs to be parsed", type=str)
    args = parser.parse_args()
    start_parsing(args)
