import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexAR
import roman
from loguru import logger


class ARParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.h2_pattern_text = None

    def pre_process(self):

        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'head1': r'^Constitution\s+Of\s+The', 'ul': r'^PREAMBLE', 'head2': r'Article 1',
                                        'head4': '^Case Notes', 'ol_p': r'^\(\d\)', 'junk1': '^Annotations$',
                                        'head3': r'^§ \d', 'normalp': '^Editor\'s note'}
            self.h2_text_con: list = ['PROCLAMATION']

            self.h2_pattern_text_con = [r'^AMEND\. (?P<id>\d+)\.']

        else:
            self.tag_type_dict: dict = {'head1': r'TITLE \d', 'ul': r'^Subchapter 1 —', 'head2': 'Chapter 1',
                                        'head4': 'Research References',
                                        'head3': r'^\d+-\d+([a-z])?-\d+(\.\d+)?\. (?!Acts 19)', 'ol_p': r'^\([a-z]\)',
                                        'junk1': '^Annotations$', 'normalp': '^Publisher\'s Notes'}

            file_no = re.search(r'gov\.ar\.code\.title\.(?P<fno>\d+)\.html', self.input_file_name).group("fno")

            if file_no in ['02', '05', '06', '09', '12', '14', '15', '16', '17', '20', '23', '18', '26', '27',
                           '28']:
                self.h2_order: list = ['subtitle', 'chapter', 'subchapter', 'article', '', '', '']
            elif file_no in ['04']:
                self.h2_order: list = ['subtitle', 'chapter', 'subchapter', 'Part', '', '']
            elif file_no in ['01', '03', '07', '08', '10', '11', '13', '19', '21',
                             '22', '24', '25']:
                self.h2_order: list = ['chapter', 'subchapter', 'article', '', '']

            self.h2_text: list = ['Title 28 — Appendix Administrative Order Number 12 — Official Probate Forms',
                                  'APPENDIX — TITLE 10 SUNSET LAWS.',
                                  'APPENDIX — TITLE 19 BOND ISSUES']
            self.h3_pattern_text = [r'^(?P<id>\d\. Acts)', r'^(?P<id>\d+)\.']

            self.h2_pattern_text = [r'^(?P<tag>Part)\s*(?P<id>\d+)', r'^(?P<tag>Subpart)\s*(?P<id>\d+)']

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS',
                              'Case Notes', 'Research References', 'RESEARCH REFERENCES']

        self.watermark_text = """Release {0} of the Official Code of Arkansas Annotated released {1}. 
                Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on {2}. 
                This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexAR()

    def replace_tags_titles(self):

        case_note_id_list = []
        case_count = 1
        case_tag = None

        super(ARParseHtml, self).replace_tags_titles()

        for p_tag in self.soup.find_all():
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    if re.search(r'^—\w+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        inner_case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag["id"] = f'{case_tag.get("id")}-{tag_text}'

                    elif re.search(r'^— —\w+', p_tag.text.strip()):
                        pass
                    elif re.search(r'^— — —\w+', p_tag.text.strip()):
                        pass
                    elif re.search(r'^— — — —\w+', p_tag.text.strip()):
                        pass
                    else:
                        p_tag.name = "h5"
                        case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-casenote-{tag_text}'
                        if p_tag_id in case_note_id_list:
                            p_tag["id"] = f'{p_tag_id}.{case_count}'
                            case_count += 1
                        else:
                            p_tag["id"] = f'{p_tag_id}'
                            case_count = 1

                        case_note_id_list.append(p_tag_id)

                if p_tag.get("class") == [self.tag_type_dict["ol_p"]]:
                    if ar_tag := re.search(r'^ARTICLE (?P<id>[IVX]+)', p_tag.text.strip()):
                        p_tag.name = "h4"
                        p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-{ar_tag.group("id")}'

                    if re.search(r'^SECTION \d+\.', p_tag.text.strip()):
                        alpha_text = re.search(r'^(SECTION \d+\.)', p_tag.text.strip()).group()
                        num_text = re.sub(r'^SECTION \d+\.', '', p_tag.text.strip())
                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = alpha_text
                        new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                        p_tag.insert_before(new_p_tag)
                        p_tag.string = num_text

            elif p_tag.name == "h2" and p_tag.get("class") == "oneh2":
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def add_anchor_tags(self):
        super(ARParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.findAll("li", id=None):
            if part_tag := re.search(r'^(?P<tag>Part|Subpart)\s*(?P<id>\d+)', li_tag.text.strip()):
                chap_num = part_tag.group("id")
                self.c_nav_count += 1
                self.set_chapter_section_id(li_tag, chap_num,
                                            sub_tag=f'{part_tag.group("tag")}',
                                            prev_id=li_tag.find_previous("h2").get("id"),
                                            cnav=f'cnav{self.c_nav_count:02}')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        inner_sec_alpha = 'a'
        cap_alpha = 'A'
        inner_cap_alpha = 'A'
        num_count = 1
        inner_count = 1
        inner_num_count = 1
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        inner_num_ol = self.soup.new_tag("ol")
        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        roman_ol = self.soup.new_tag("ol", type="i")
        inner_cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
        inner_cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_alpha_ol = self.soup.new_tag("ol", type="a")
        roman_ol1 = self.soup.new_tag("ol", type="i")
        ol_count = 1
        cap_alpha_cur_tag = None
        roman_cur_tag = None
        sec_alpha_cur_tag = None
        inner_sec_alpha_cur_tag = None
        num_cur_tag = None
        inner_alpha = 'a'
        roman_cur_tag1 = None
        small_roman = 'i'
        small_roman1 = 'i'
        innumerate_cur_tag = None
        section_tag = None
        inner_num_cur_tag = None
        inner_num_id = None
        inner_sec_alpha_id = None
        prev_id1 = None
        sec_alpha_id = None
        inner_cap_alpha_id1 = None
        num_id = None
        cap_alpha_id = None
        inner_cap_alpha_id = None
        inner_cap_alpha_cur_tag = None
        inner_alpha_cur_tag = None
        num_id1 = None
        inner_alpha_id = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()
            if re.search(r'SECTION \d+\.', current_tag_text):
                section_tag = p_tag
            elif p_tag.name in ['h3', 'h4', 'h5']:
                section_tag = None

            if re.search(rf'^\({inner_count}\)', current_tag_text) \
                    and p_tag.name == "p" and inner_sec_alpha_cur_tag:

                p_tag.name = "li"
                innumerate_cur_tag = p_tag
                inner_cap_alpha = "A"

                if re.search(r'^\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if inner_sec_alpha_cur_tag:
                        inner_num_id = inner_sec_alpha_cur_tag.get('id')
                        inner_sec_alpha_cur_tag.append(inner_num_ol)

                else:
                    inner_num_ol.append(p_tag)

                p_tag["id"] = f'{inner_num_id}{inner_count}'
                p_tag.string = re.sub(rf'^\({inner_count}\)', '', current_tag_text)
                inner_count += 1

                if re.search(rf'^\([0-9]+\)\s*\(A\)', current_tag_text):
                    inner_cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([0-9]+\)\s*\(A\)', '', current_tag_text)
                    inner_cap_alpha_cur_tag1 = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[0-9]+)\)\s*\((?P<pid>A)\)', current_tag_text)
                    inner_cap_alpha_id1 = f'{innumerate_cur_tag.get("id")}'
                    li_tag["id"] = f'{innumerate_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    inner_cap_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_cap_alpha_ol1)
                    inner_cap_alpha = "B"

            elif re.search(rf'^\({inner_sec_alpha}\)', current_tag_text) \
                    and p_tag.name == "p" and (roman_cur_tag or roman_cur_tag1):

                p_tag.name = "li"
                inner_sec_alpha_cur_tag = p_tag
                inner_count = 1
                innumerate_cur_tag = None

                if re.search(r'^\(a\)', current_tag_text):
                    inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inner_sec_alpha_ol)
                    if roman_cur_tag1:
                        roman_cur_tag1.append(inner_sec_alpha_ol)
                        inner_sec_alpha_id = f"{roman_cur_tag1.get('id')}"
                    else:
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha_id = f"{roman_cur_tag.get('id')}"
                else:
                    inner_sec_alpha_ol.append(p_tag)
                if inner_sec_alpha in ["i", "v", "x"]:
                    p_tag["id"] = f'{inner_sec_alpha_id}-{inner_sec_alpha}'
                else:
                    p_tag["id"] = f'{inner_sec_alpha_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}\)', '', current_tag_text)
                inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)
                    num_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                    inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    inner_num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_num_ol)
                    inner_count = 2
                    inner_cap_alpha = 'B'

            elif re.search(rf'^\({small_roman}\)', current_tag_text):
                p_tag.name = "li"
                roman_cur_tag = p_tag
                inner_sec_alpha = 'a'
                inner_sec_alpha_cur_tag = None

                if re.search(r'^\(i\)', current_tag_text):
                    if re.search(r'^\(ii\)|^\([a-b]\)|^\(1\)|^\(A\)', p_tag.find_next_sibling("p").text.strip()):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        p_tag.wrap(roman_ol)

                        if cap_alpha_cur_tag:
                            cap_alpha_cur_tag.append(roman_ol)
                            prev_id1 = cap_alpha_cur_tag.get("id")
                        elif num_cur_tag:
                            num_cur_tag.append(roman_ol)
                            prev_id1 = num_cur_tag.get("id")
                        elif sec_alpha_cur_tag:
                            sec_alpha_cur_tag.append(roman_ol)
                            prev_id1 = sec_alpha_cur_tag.get("id")
                        elif inner_alpha_cur_tag:
                            inner_alpha_cur_tag.append(roman_ol)
                            prev_id1 = inner_alpha_cur_tag.get("id")
                        else:
                            prev_id1 = f'{p_tag.find_previous({"h3", "h4", "h2"}).get("id")}ol{ol_count}'

                        rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                        p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                        p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                        small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                    else:
                        p_tag.name = "li"
                        sec_alpha_cur_tag = p_tag
                        cap_alpha_cur_tag = None
                        num_cur_tag = None
                        roman_cur_tag = None
                        num_count = 1

                        sec_alpha_ol.append(p_tag)

                        p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                        p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                        if main_sec_alpha == 'z':
                            main_sec_alpha = 'a'
                        else:
                            main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                        ol_count += 1

                        if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                            num_ol = self.soup.new_tag("ol")
                            li_tag = self.soup.new_tag("li")
                            li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)

                            num_cur_tag = li_tag
                            cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                            num_id = f'{sec_alpha_cur_tag.get("id")}'
                            li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                            num_ol.append(li_tag)
                            p_tag.string = ""
                            p_tag.append(num_ol)
                            num_count = 2
                            cap_alpha = "A"

                            if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)', current_tag_text):
                                cap_alpha_ol = self.soup.new_tag("ol", type="A")
                                inner_li_tag = self.soup.new_tag("li")
                                cap_alpha_cur_tag = inner_li_tag
                                inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)', '', current_tag_text)
                                cur_tag = re.search(r'^\((?P<cid>[a-z])\)(\s)?\((?P<pid>1)\)\s?\((?P<nid>A)\)',
                                                    current_tag_text)
                                cap_alpha_id = f'{num_cur_tag.get("id")}'
                                inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                                cap_alpha_ol.append(inner_li_tag)
                                num_cur_tag.string = ""
                                num_cur_tag.append(cap_alpha_ol)
                                cap_alpha = "B"

                                if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', current_tag_text):
                                    roman_ol = self.soup.new_tag("ol", type="i")
                                    inner_li_tag = self.soup.new_tag("li")
                                    roman_cur_tag = inner_li_tag
                                    inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', '',
                                                                 current_tag_text)
                                    prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                                    inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                                    roman_ol.append(inner_li_tag)
                                    cap_alpha_cur_tag.string = ""
                                    cap_alpha_cur_tag.append(roman_ol)
                                    small_roman = "ii"

                        if re.search(rf'^\([a-z]+\)\s*\(i\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="i")
                            li_tag = self.soup.new_tag("li")
                            li_tag.string = re.sub(r'^\([a-z]+\)\s*\(i\)', '', current_tag_text)
                            roman_cur_tag = li_tag
                            cur_tag1 = re.search(r'^\((?P<cid>[a-z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                            prev_id1 = f'{sec_alpha_cur_tag.get("id")}'
                            li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                            roman_ol.append(li_tag)
                            p_tag.string = ""
                            p_tag.append(roman_ol)
                            small_roman = "ii"

                else:
                    roman_ol.append(p_tag)

                    rom_head = re.search(r'^\((?P<rom>[ivxl]+)\)', current_tag_text)
                    p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                    p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)

                    small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                if re.search(rf'^\([ivx]+\)\s*\(a\)', current_tag_text):
                    inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivxl]+\)\s*\(a\)', '', current_tag_text)
                    inner_sec_alpha_cur_tag = li_tag

                    inner_sec_alpha_id = f'{roman_cur_tag.get("id")}'
                    li_tag["id"] = f'{roman_cur_tag.get("id")}a'

                    inner_sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inner_sec_alpha_ol)
                    inner_sec_alpha = 'b'

                if re.search(rf'^\([ivx]+\)\s*\(a\)\s*\(1\)', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivxl]+\)\s*\(a\)\s*\(1\)', '', current_tag_text)
                    innumerate_cur_tag = li_tag

                    inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}1'
                    inner_num_ol.append(li_tag)
                    inner_sec_alpha_cur_tag.string = ""
                    inner_sec_alpha_cur_tag.append(inner_num_ol)

                    inner_count = 2

            elif re.search(rf'^\({inner_cap_alpha}\)', current_tag_text) and innumerate_cur_tag:
                p_tag.name = "li"

                if re.search(r'^\(A\)', current_tag_text):
                    inner_cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inner_cap_alpha_ol1)
                    innumerate_cur_tag.append(inner_cap_alpha_ol1)
                    inner_cap_alpha_id1 = f"{innumerate_cur_tag.get('id')}"

                else:
                    inner_cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{inner_cap_alpha_id1}{inner_cap_alpha}'
                p_tag.string = re.sub(rf'^\({inner_cap_alpha}\)', '', current_tag_text)
                if inner_cap_alpha == "Z":
                    inner_cap_alpha = 'A'
                else:
                    inner_cap_alpha = chr(ord(inner_cap_alpha) + 1)

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                cap_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None
                roman_cur_tag = None
                num_count = 1

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)

                    if num_cur_tag:
                        num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = f"{num_cur_tag.get('id')}"

                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"

                    elif inner_num_cur_tag:
                        inner_num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = f"{inner_num_cur_tag.get('id')}"

                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                if main_sec_alpha == 'z':
                    main_sec_alpha = 'a'
                else:
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                ol_count += 1
                num_cur_tag = None

                if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)

                    num_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                    num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(num_ol)
                    num_count = 2
                    cap_alpha = "A"

                    if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)', current_tag_text):
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        cap_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)\s*\((?P<nid>A)\)', current_tag_text)
                        cap_alpha_id = f'{num_cur_tag.get("id")}'

                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                        cap_alpha_ol.append(inner_li_tag)
                        num_cur_tag.string = ""
                        num_cur_tag.append(cap_alpha_ol)
                        cap_alpha = "B"
                        small_roman = 'i'

                        if re.search(rf'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="i")
                            inner_li_tag = self.soup.new_tag("li")
                            roman_cur_tag = inner_li_tag
                            inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)\s*\(A\)\s*\(i\)', '', current_tag_text)
                            prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                            inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                            roman_ol.append(inner_li_tag)
                            cap_alpha_cur_tag.string = ""
                            cap_alpha_cur_tag.append(roman_ol)
                            small_roman = "ii"

                if re.search(rf'^\([a-z]+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]+\)\s*\(i\)', '', current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[a-z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                    prev_id1 = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = "A"
                small_roman = 'i'
                roman_cur_tag = None
                cap_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    if sec_alpha_cur_tag:
                        num_id = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol)
                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")
                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"
                    else:
                        num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    num_ol.append(p_tag)

                p_tag["id"] = f'{num_id}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

                if re.search(rf'^\(\d+\)\s*\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>\d+)\)\s*\((?P<pid>A)\)', current_tag_text)
                    cap_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"
                    small_roman = 'i'

                    if re.search(rf'^\(\d+\)\s*\(A\)\s*\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        roman_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)\s*\(i\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>A)\)\s?\((?P<nid>i)\)',
                                            current_tag_text)
                        prev_id1 = f'{num_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}i'
                        roman_ol.append(inner_li_tag)
                        cap_alpha_cur_tag.string = ""
                        cap_alpha_cur_tag.append(roman_ol)
                        small_roman = "ii"

                    if re.search(rf'^\(\d+\)\s*\(A\)\s*\(i\)\s*\(a\)', current_tag_text):
                        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_sec_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)\s*\(i\)\s*\(a\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>A)\)\s?\((?P<nid>i)\)\s*\((?P<id>a)\)',
                                            current_tag_text)
                        inner_sec_alpha_id = f'{roman_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag.group("id")}'
                        inner_sec_alpha_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha = "b"

            elif re.search(r'^\([A-Z]\)\([A-Z]\)(\([A-Z]\))*', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_ol.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<cap>[A-Z])\)\((?P<cap1>[A-Z])\)(\((?P<cap2>[A-Z])\))*',
                                     current_tag_text)
                if p_tag_id.group("cap2"):
                    p_tag[
                        "id"] = f'{cap_alpha_id}{p_tag_id.group("cap")}{p_tag_id.group("cap1")}{p_tag_id.group("cap2")}'
                    p_tag.string = re.sub(rf'^\([A-Z]\)\([A-Z]\)', '', current_tag_text)
                elif p_tag_id.group("cap1"):
                    p_tag["id"] = f'{cap_alpha_id}{p_tag_id.group("cap")}{p_tag_id.group("cap1")}'
                    p_tag.string = re.sub(rf'^\([A-z]\)\([A-Z]\)(\([A-Z]\))', '', current_tag_text)

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                inner_sec_alpha = 'a'
                inner_sec_alpha_cur_tag = None
                roman_cur_tag = None
                small_roman = 'i'

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    if num_cur_tag:
                        num_cur_tag.append(cap_alpha_ol)
                        cap_alpha_id = num_cur_tag.get("id")
                    else:
                        cap_alpha_id = p_tag.find_previous("li").get("id")
                        p_tag.find_previous("li").append(cap_alpha_ol)
                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                if cap_alpha == "Z":
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

                if re.search(rf'^\([A-Z]+\)\s*\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)', '', current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[A-Z]+)\)\s*\((?P<pid>i)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"

                    if re.search(rf'^\([A-Z]+\)\s*\(i\)\s*\(a\)', current_tag_text):
                        inner_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_sec_alpha_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)\s*\(a\)', '', current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>[A-Z]+)\)(\s)?\((?P<pid>i)\)\s?\((?P<nid>a)\)',
                                            current_tag_text)
                        inner_sec_alpha_id = f'{cap_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{cap_alpha_cur_tag.get("id")}a'
                        inner_sec_alpha_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(inner_sec_alpha_ol)
                        inner_sec_alpha = 'b'

                    if re.search(rf'^\([A-Z]+\)\s*\(i\)\s*\(a\)\s*\(1\)', current_tag_text):
                        inner_num_ol = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        innumerate_cur_tag = inner_li_tag
                        inner_li_tag.string = re.sub(r'^\([A-Z]+\)\s*\(i\)\s*\(a\)\s*\(1\)', '', current_tag_text)
                        inner_num_id = f'{inner_sec_alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{inner_sec_alpha_cur_tag.get("id")}1'
                        inner_num_ol.append(inner_li_tag)
                        inner_sec_alpha_cur_tag.string = ""
                        inner_sec_alpha_cur_tag.append(inner_num_ol)
                        inner_count = 2

            elif re.search(rf'^{inner_cap_alpha}\. ', current_tag_text):
                p_tag.name = "li"
                inner_cap_alpha_cur_tag = p_tag
                inner_num_count = 1

                if re.search(r'^A\.', current_tag_text):
                    inner_cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inner_cap_alpha_ol)
                    if section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group(
                            "sid")
                        inner_cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"
                    else:
                        inner_cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    inner_cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inner_cap_alpha_id}{inner_cap_alpha}'
                p_tag.string = re.sub(rf'^{inner_cap_alpha}\.', '', current_tag_text)
                if inner_cap_alpha == "Z":
                    inner_cap_alpha = 'A'
                else:
                    inner_cap_alpha = chr(ord(inner_cap_alpha) + 1)

            elif re.search(rf'^{inner_num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_num_cur_tag = p_tag
                inner_alpha = "a"
                small_roman = 'i'

                if re.search(r'^1\.', current_tag_text):
                    inner_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inner_num_ol)
                    if inner_cap_alpha_cur_tag:
                        inner_cap_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = inner_cap_alpha_cur_tag.get('id')
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = cap_alpha_cur_tag.get('id')
                    elif inner_alpha_cur_tag:
                        inner_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = inner_alpha_cur_tag.get('id')
                    elif num_cur_tag:
                        num_cur_tag.append(inner_num_ol)
                        num_id1 = num_cur_tag.get('id')
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(inner_num_ol)
                        num_id1 = sec_alpha_cur_tag.get('id')
                    elif section_tag:
                        pvr_s_id = re.search(r'SECTION (?P<sid>\d+(\.\d+)*)\.', section_tag.text.strip()).group("sid")
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}s{pvr_s_id}ol{ol_count}"
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inner_num_ol.append(p_tag)

                p_tag["id"] = f'{num_id1}{inner_num_count}'
                p_tag.string = re.sub(rf'^{inner_num_count}\.', '', current_tag_text)
                inner_num_count += 1

            elif re.search(rf'^{inner_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inner_alpha_cur_tag = p_tag
                small_roman1 = "i"

                if re.search(r'^a\.', current_tag_text):
                    inner_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inner_alpha_ol)
                    inner_num_cur_tag.append(inner_alpha_ol)
                    inner_alpha_id = f"{inner_num_cur_tag.get('id')}"

                else:
                    inner_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inner_alpha_id}{inner_alpha}'
                p_tag.string = re.sub(rf'^{inner_alpha}\.', '', current_tag_text)
                inner_alpha = chr(ord(inner_alpha) + 1)

            elif re.search(rf'^{small_roman1}\. ', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                roman_cur_tag1 = p_tag
                inner_sec_alpha = 'a'

                if re.search(r'^i\.', current_tag_text):
                    roman_ol1 = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)

                    if inner_alpha_cur_tag:
                        inner_alpha_cur_tag.append(roman_ol1)
                        prev_id1 = inner_alpha_cur_tag.get("id")
                    else:
                        inner_num_cur_tag.append(roman_ol1)
                        prev_id1 = inner_num_cur_tag.get("id")
                else:
                    roman_ol1.append(p_tag)

                rom_head = re.search(r'^(?P<rom>[ivxl]+)\.', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(rf'^{small_roman1}\.', '', current_tag_text)
                small_roman1 = roman.toRoman(roman.fromRoman(small_roman1.upper()) + 1).lower()

            elif re.search(rf'^\({main_sec_alpha}{main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                cap_alpha_cur_tag = None
                num_cur_tag = None
                roman_cur_tag = None
                num_count = 1
                sec_alpha_ol.append(p_tag)
                p_tag.string = re.sub(rf'^\({main_sec_alpha}{main_sec_alpha}\)', '', current_tag_text)
                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}{main_sec_alpha}'
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

            if p_tag.name in ['h3', 'h4', 'h5'] or re.search(r'^SECTION \d+\.', current_tag_text):
                cap_alpha = 'A'
                cap_alpha_cur_tag = None
                num_count = 1
                ol_count = 1
                inner_count = 1
                inner_num_count = 1
                main_sec_alpha = 'a'
                inner_sec_alpha = 'a'
                inner_alpha = 'a'
                inner_cap_alpha = 'A'
                inner_alpha_cur_tag = None
                sec_alpha_cur_tag = None
                inner_sec_alpha_cur_tag = None
                innumerate_cur_tag = None
                inner_num_cur_tag = None
                num_cur_tag = None
                roman_cur_tag = None
                roman_cur_tag1 = None
                inner_cap_alpha_cur_tag = None

        logger.info("ol tags added")

    def create_analysis_nav_tag(self):
        super(ARParseHtml, self).create_case_note_analysis_nav_tag()
        logger.info("Case Note nav created")

    def replace_tags_constitution(self):

        super(ARParseHtml, self).replace_tags_constitution()

        case_count = 1
        case_note_id_list = []

        for tag in self.soup.find_all():
            if tag.get("class") == [self.tag_type_dict["head4"]] and not re.search(r'^Case Notes$', tag.text.strip()):
                if re.search(r'^—\w+', tag.text.strip()):
                    tag.name = "h5"
                    inner_case_tag = tag
                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                    tag["id"] = f'{case_tag.get("id")}-{tag_text}'

                elif re.search(r'^— —\w+', tag.text.strip()):
                    pass
                elif re.search(r'^— — —\w+', tag.text.strip()):
                    pass
                elif re.search(r'^— — — —\w+', tag.text.strip()):
                    pass
                else:
                    tag.name = "h5"
                    case_tag = tag
                    tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                    p_tag_id = f'{tag.find_previous({"h3", "h2", "h1"}).get("id")}-casenote-{tag_text}'
                    if p_tag_id in case_note_id_list:
                        tag["id"] = f'{p_tag_id}.{case_count}'
                        case_count += 1
                    else:
                        tag["id"] = f'{p_tag_id}'
                        case_count = 1

                    case_note_id_list.append(p_tag_id)

    def add_anchor_tags_con(self):
        super(ARParseHtml, self).add_anchor_tags_con()
        for li_tag in self.soup.find_all("li"):
            if not li_tag.get("id") and re.search(r'^AMEND\. \d+\.', li_tag.text.strip()):
                chap_num = re.search(r'^AMEND\. (?P<id>\d+)\.', li_tag.text.strip()).group("id")
                self.c_nav_count += 1
                self.set_chapter_section_id(li_tag, chap_num,
                                            sub_tag="-amd",
                                            prev_id=li_tag.find_previous("h2", class_="gen").get("id"),
                                            cnav=f'cnav{self.c_nav_count:02}')
