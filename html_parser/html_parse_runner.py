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
from bs4 import BeautifulSoup


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
            soup_obj = parser_obj(state_key, path, release_number, input_file_name).run()
            add_cite_to_file(soup_obj, state_key, release_number, input_file_name)

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
        future_list = []
        for file in file_list:
            release_number = re.search(r'(?P<r_num>\d+)$', os.path.dirname(file)).group("r_num")
            future_obj = executor.submit(parser_obj(state_key, file, release_number, os.path.basename(file)).run)
            future_list.append({future_obj: [os.path.basename(file), release_number]})

        for item in future_list:
            for future_obj in concurrent.futures.as_completed(item.keys()):
                try:
                    future_obj.result()
                    add_cite_to_file(future_obj.result(), state_key, item[future_obj][1], os.path.basename(item[future_obj][0]))
                except Exception as exc:
                    exception_on = f'{exc}\n------------------------\n' \
                                   f'{item[future_obj][0]}'
                    logging.exception(exception_on, traceback.format_exc())


def add_cite_to_file(soup_obj, state_key, release_number, input_file_name):
    id_dictionary = {}
    cite_parser_obj = getattr(importlib.import_module('regex_pattern'), f'CustomisedRegex{state_key}')()
    with open("header_ids.txt") as file:
        for line in file:
            (key, value) = line.split()
            id_dictionary[key] = value

    soup = BeautifulSoup(soup_obj, "html.parser")

    cite_p_tags = []
    for tag in soup.findAll(
            lambda tag: getattr(cite_parser_obj, "cite_tag_pattern").search(tag.get_text()) and tag.name == 'p'
                        and tag not in cite_p_tags):
        cite_p_tags.append(tag)
        text = str(tag)

        for match in set(x[0] for x in getattr(cite_parser_obj, "cite_pattern").findall(tag.text.strip())):
            inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>|<p.+>', '', text, re.DOTALL)
            id_reg = getattr(cite_parser_obj, "cite_pattern").search(match.strip())
            file_name = re.search(r'^(?P<name>.+\.)(?P<tid>\d+[.\w]*)\.html$', input_file_name.strip())
            title_id = file_name.group("tid").zfill(2)
            cite_title_id = id_reg.group("title").strip().zfill(2)

            for key in id_dictionary.keys():
                if re.search(rf'^{id_reg.group("cite")}$', key):
                    tag.clear()
                    if cite_title_id == title_id:
                        target = "_self"
                        a_id = f'#{id_dictionary[key]}'
                    else:
                        target = "_blank"
                        a_id = f'{file_name.group("name")}{cite_title_id}.html#{id_dictionary[key]}'

                    text = re.sub(fr'\s{re.escape(match)}',
                                  f' <cite class="ocak"><a href="{a_id}" target="{target}">{match}</a></cite>',
                                  inside_text, re.I)
                    tag.append(BeautifulSoup(text))

        for match in set(
                x for x in re.findall(r'N\.D\. LEXIS \d+',
                                      tag.get_text())):
            inside_text = re.sub(r'<p\sclass="\w\d+">|</p>|<b>|</b>|<p>', '', text, re.DOTALL)
            tag.clear()
            text = re.sub(re.escape(match), f'<cite class="nd_code">{match}</cite>', inside_text, re.I)
            tag.append(BeautifulSoup(text))

    soup_str = str(soup.prettify())
    with open(
            f"/home/mis/PycharmProjects/cic_code_framework/transforms_output/{state_key.lower()}/oc{state_key.lower()}"
            f"/r{release_number}/{input_file_name}", "w") as file:
        file.write(soup_str)

    print("cite added", input_file_name)


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
    f = open("header_ids.txt", "w")
    f.close()
