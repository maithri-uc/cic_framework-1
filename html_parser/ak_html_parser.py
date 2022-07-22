"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""

import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns, CustomisedRegexAK
import roman


class AKParseHtml(ParseHtml, RegexPatterns):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):

        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^The Constitution of the State|^CONSTITUTION OF THE UNITED STATES OF AMERICA',
                'ul': r'^Preamble', 'head2': '^Article I',
                'head4': '^Notes to Decisions', 'junk1': '^Text$',
                'head3': r'^Section \d\.|^§ \d\.', 'note_tag': '^Analysis'}
        else:
            self.tag_type_dict: dict = {'head1': r'Title \d+\.', 'ul': r'^Chapter \d+\.',
                                        'head2': r'^Chapter \d+\.',
                                        'head4': r'^History\.',
                                        'head3': r'^Sec\. \d+\.\d+\.\d+\.',
                                        'junk1': '^History$', 'NTD': '^Notes to Decisions'}

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS','Notes to Decisions']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']

        self.watermark_text = """Release {0} of the Official Code of Alaska Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
        """

        self.regex_pattern_obj = CustomisedRegexAK()
        self.h2_order: list = ['chapter', 'article', '', '', '']

    def replace_tags_titles(self):
        """
            - regex_pattern_obj  for customised regex class is created
            - h2_order list which has order of h2 tags created
            - calling method of base class
            - replacing all other tags which are not handled in the base class

        """
        super(AKParseHtml, self).replace_tags_titles()
        for p_tag in self.soup.find_all():
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["head2"]]:
                    p_tag.name = 'h2'
                    cur_tag_text = re.sub(r'\W+', '', p_tag.get_text().strip()).lower()
                    p_tag['id'] = f'{p_tag.find_previous("h2", class_="oneh2").get("id")}-{cur_tag_text}'

                elif p_tag.get("class") == [self.tag_type_dict["ul"]]:
                    p_tag.name = "li"
                    p_tag.wrap(self.ul_tag)

            elif p_tag.name == "h2" and p_tag.get("class") == "oneh2":
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to ordered list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers' id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        inner_sec_alpha = 'A'
        inner_num_count = 1
        ol_count = 1
        main_sec_alpha = 'a'
        small_roman = "i"

        sec_alpha_cur_tag = None
        inr_sec_alpha_cur_tag = None
        inr_num_cur_tag = None
        sec_alpha_id = None
        inr_num_id = None
        inr_sec_alpha_id = None
        small_roman_id = None

        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        inr_num_ol = self.soup.new_tag("ol")
        inr_sec_alpha_ol = self.soup.new_tag("ol", type="A")
        roman_ol = self.soup.new_tag("ol", type="i")

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                inner_num_count = 1
                inr_sec_alpha_cur_tag = None

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)

                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s\(1\)', current_tag_text):
                    p_tag.name = "li"
                    inr_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s\(1\)', '', current_tag_text)
                    inr_num_cur_tag = li_tag
                    inr_num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    inr_num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_num_ol)
                    inner_num_count = 2

            elif re.search(rf'^\({inner_num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_num_cur_tag = p_tag
                inner_sec_alpha = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    inr_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inr_num_ol)

                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(inr_num_ol)
                        inr_num_id = sec_alpha_cur_tag.get('id')
                    else:
                        inr_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    inr_num_ol.append(p_tag)

                p_tag["id"] = f'{inr_num_id}{inner_num_count}'
                p_tag.string = re.sub(rf'^\({inner_num_count}\)', '', current_tag_text)
                inner_num_count = inner_num_count + 1

                if re.search(rf'^\(\d+\)\s*\(A\)', current_tag_text):
                    p_tag.name = "li"
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)', '', current_tag_text)
                    inr_sec_alpha_cur_tag = li_tag
                    inr_sec_alpha_id = f'{inr_num_cur_tag.get("id")}'
                    li_tag["id"] = f'{inr_num_cur_tag.get("id")}A'
                    inr_sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_sec_alpha_ol)
                    inner_sec_alpha = 'b'
                    ol_head = 1

            elif re.search(rf'^\({inner_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_sec_alpha_cur_tag = p_tag
                ol_head = 1
                small_roman = "i"

                if re.search(r'^\(A\)', current_tag_text):
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inr_sec_alpha_ol)
                    if inr_num_cur_tag:
                        inr_num_cur_tag.append(inr_sec_alpha_ol)
                        inr_sec_alpha_id = inr_num_cur_tag.get('id')
                    else:
                        inr_sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inr_sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inr_sec_alpha_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}\)', '', current_tag_text)

                if inner_sec_alpha == 'Z':
                    inner_sec_alpha = 'A'
                else:
                    inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

                if re.search(r'^\([A-Z]\)\s*\(i\)', current_tag_text):
                    p_tag.name = "li"
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s*\(i\)', '', current_tag_text)
                    ol_head_cur_tag = li_tag
                    ol_head_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}i'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"

            elif re.search(rf'^\({inner_sec_alpha}{inner_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inr_sec_alpha_id}{inner_sec_alpha}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}{inner_sec_alpha}\)', '', current_tag_text)

                if inner_sec_alpha == 'Z':
                    inner_sec_alpha = 'A'
                else:
                    inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

            elif re.search(rf'^\({small_roman}\)', current_tag_text):
                p_tag.name = "li"
                rom_cur_tag = p_tag

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    if inr_sec_alpha_cur_tag:
                        inr_sec_alpha_cur_tag.append(roman_ol)
                        small_roman_id = inr_sec_alpha_cur_tag.get('id')
                    else:
                        sec_alpha_cur_tag.append(roman_ol)
                        small_roman_id = sec_alpha_cur_tag.get('id')
                else:
                    roman_ol.append(p_tag)

                p_tag["id"] = f'{small_roman_id}{small_roman}'
                p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

            if p_tag.name in ['h3', 'h4', 'h5']:
                inner_sec_alpha = 'A'
                inner_num_count = 1
                ol_count = 1
                main_sec_alpha = 'a'
                sec_alpha_cur_tag = None
                inr_sec_alpha_cur_tag = None
                inr_num_cur_tag = None

        print('ol tags added')

    def create_analysis_nav_tag(self):
        """
            - calling appropriate analysis nav method of base
            according to the header of analysis nav tag
        """

        rom = "I"

        if re.search('constitution', self.input_file_name):
            for case_tag in self.soup.find_all():
                if case_tag.name == "li" and case_tag.get("class") == "note":
                    if re.search(fr'^{rom}\.', case_tag.text.strip()):
                        rom_tag = case_tag
                        if re.search(r'^I\.', case_tag.text.strip()):
                            rom_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            case_tag.wrap(rom_ul)
                        else:
                            rom_ul.append(case_tag)

                        rom_num = re.sub(r'[\W\s]+','',case_tag.text.strip()).lower()
                        a_tag_id = f'#{case_tag.find_previous("h3").get("id")}-notestodecisions-{rom_num}'
                        rom_tag_id = f'#{case_tag.find_previous("h3").get("id")}-notestodecisions-{rom_num}'
                        rom = roman.toRoman(roman.fromRoman(rom.upper()) + 1)
                        alpha = "A"

                    elif re.search(fr'^{alpha}\.', case_tag.text.strip()):
                        alpha_tag = case_tag
                        if re.search(r'^A\.', case_tag.text.strip()):
                            alpha_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            case_tag.wrap(alpha_ul)
                            rom_tag.append(alpha_ul)
                        else:
                            alpha_ul.append(case_tag)

                        alpha_id = re.sub(r'[\W\s]+','', case_tag.text.strip().strip()).lower()
                        a_tag_id = f'{rom_tag_id}-{alpha_id}'
                        alpha = chr(ord(alpha) + 1)

                    elif re.search(r'^[0-9]+\.', case_tag.text.strip().strip()):
                        digit_tag = case_tag
                        if re.search(r'^1\.', case_tag.text.strip().strip()):
                            digit_ul = self.soup.new_tag("ul", **{"class": "leaders"})
                            case_tag.wrap(digit_ul)
                            alpha_tag.append(digit_ul)
                        else:
                            digit_ul.append(case_tag)

                        digit = re.search(r'^(?P<nid>[0-9]+)\.', case_tag.text.strip().strip()).group("nid")
                        a_tag_id = f'{alpha_tag.get("id")}-{digit}'

                    anchor = self.soup.new_tag('a', href=a_tag_id)
                    anchor.string = case_tag.text
                    case_tag.string = ''
                    case_tag.append(anchor)

                elif case_tag.name == "h5":
                    rom = "I"

            print("note to decision nav created")
        else:
            super(AKParseHtml, self).create_case_note_analysis_nav_tag()
            print("case note nav created")

    def add_cite(self):
        """
            - Call add_cite method of base class
            with file name and the tag which matches cite pattern

        """

        self.file_name = 'gov.ak.code.title.'
        cite_p_tags = []
        for self.tag in self.soup.findAll(
                lambda tag: re.search(
                    r'AS\s\d+\.\d+\.\d+((\([a-z]\))(\(\d+\))*)*|\d+ AAC \d+, art\. \d+\.|State v\. Yi, \d+ P\.\d+d \d+',
                    tag.get_text()) and tag.name == 'p'
                            and tag not in cite_p_tags):
            cite_p_tags.append(self.tag)
            super(AKParseHtml, self).add_cite()
        print("cite is added")

    def replace_tags_constitution(self):
        self.regex_pattern_obj = CustomisedRegexAK()
        super(AKParseHtml, self).replace_tags_constitution()

        note_to_decision_id_list:list = []

        for header_tag in self.soup.find_all("p"):
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^[IVX]+\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    NTD_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                    NTD_rom_head_id = f"{header_tag.find_previous('h4').get('id')}-{NTD_text}"

                    if NTD_rom_head_id in note_to_decision_id_list:
                        header_tag['id'] = f"{NTD_rom_head_id}.1"
                    else:
                        header_tag['id'] = f"{NTD_rom_head_id}"
                    note_to_decision_id_list.append(NTD_rom_head_id)

                elif re.search(r'^[A-Z]\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    NTD_alpha_text = re.sub(r'\W+', '', header_tag.text.strip()).lower()
                    NTD_alpha_head_id = f"{NTD_rom_head_id}-{NTD_alpha_text}"

                    if NTD_alpha_head_id in note_to_decision_id_list:
                        header_tag['id'] = f"{NTD_alpha_head_id}.1"
                    else:
                        header_tag['id'] = f"{NTD_alpha_head_id}"
                    note_to_decision_id_list.append(NTD_alpha_head_id)


