import re
# from bs4 import BeautifulSoup, Doctype, element
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns
import argparse
import os
import roman


class GAParseHtml(ParseHtml,RegexPatterns):

    def __init__(self):
        super().__init__()

        self.tag_type_dict: dict = {'head1': r'TITLE \d', 'ul': r'^Chap\.|^Art\.|^Sec\.',
                                    'head2': r'^CHAPTER \d|^ARTICLE \d|^Article \d',
                                    'head3': r'^(?P<title>\d+)-(?P<chapter>\d+([a-z])?)-(?P<section>\d+(\.\d+)?)',
                                    'head4': '^JUDICIAL DECISIONS|OPINIONS OF THE ATTORNEY GENERAL',
                                    'ol_p': r'^\([a-z]\)', 'junk': '^——————————', 'junk1': '^Annotations$',
                                    'normalp': '^Editor\'s note',
                                    'article': r'^Article \d$|^Part \d$'}

        self.h4_head: list = ['JUDICIAL DECISIONS', 'RESEARCH REFERENCES', 'OPINIONS OF THE ATTORNEY GENERAL']
        self.watermark_text = """Release {0} of the Official Code of Georgia Annotated released {1}. 
                Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on {2}. 
                This document is not subject to copyright and is in the public domain.
                """

    def generate_class_name_dict(self):
        if int(self.release_number) > 82:
            self.tag_type_dict['ul'] = r'^CHAPTER \d|^ARTICLE \d|^Article \d'

        super(GAParseHtml, self).generate_class_name_dict()

    def replace_tags_titles(self):

        super(GAParseHtml, self).replace_tags_titles()

        ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        for p_tag in self.soup.find_all("p"):
            if p_tag.get("class") in [[self.tag_type_dict["head2"]], [self.tag_type_dict["head3"]]]:
                if re.search(r'^APPENDIXRULES', p_tag.get_text().strip()):
                    p_tag.name = 'h2'
                    apdx_text = re.sub(r'\W+', '', p_tag.get_text().strip()).lower()
                    p_tag['id'] = f'{p_tag.find_previous("h1").get("id")}apr{apdx_text}'
                    p_tag['class'] = "apdxrules"

                elif re.search(r'^Rule \d+(-\d+-\.\d+)*(\s\(\d+\))*\.', p_tag.get_text().strip()):
                    p_tag.name = 'h2'
                    rule_id = re.search(r'^Rule (?P<r_id>\d+(-\d+-\.\d+)*(\s\(\d+\))*)\.',
                                        p_tag.get_text().strip()).group("r_id")
                    p_tag['id'] = f'{p_tag.find_previous("h2", class_="apdxrules").get("id")}r{rule_id.zfill(2)}'
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif p_tag.get("class") == [self.tag_type_dict["ul"]]:
                if self.rule_pattern.search(p_tag.text.strip()):
                    p_tag.name = "li"
                    p_tag.wrap(self.ul_tag)
                elif re.search(r'^APPENDIXRULES', p_tag.text.strip()):
                    p_tag.name = "li"
                    p_tag.find_previous("ul").append(p_tag)

            elif p_tag.get("class") == [self.tag_type_dict["junk"]]:
                if self.h2_article_pattern.search(p_tag.text.strip()):
                    p_tag["class"] = "navhead"
                    p_tag["id"] = f'{p_tag.find_previous("h2").get("id")}' \
                                       f'a{self.h2_article_pattern.search(p_tag.text.strip()).group("aid").zfill(2)}'
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})


    def add_anchor_tags(self):
        super(GAParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if re.search(r'^APPENDIXRULES', li_tag.text.strip()):
                    chap_num = re.sub(r'\W+', '', li_tag.text.strip()).lower()
                    sub_tag = 'apr'
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)

                elif self.rule_pattern.search(li_tag.text.strip()):
                    rule_num = self.rule_pattern.search(li_tag.text.strip()).group("rid")
                    sub_tag = 'r'
                    prev_id = li_tag.find_previous("h2", class_="apdxrules").get("id")
                    self.s_nav_count += 1
                    cnav = f'cnav{self.s_nav_count:02}'
                    self.set_chapter_section_id(li_tag, rule_num, sub_tag, prev_id, cnav)


            elif li_tag.name in ['h2', 'h3', 'h4']:
                self.a_nav_count = 0
                self.c_nav_count = 0
                self.p_nav_count = 0
                self.s_nav_count = 0

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
                    For each tag which has to be converted to orderd list(<ol>)
                    - create new <ol> tags with appropriate type (1, A, i, a ..)
                    - get previous headers id to set unique id for each list item (<li>)
                    - append each li to respective ol accordingly
                """
        main_sec_alpha = 'a'
        cap_alpha1 = 'A'
        ol_head = 1
        num_count = 1
        small_roman = "i"
        ol_count = 0
        inr_num_count = 1

        ol_terminator = None
        sec_alpha_cur_tag = None

        sec_alpha_ol = self.soup.new_tag("ol", type="a")

        for p_tag in self.soup.findAll():

            if p_tag.get("class") == [self.tag_type_dict['ol_p']]:
                current_tag_text = p_tag.text.strip()
                if p_tag.b:
                    p_tag.b.unwrap()
                if p_tag.i:
                    p_tag.i.unwrap()
                if p_tag.span:
                    p_tag.span.unwrap()

                if re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                    p_tag.name = "li"
                    sec_alpha_cur_tag = p_tag
                    num_count = 1
                    ol_terminator = 1
                    inr_num_count = 1
                    num_cur_tag1 = None

                    if re.search(r'^\(a\)', current_tag_text):
                        sec_alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(sec_alpha_ol)

                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        ol_count += 1

                    else:
                        sec_alpha_ol.append(p_tag)

                    p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                    p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)

                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                    if re.search(rf'^\([a-z]\)\s*\(1\)', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\([a-z]\)\s*\(1\)', '', current_tag_text)
                        num_cur_tag1 = li_tag
                        cur_tag1 = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>1)\)', current_tag_text)
                        num_id1 = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("cid")}'
                        li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag1.group("pid")}'
                        num_ol1.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(num_ol1)
                        num_count = 2

                        if re.search(rf'^\([a-z]\)\s*?\(\d+\)\s*?\(A\)', current_tag_text):
                            cap_alpha1_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            cap_alpha1_cur_tag = li_tag
                            inner_li_tag.string = re.sub(r'^\([a-z]\)\s*?\(\d+\)\s*?\(A\)', '', current_tag_text)
                            cur_tag = re.search(r'^\((?P<cid>[a-z])\)(\s)?\((?P<pid>\d+)\)\s\((?P<nid>A)\)',
                                                current_tag_text)
                            cap_alpha1_id = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                            inner_li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                            cap_alpha1_ol.append(inner_li_tag)
                            num_cur_tag1.string = ""
                            num_cur_tag1.append(cap_alpha1_ol)
                            cap_alpha1 = "B"

                elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                    p_tag.name = "li"
                    num_cur_tag1 = p_tag
                    cap_alpha1 = "A"
                    main_sec_alpha1 = 'a'
                    small_roman = "i"
                    ol_terminator = 1

                    if re.search(r'^\(1\)', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol1)

                        if sec_alpha_cur_tag:
                            num_id1 = sec_alpha_cur_tag.get('id')
                            sec_alpha_cur_tag.append(num_ol1)
                        else:
                            num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                    else:
                        num_ol1.append(p_tag)

                    p_tag["id"] = f'{num_id1}{num_count}'
                    p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                    num_count += 1

                    if re.search(rf'^\(\d+\)\s*\(A\)', current_tag_text):
                        cap_alpha1_ol = self.soup.new_tag("ol", type="A")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s*\(A\)', '', current_tag_text)
                        cap_alpha1_cur_tag = p_tag
                        cap_alpha = re.search(r'^\((?P<cid>\d+)\)\s*\((?P<pid>A)\)', current_tag_text)
                        cap_alpha1_id = f'{num_cur_tag1.get("id")}{cap_alpha.group("cid")}'
                        li_tag["id"] = f'{num_cur_tag1.get("id")}{cap_alpha.group("pid")}'
                        cap_alpha1_ol.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(cap_alpha1_ol)
                        cap_alpha1 = "B"

                elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p" and num_cur_tag1:
                    p_tag.name = "li"
                    cap_alpha1_cur_tag = p_tag
                    small_roman = "i"
                    ol_terminator = 1

                    if re.search(r'^\(A\)', current_tag_text):
                        cap_alpha1_ol = self.soup.new_tag("ol", type="A")
                        p_tag.wrap(cap_alpha1_ol)
                        num_cur_tag1.append(cap_alpha1_ol)
                        cap_alpha1_id = f"{num_cur_tag1.get('id')}ol{ol_count}"
                        ol_count += 1
                    else:
                        cap_alpha1_ol.append(p_tag)

                    p_tag["id"] = f'{cap_alpha1_id}{cap_alpha1}'
                    p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                    cap_alpha1 = chr(ord(cap_alpha1) + 1)

                    if re.search(rf'^\([A-Z]\)\s*\(i\)', current_tag_text):
                        smallroman_ol = self.soup.new_tag("ol", type="i")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\([A-Z]\)\s*\(i\)', '', current_tag_text)
                        roman_cur_tag = p_tag
                        cap_alpha = re.search(r'^\((?P<cid>[A-Z])\)\s*\((?P<pid>i)\)', current_tag_text)
                        prev_id1 = f'{cap_alpha1_cur_tag.get("id")}{cap_alpha.group("cid")}'
                        li_tag["id"] = f'{cap_alpha1_cur_tag.get("id")}{cap_alpha.group("pid")}'
                        smallroman_ol.append(li_tag)
                        p_tag.string = ""
                        p_tag.append(smallroman_ol)
                        small_roman = "ii"

                elif re.search(rf'^\({small_roman}\)', current_tag_text) and p_tag.name == "p":
                    p_tag.name = "li"
                    roman_cur_tag = p_tag
                    ol_terminator = 1

                    if re.search(r'^\(i\)', current_tag_text):
                        smallroman_ol = self.soup.new_tag("ol", type="i")
                        p_tag.wrap(smallroman_ol)

                        prev_id1 = p_tag.find_previous("li").get('id')
                        p_tag.find_previous("li").append(smallroman_ol)
                    else:
                        smallroman_ol.append(p_tag)

                    p_tag["id"] = f'{prev_id1}{small_roman}'
                    p_tag.string = re.sub(rf'^\({small_roman}\)', '', current_tag_text)
                    small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                elif re.search(rf'^{inr_num_count}\.', current_tag_text) and p_tag.name == "p":
                    p_tag.name = "li"
                    inr_num_tag = p_tag
                    ol_terminator = 1

                    if re.search(r'^1\.', current_tag_text):
                        inr_num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(inr_num_ol)

                        if sec_alpha_cur_tag:
                            inr_num_id = sec_alpha_cur_tag.get('id')
                            sec_alpha_cur_tag.append(inr_num_ol)
                        else:
                            inr_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                    else:
                        inr_num_ol.append(p_tag)

                    p_tag["id"] = f'{inr_num_id}{inr_num_count}'
                    p_tag.string = re.sub(rf'{inr_num_count}\.', '', current_tag_text)
                    inr_num_count += 1



                elif re.search(r'\(\d+\.\d+\)', current_tag_text):
                    num_cur_tag1.append(p_tag)
                    ol_terminator = 1

                elif ol_terminator and p_tag.name == "p":
                    # print(p_tag)
                    p_tag.find_previous("li").append(p_tag)

            elif p_tag.name in ['h3', 'h4', 'h5', 'p']:
                ol_head = 1
                main_sec_alpha = 'a'
                cap_alpha1 = "A"
                num_count = 1
                inr_num_count = 1
                small_roman = "i"

                sec_alpha_cur_tag = None
                ol_terminator = None
                num_cur_tag1 = None

        print('ol tags added')

    def create_analysis_nav_tag(self):
        super(GAParseHtml, self).create_judicial_decision_analysis_nav_tag()
        print("judicial decision nav created")

    def add_cite(self):
        self.cite_pattern = re.compile(r'\b(\d{1,2}-\d(\w+)?-\d+(\.\d+)?(\s?(\(\w+\))+)?)')
        cite_p_tags = []
        for tag in self.soup.findAll(lambda tag: re.search(r"§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                                           r"|\d+ Ga.( App.)? \d+"
                                                           r"|\d+ S.E.(2d)? \d+"
                                                           r"|\d+ U.S.C. § \d+(\(\w\))?"
                                                           r"|\d+ S\. (Ct\.) \d+"
                                                           r"|\d+ L\. (Ed\.) \d+"
                                                           r"|\d+ L\.R\.(A\.)? \d+"
                                                           r"|\d+ Am\. St\.( R\.)? \d+"
                                                           r"|\d+ A\.L\.(R\.)? \d+",
                                                           tag.get_text()) and tag.name == 'p'
                                                 and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            super(GAParseHtml, self).add_cite(tag)


GAParseHtml_obj = GAParseHtml()
GAParseHtml_obj.run_constitution()
GAParseHtml_obj.run_titles()
