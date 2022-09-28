"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""
import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexRI
import roman
from loguru import logger


class RIParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.alphabet = 'a'
        self.number = 1
        self.roman_number = 'i'
        self.inner_roman = 'i'
        self.caps_alpha = 'A'
        self.inner_num = 1
        self.caps_roman = 'I'
        self.inner_alphabet = 'a'
        self.inner_caps_roman = 'I'

    def pre_process(self):
        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES',
                'ul': r'^Preamble', 'head2': '^Article I',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_p': '^—', 'head4': r'Compiler’s Notes\.',
                'history': r'History of Section\.'}
            self.h2_order = ['article', '', '', '']
            self.h2_text_con: list = ['Articles of Amendment']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+[A-Z]?(\.\d+)?', 'ul': r'^Chapter \d+',
                                        'head2': r'^Chapter \d+', 'history': r'^History of Section\.',
                                        'head4': r'^Compiler’s Notes\.|^Repealed Sections\.',
                                        'head3': r'^\d+[A-Z]?(\.\d+)?-\d+-\d+',
                                        'junk1': '^Text|^Annotations', 'ol_of_p': r'^\([A-Z a-z0-9]\)'}
            self.file_no = re.search(r'gov\.ri\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if self.file_no in ['02', '31', '44', '07']:
                self.h2_order = ['chapter', 'part', '', '']
            elif self.file_no in ['06A']:
                self.h2_order = ['chapter', 'part', 'subpart', '']
            elif self.file_no in ['21', '42', '34']:
                self.h2_order = ['chapter', 'article', '', '']
            elif self.file_no in ['15', '23', '07']:
                self.h2_order = ['chapter', 'article', 'part', '']
            else:
                self.h2_order = ['chapter', '', '', '']
            if self.release_number == '73':
                if self.file_no in ['07']:
                    self.h2_order = ['chapter', 'article', 'part', 'subpart']
            self.h2_pattern_text: list = [r'^(?P<tag>C)hapters (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)']
        self.h4_head: list = ['Compiler’s Notes.', 'History of Section', 'Applicability.', 'Compiler\'s Notes.', 'Variations from Uniform Code.', 'Comparative Provisions.', 'Obsolete Sections.', 'Omitted Sections.', 'Reserved Sections.', 'Compiler\'s Notes', 'Cross References.', 'Subsequent Reenactments.', 'Abridged Life Tables and Tables of Work Life Expectancies.', 'Definitional Cross References.', 'Contingent Effective Dates.', 'Comparative Legislation.', 'Sunset Provision.', 'Liberal Construction.', 'Sunset Provisions.', 'Legislative Findings.', 'Contingently Repealed Sections.', 'Transferred Sections.', 'Collateral References.', 'NOTES TO DECISIONS', 'Retroactive Effective Dates.', 'Legislative Intent.', 'Repealed Sections.', 'Effective Dates.', 'Law Reviews.', 'Rules of Court.', 'OFFICIAL COMMENT', 'Superseded Sections.', 'Repeal of Sunset Provision.', 'Legislative Findings and Intent.', 'Official Comment.', 'Official Comments', 'Repealed and Reenacted Sections.', 'COMMISSIONER’S COMMENT', 'Comment.', 'History of Amendment.', 'Ratification.', 'Federal Act References.', 'Reenactments.', 'Severability.', 'Delayed Effective Dates.', 'Delayed Effective Date.', 'Delayed Repealed Sections.']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.watermark_text = """Release {0} of the Official Code of Rhode Island Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
                """
        self.regex_pattern_obj = CustomisedRegexRI()

    def recreate_tag(self, p_tag):
        new_tag = self.soup.new_tag("p")
        new_tag.string = p_tag.b.text
        new_tag['class'] = p_tag['class']
        p_tag.insert_before(new_tag)
        p_tag.string = re.sub(f'{p_tag.b.text}', '', p_tag.text.strip())
        return p_tag, new_tag

    def replace_tags_titles(self):
        super(RIParseHtml, self).replace_tags_titles()
        h4_count = 1
        h5count = 1
        note_to_decision_list: list = []
        note_to_decision_id: list = []
        case_tag = None
        inner_case_tag = None
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^NOTES TO DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["history"]]:
                            tag.name = "li"
                            tag["class"] = "note"
                            note_to_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and not re.search(r'Collateral References\.', tag.b.text):
                            tag.name = "h5"
                            tag_text = re.sub(r'\W+', '', tag.text.strip()).lower()
                            if tag.text.strip() in note_to_decision_list:
                                if re.search(r'^—\s*\w+', tag.text.strip()):
                                    inner_case_tag = tag
                                    p_tag_id = f'{case_tag.get("id")}-{tag_text}'
                                elif re.search(r'^— —\s*\w+', tag.text.strip()):
                                    p_tag_id = f'{inner_case_tag.get("id")}-{tag_text}'
                                else:
                                    p_tag_id = f'{tag.find_previous(["h3", "h2"]).get("id")}-notetodecision-{tag_text}'
                                    case_tag = tag
                            else:
                                p_tag_id = f'{tag.find_previous(["h3", "h2"]).get("id")}-notetodecision-{tag_text}'
                            if p_tag_id in note_to_decision_id:
                                tag["id"] = f'{p_tag_id}.{h5count:02}'
                                h5count += 1
                            else:
                                tag["id"] = f'{p_tag_id}'
                                h5count = 1
                            note_to_decision_id.append(p_tag_id)
                        elif tag.name in ["h2", "h3", "h4"]:
                            break
            elif p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["history"]]:
                    if re.search(r"^History of Section\.", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        id_of_tag = re.sub(r'\W+', '', new_tag.text.strip()).lower()
                        new_tag['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{id_of_tag}"
                    elif re.search('The Interstate Compact on Juveniles', p_tag.text.strip()):
                        p_tag.name = "h4"
                        id_of_tag = re.sub(r'\W+', '', p_tag.text).lower()
                        p_tag['id'] = f"{p_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{id_of_tag}"
                    elif re.search(r"^ARTICLE (\d+|[IVXCL]+)", p_tag.text.strip(), re.I):
                        if re.search(r"^ARTICLE [IVXCL]+\.?$", p_tag.text.strip(), re.I):
                            p_tag.name = "h4"
                            article_id = re.search(r"^ARTICLE (?P<article_id>[IVXCL]+)", p_tag.text.strip(), re.I).group('article_id')
                            p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_id}"
                        elif re.search(r"^ARTICLE [IVXCL]+[—.]?[A-Z\sa-z]+", p_tag.text.strip(), re.I):
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search('^(ARTICLE (?P<article_id>[IVXCL]+))', p_tag.text.strip(), re.I)
                            if p_tag.b:
                                tag_for_article.string = p_tag.b.text
                                tag_text = re.sub(fr'{p_tag.b.text}', '', p_tag.text.strip())
                            else:
                                tag_for_article.string = article_number.group()
                                tag_text = re.sub(fr'{article_number.group()}', '', p_tag.text.strip())
                            p_tag.insert_before(tag_for_article)
                            p_tag.clear()
                            p_tag.string = tag_text
                            tag_for_article.attrs['class'] = [self.tag_type_dict['history']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_id')}"
                        elif re.search(r'^Article \d+\.', p_tag.text.strip()):
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search(r'^(Article (?P<article_number>\d+)\.)', p_tag.text.strip())
                            tag_for_article.string = article_number.group()
                            p_tag.insert_before(tag_for_article)
                            p_tag.string = p_tag.text.replace(f'{article_number.group()}', '')
                            tag_for_article.attrs['class'] = [self.tag_type_dict['history']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_number')}"
                    elif re.search(r"^Section \d+\. [a-z ,\-A-Z]+\. \(a\)", p_tag.text.strip()) and re.search(r"^\(b\)", p_tag.find_next_sibling().text.strip()):
                        text_from_b = p_tag.text.split('(a)')
                        p_tag_for_section = self.soup.new_tag("p")
                        p_tag_for_section.string = text_from_b[0]
                        p_tag.string = f"{p_tag.text.strip().replace(f'{text_from_b[0]}', '')}"
                        p_tag.insert_before(p_tag_for_section)
                        p_tag_for_section.attrs['class'] = p_tag['class']
                    elif re.search(r'^Schedule [IVX]+', p_tag.text.strip()):
                        p_tag.name = "h4"
                        p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}sec{re.search(r'^Schedule (?P<schedule_id>[IVX]+)', p_tag.text.strip()).group('schedule_id')}"
                elif p_tag.get('class') == [self.tag_type_dict["head4"]]:
                    if re.search(r'^Cross References\.\s+[a-zA-Z0-9]+|^Compiler’s Notes\.\s+[a-zA-Z0-9]+|^Definitional Cross References[.:]\s+[“a-z A-Z0-9]+', p_tag.text.strip()) and p_tag.b:
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        header4_tag_text = re.sub(r'\W+', '', new_tag.text.strip()).lower()
                        h4_tag_id = f'{new_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'
                        if h4_tag_id in self.h4_cur_id_list:
                            new_tag['id'] = f'{h4_tag_id}.{h4_count:02}'
                            h4_count += 1
                        else:
                            new_tag['id'] = f'{h4_tag_id}'
                        self.h4_cur_id_list.append(h4_tag_id)
                    elif re.search(r'^Purposes( of Changes( and New Matter)?)?\. (\d+|\([a-z]\))', p_tag.text.strip()):
                        self.recreate_tag(p_tag)

    def split_tag(self, tag, split_attr, split_by):
        text_from_b = re.split(split_attr, tag.text.strip())
        p_tag = self.soup.new_tag("p")
        p_tag.string = f'{text_from_b[0]}{split_by}'
        tag.string = tag.text.replace(f'{text_from_b[0]}{split_by}', '')
        tag.insert_before(p_tag)
        p_tag.attrs['class'] = tag['class']

    @staticmethod
    def increment(text):
        if re.search('[ivx]+', text):
            text = roman.toRoman(roman.fromRoman(text.upper())+1).lower()
        elif re.search('[IVX]+', text):
            text = roman.toRoman(roman.fromRoman(text)+1)
        elif re.search('[a-zA-Z]', text):
            text = chr(ord(text) + 1)
        elif re.search(r'\d+', text):
            text = int(text) + 1
        return text

    def recreate_ol_tag(self):
        for tag in self.soup.main.find_all("p"):
            class_name = tag.get('class')[0]
            if class_name == self.tag_type_dict['history'] or class_name == self.tag_type_dict['ol_of_p'] or class_name == self.tag_type_dict['head4']:
                if re.search(r'^(\(([a-z\d]+)\)\s(\(\w\) )?)?.+?[:.]\s*\(\w\)', tag.text.strip()):
                    text = re.search(r'^(\((?P<text_1>([a-z\d]+))\)\s(\((?P<id>\w)\) )?)?.+?(?P<split_attr>[.:])\s*\((?P<text>\w)\)', tag.text.strip())
                    alpha = text.group('id')
                    split_attr = text.group('split_attr')
                    text_1 = text.group('text_1')
                    text = text.group('text')
                    text_string = text
                    text = self.increment(text)
                    if text_1:
                        text_1 = self.increment(text_1)
                    if text_1:
                        sibling_tag = tag.find_next_sibling(lambda next_tag: re.search(fr'^\({text}\)|^\({text_1}\)', next_tag.text.strip()) or next_tag.name == "h4")
                    else:
                        sibling_tag = tag.find_next_sibling()
                    next_tag = tag.find_next_sibling()
                    if next_tag.br:
                        next_tag = next_tag.find_next_sibling()
                    if re.search(fr'^\({text}\)', sibling_tag.text.strip()) and alpha != text_string and not re.search(fr'\({text_string}\)', next_tag.text.strip()):
                        self.split_tag(tag, fr'{split_attr}\s+\({text_string}\)', split_attr)
            elif tag.br and len(tag.text.strip()) == 0:
                tag.decompose()

    def initialize(self, ol_tag, cls_list):
        prev_tag = ol_tag.find_previous(["ol", "h3", "h4"], cls_list)
        if prev_tag.name != "ol":
            if cls_list[0] == "caps_alpha":
                self.caps_alpha = "A"
            elif cls_list[0] == "number":
                self.number = 1
            elif cls_list[0] == "inner_num":
                self.inner_num = 1
            elif cls_list[0] == "caps_roman":
                self.caps_roman = "I"
            elif cls_list[0] == "inner_caps_roman":
                self.inner_caps_roman = "I"
            elif cls_list[0] == "inner_roman":
                self.inner_roman = "i"
            elif cls_list[0] == "roman":
                self.roman_number = "i"
            elif cls_list[0] == "inner_alphabet":
                self.inner_alphabet = "a"

    def convert_paragraph_to_alphabetical_ol_tags(self):
        self.recreate_ol_tag()
        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
        ol_count = 1
        count_of_p_tag = 1
        prev_li = None
        for tag in self.soup.main.find_all(["h2", "h3", "h4", "p", "h5"]):
            if tag.i:
                tag.i.unwrap
            if tag['class'] == "text":
                continue
            next_tag = tag.find_next_sibling()
            if not next_tag:
                break
            if re.search(fr'^\([gk]\)', tag.text.strip()) and self.file_no == "19" and tag.find_previous_sibling().get('class') == "h3_part":
                self.alphabet = re.search(fr'^\((?P<alpha_id>[gk])\)', tag.text.strip()).group('alpha_id')
                if self.alphabet == "g":
                    start = 7
                else:
                    start = 11
                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a", start=start)
            if re.search(fr'^{self.number}\.', tag.text.strip()):
                prev_li = tag
                if self.number == 1:
                    ol_tag_for_number = self.soup.new_tag("ol")
                    ol_tag_for_number['class'] = "number"
                self.roman_number = 'i'
                self.inner_alphabet = 'a'
                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                tag.name = "li"
                tag.string = re.sub(fr'^{self.number}\.', '', tag.text.strip())
                tag['class'] = "number"
                if self.number != 1:
                    ol_tag_for_number.append(tag)
                else:
                    tag.wrap(ol_tag_for_number)
                self.initialize(ol_tag_for_number, ["caps_alpha", "section", "sub_section"])
                if self.caps_alpha != "A":
                    parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                    tag['id'] = f"{parent_tag.attrs['id']}{self.number}"
                elif ol_tag_for_alphabet.li:
                    parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    tag['id'] = f"{parent_tag.attrs['id']}{self.number}"
                else:
                    parent_tag = None
                    tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                if self.number == 1 and parent_tag:
                    parent_tag.append(ol_tag_for_number)
                self.number += 1
            elif re.search(fr'^{self.caps_alpha}{self.caps_alpha}?\.', tag.text.strip()):
                prev_li = tag
                if self.caps_alpha == "A":
                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                tag.name = "li"
                caps_alpha_id = re.search(fr'^(?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\.', tag.text.strip()).group('caps_alpha_id')
                tag.string = re.sub(fr'^{self.caps_alpha}{self.caps_alpha}?\.', '', tag.text.strip())
                tag['class'] = "caps_alpha"
                if re.search('[IVX]+', caps_alpha_id):
                    caps_alpha_id = f'-{caps_alpha_id}'
                else:
                    caps_alpha_id = self.caps_alpha
                if self.caps_alpha != "A":
                    ol_tag_for_caps_alphabet.append(tag)
                else:
                    tag.wrap(ol_tag_for_caps_alphabet)
                self.initialize(ol_tag_for_caps_alphabet, ["number", "section", "sub_section"])
                tag['id'] = f"{tag_id}ol{ol_count}{caps_alpha_id}"
                self.caps_alpha = chr(ord(self.caps_alpha) + 1)
            elif re.search(fr'^{self.inner_alphabet}\.', tag.text.strip()):
                if self.inner_alphabet == "a":
                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                    ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                prev_li = tag
                tag.name = "li"
                tag.string = re.sub(fr'^{self.inner_alphabet}\.', '', tag.text.strip())
                tag['class'] = "inner_alpha"
                if self.inner_alphabet != "a":
                    ol_tag_for_inner_alphabet.append(tag)
                else:
                    tag.wrap(ol_tag_for_inner_alphabet)
                self.initialize(ol_tag_for_inner_alphabet, ["roman", "section", "sub_section"])
                self.initialize(ol_tag_for_inner_alphabet, ["inner_num", "section", "sub_section"])
                if self.number != 1:
                    tag['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{self.inner_alphabet}'
                    if self.inner_alphabet == 'a':
                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
            elif re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()) and self.caps_roman != 'II':
                prev_li = tag
                self.inner_num = 1
                self.inner_roman = "i"
                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                ol_tag_for_inner_roman['class'] = "inner_roman"
                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                ol_tag_for_caps_roman['class'] = "caps_roman"
                self.caps_roman = "I"
                caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                if caps_alpha_id == "A":
                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                if re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\(i\)', tag.text.strip()):
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                    self.roman_number = "i"
                if re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.caps_roman}\)', tag.text.strip()):
                    if re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.caps_roman}\)\s?\({self.inner_alphabet}\)', tag.text.strip()):
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.caps_roman}\)\s?\({self.inner_alphabet}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_inner_alphabet)
                        li_tag_for_caps_alpha = self.soup.new_tag("li")
                        li_tag_for_caps_alpha['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                        li_tag_for_caps_roman = self.soup.new_tag("li")
                        li_tag_for_caps_roman['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{self.caps_roman}"
                        li_tag_for_caps_alpha['class'] = "caps_alpha"
                        tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{self.caps_roman}{self.inner_alphabet}"
                        tag['class'] = "inner_alpha"
                        li_tag_for_caps_roman['class'] = "caps_roman"
                        ol_tag_for_inner_alphabet.wrap(li_tag_for_caps_roman)
                        li_tag_for_caps_roman.wrap(ol_tag_for_caps_roman)
                        ol_tag_for_caps_roman.wrap(li_tag_for_caps_alpha)
                        if self.caps_alpha != "A":
                            ol_tag_for_caps_alphabet.append(li_tag)
                        else:
                            li_tag_for_caps_alpha.wrap(ol_tag_for_caps_alphabet)
                        if self.caps_alpha == 'A':
                            ol_tag_for_number.find_all('li', class_='number')[-1].append(ol_tag_for_caps_alphabet)
                        self.caps_roman = roman.toRoman(roman.fromRoman(self.caps_roman) + 1)
                        if self.caps_alpha == 'Z':
                            self.caps_alpha = 'A'
                        else:
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                    else:
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.caps_roman}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_caps_roman)
                        li_tag_for_caps_alpha = self.soup.new_tag("li")
                        li_tag_for_caps_alpha['class'] = "caps_alpha"
                        tag['class'] = "caps_roman"
                        ol_tag_for_caps_roman.wrap(li_tag_for_caps_alpha)
                        if self.caps_alpha != "A":
                            ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                        else:
                            li_tag_for_caps_alpha.wrap(ol_tag_for_caps_alphabet)
                        if self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                        else:
                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                        if self.caps_alpha == 'A':
                            parent_tag.append(ol_tag_for_caps_alphabet)
                        li_tag_for_caps_alpha['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}"
                        tag.attrs['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}-{self.caps_roman}"
                        self.caps_roman = roman.toRoman(roman.fromRoman(self.caps_roman) + 1)
                        if self.caps_alpha == 'Z':
                            self.caps_alpha = 'A'
                        else:
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                elif re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.inner_num}\)', tag.text.strip()):
                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                    ol_tag_for_inner_number['class'] = "inner_num"
                    self.caps_roman = "I"
                    tag.name = "li"
                    caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                    tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.inner_num}\)', '', tag.text.strip())
                    if re.search('[IVX]+', caps_alpha_id):
                        caps_alpha_id = f'-{caps_alpha_id}'
                    tag.wrap(ol_tag_for_inner_number)
                    li_tag_for_caps_alpha = self.soup.new_tag("li")
                    li_tag_for_caps_alpha['class'] = "caps_alpha"
                    tag['class'] = "inner_num"
                    ol_tag_for_inner_number.wrap(li_tag_for_caps_alpha)
                    if self.caps_alpha != "A":
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                    else:
                        li_tag_for_caps_alpha.wrap(ol_tag_for_caps_alphabet)
                    self.initialize(ol_tag_for_caps_alphabet, ["number", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_alphabet", "section", "sub_section"])
                    if self.roman_number != "i":
                        parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                    else:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    li_tag_for_caps_alpha['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}"
                    tag.attrs['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}{self.inner_num}"
                    if self.caps_alpha == 'A':
                        parent_tag.append(ol_tag_for_caps_alphabet)
                    if self.caps_alpha == 'Z':
                        self.caps_alpha = 'A'
                    else:
                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                    self.inner_num += 1
                elif re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.inner_roman}\)', tag.text.strip()):
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                    tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.inner_roman}\)', '', tag.text.strip())
                    if re.search('[IVX]+', caps_alpha_id):
                        caps_alpha_id = f'-{caps_alpha_id}'
                    tag.wrap(ol_tag_for_inner_roman)
                    li_tag_for_caps_alpha = self.soup.new_tag("li")
                    ol_tag_for_inner_roman.wrap(li_tag_for_caps_alpha)
                    li_tag_for_caps_alpha['class'] = "caps_alpha"
                    tag['class'] = "inner_roman"
                    if self.caps_alpha != "A":
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                    else:
                        li_tag_for_caps_alpha.wrap(ol_tag_for_caps_alphabet)
                    self.initialize(ol_tag_for_caps_alphabet, ["number", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_alphabet", "section", "sub_section"])
                    if self.number != 1:
                        li_tag_for_caps_alpha['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                        tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{self.inner_roman}"
                        if self.caps_alpha == 'A':
                            ol_tag_for_number.find_all('li', class_='number')[-1].append(ol_tag_for_caps_alphabet)
                    else:
                        li_tag_for_caps_alpha['id'] = f"{tag_id}ol{ol_count}{caps_alpha_id}"
                        tag['id'] = f"{tag_id}ol{ol_count}{caps_alpha_id}-{self.inner_roman}"
                    self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
                    if self.caps_alpha == 'Z':
                        self.caps_alpha = 'A'
                    else:
                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                elif re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.roman_number}\)', tag.text.strip()):
                    tag.name = "li"
                    caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                    if re.search('[IVX]+', caps_alpha_id):
                        caps_alpha_id = f'-{caps_alpha_id}'
                    tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.roman_number}\)', '', tag.text.strip())
                    tag.wrap(ol_tag_for_roman)
                    li_tag_for_caps_alpha = self.soup.new_tag("li")
                    li_tag_for_caps_alpha['class'] = "caps_alpha"
                    tag['class'] = "roman"
                    ol_tag_for_roman.wrap(li_tag_for_caps_alpha)
                    if self.caps_alpha != "A":
                        ol_tag_for_caps_alphabet.append(li_tag_for_caps_alpha)
                    else:
                        li_tag_for_caps_alpha.wrap(ol_tag_for_caps_alphabet)
                    self.initialize(ol_tag_for_caps_alphabet, ["number", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_alphabet", "section", "sub_section"])
                    if self.number != 1:
                        li_tag_for_caps_alpha['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}"
                        tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{caps_alpha_id}-{self.roman_number}"
                        if self.caps_alpha == 'A':
                            ol_tag_for_number.find_all('li', class_='number')[-1].append(ol_tag_for_caps_alphabet)
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    if self.caps_alpha == 'Z':
                        self.caps_alpha = 'A'
                    else:
                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                else:
                    if self.caps_alpha == "I" and re.search(r'^\(II\)', next_tag.text.strip()):
                        if re.search(fr'^\({self.caps_roman}\)', tag.text.strip()):
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.caps_roman}\)', '', tag.text.strip())
                            if self.caps_roman != "I":
                                ol_tag_for_caps_roman.append(tag)
                            else:
                                tag.wrap(ol_tag_for_caps_roman)
                            self.initialize(ol_tag_for_caps_roman, ["inner_roman", "section", "sub_section"])
                            self.initialize(ol_tag_for_caps_roman, ["roman", "section", "sub_section"])
                            self.initialize(ol_tag_for_caps_roman, ["inner_alphabet", "section", "sub_section"])
                            if self.inner_roman != "i":
                                parent_tag = ol_tag_for_inner_roman.find_all('li', class_='inner_roman')[-1]
                            elif self.caps_alpha != "A":
                                parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                            elif self.roman_number != "i":
                                parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                            elif self.number != 1:
                                parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                            if self.caps_roman == "I":
                                parent_tag.append(ol_tag_for_caps_roman)
                            tag['id'] = f"{parent_tag.attrs['id']}-{self.caps_roman}"
                            tag['class'] = "caps_roman"
                            self.inner_num = 1
                            self.caps_roman = roman.toRoman(roman.fromRoman(self.caps_roman) + 1)
                        else:
                            if self.inner_caps_roman == "I":
                                ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.inner_caps_roman}\)', '', tag.text.strip())
                            if ol_tag_for_inner_caps_roman.li:
                                ol_tag_for_inner_caps_roman.append(tag)
                            else:
                                tag.wrap(ol_tag_for_inner_caps_roman)
                            if self.roman_number != "i":
                                tag['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}-{self.inner_caps_roman}"
                                if self.inner_caps_roman == "I":
                                    ol_tag_for_roman.find_all('li', class_='roman')[-1].append(ol_tag_for_inner_caps_roman)
                            self.inner_caps_roman = roman.toRoman(roman.fromRoman(self.inner_caps_roman) + 1)
                    else:
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        caps_alpha_id = re.search(fr'^\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.string = re.sub(fr'^\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                        tag['class'] = "caps_alpha"
                        if self.caps_alpha != "A":
                            ol_tag_for_caps_alphabet.append(tag)
                        else:
                            tag.wrap(ol_tag_for_caps_alphabet)
                        self.initialize(ol_tag_for_caps_alphabet, ["number", "section", "sub_section"])
                        self.initialize(ol_tag_for_caps_alphabet, ["roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_caps_alphabet, ["inner_alphabet", "section", "sub_section"])
                        if self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                            tag['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}"
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                            tag['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}"
                        elif ol_tag_for_alphabet.li:
                            parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                            tag['id'] = f"{parent_tag.attrs['id']}{caps_alpha_id}"
                        else:
                            parent_tag = None
                            tag['id'] = f"{tag_id}ol{ol_count}{caps_alpha_id}"
                        if parent_tag and self.caps_alpha == "A":
                            parent_tag.append(ol_tag_for_caps_alphabet)
                        if self.caps_alpha == "Z":
                            self.caps_alpha = 'A'
                        else:
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        if re.search(r'^“\w+', next_tag.text.strip()) and re.search(fr'^\({self.roman_number}\)', next_tag.find_next_sibling().text.strip()) and self.roman_number != "i":
                            self.caps_alpha = 'A'
            elif re.search(fr'^\({self.caps_roman}\)|^\({self.inner_caps_roman}\)', tag.text.strip()):
                prev_li = tag
                if re.search(fr'^\({self.caps_roman}\)', tag.text.strip()):
                    if self.caps_roman == 'I':
                        ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                        ol_tag_for_caps_roman['class'] = "caps_roman"
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.caps_roman}\)', '', tag.text.strip())
                    if self.caps_roman != "I":
                        ol_tag_for_caps_roman.append(tag)
                    else:
                        tag.wrap(ol_tag_for_caps_roman)
                    self.initialize(ol_tag_for_caps_roman, ["inner_roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_roman, ["roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_roman, ["inner_alphabet", "section", "sub_section"])
                    self.inner_num = 1
                    if self.inner_roman != "i":
                        parent_tag = ol_tag_for_inner_roman.find_all('li', class_='inner_roman')[-1]
                    elif self.caps_alpha != "A":
                        parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                    elif self.roman_number != "i":
                        parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                    elif self.number != 1:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    if self.caps_roman == "I":
                        parent_tag.append(ol_tag_for_caps_roman)
                    tag['id'] = f"{parent_tag.attrs['id']}-{self.caps_roman}"
                    tag['class'] = "caps_roman"
                    self.caps_roman = roman.toRoman(roman.fromRoman(self.caps_roman) + 1)
                else:
                    if self.inner_caps_roman == "I":
                        ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.inner_caps_roman}\)', '', tag.text.strip())
                    if ol_tag_for_inner_caps_roman.li:
                        ol_tag_for_inner_caps_roman.append(tag)
                    else:
                        tag.wrap(ol_tag_for_inner_caps_roman)
                    if self.roman_number != "i":
                        tag['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}-{self.inner_caps_roman}"
                        if self.inner_caps_roman == "I":
                            ol_tag_for_roman.find_all('li', class_='roman')[-1].append(ol_tag_for_inner_caps_roman)
                    self.inner_caps_roman = roman.toRoman(roman.fromRoman(self.inner_caps_roman) + 1)
            elif re.search(fr'^\({self.inner_roman}\)', tag.text.strip()) and self.inner_roman != self.inner_alphabet and (self.caps_alpha != "A" or self.inner_num != 1 or self.roman_number != "i"):
                prev_li = tag
                if self.inner_roman == 'i':
                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_inner_roman['class'] = "inner_roman"
                tag.name = "li"
                tag.string = re.sub(fr'^\({self.inner_roman}\)', '', tag.text.strip())
                if self.inner_roman != "i":
                    ol_tag_for_inner_roman.append(tag)
                else:
                    tag.wrap(ol_tag_for_inner_roman)
                self.initialize(ol_tag_for_inner_roman, ["caps_roman", "section", "sub_section"])
                self.initialize(ol_tag_for_inner_roman, ["inner_num", "section", "sub_section"])
                self.initialize(ol_tag_for_inner_roman, ["inner_alphabet", "section", "sub_section"])
                tag['class'] = "inner_roman"
                if self.inner_alphabet != "a":
                    parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alpha')[-1]
                elif self.inner_num != 1:
                    parent_tag = ol_tag_for_inner_number.find_all('li', class_='inner_num')[-1]
                elif self.caps_roman != "I":
                    parent_tag = ol_tag_for_caps_roman.find_all('li', class_='caps_roman')[-1]
                elif self.caps_alpha != "A":
                    parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                elif self.roman_number != "i":
                    parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                if self.inner_roman == "i":
                    parent_tag.append(ol_tag_for_inner_roman)
                tag['id'] = f"{parent_tag.attrs['id']}-{self.inner_roman}"
                self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
                if re.search(fr'^\(i\)', next_tag.text.strip()):
                    self.inner_roman = 'i'
                    self.inner_num = 1
                    self.caps_alpha = "A"
                    self.number = 1
            elif re.search(fr'^\({self.roman_number}\)', tag.text.strip()) and (self.number != 1 or self.alphabet != self.roman_number) and self.inner_roman != self.inner_alphabet:
                prev_li = tag
                if self.roman_number == 'i':
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                self.inner_caps_roman = "I"
                self.inner_roman = "i"
                self.inner_num = 1
                if re.search(fr'^\({self.roman_number}\)\s?\(A\)', tag.text.strip()):
                    self.caps_alpha = "A"
                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                if re.search(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                    caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                    if re.search('[IVX]+', caps_alpha_id):
                        caps_alpha_id = f'-{caps_alpha_id}'
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                    tag['class'] = "caps_alpha"
                    tag.wrap(ol_tag_for_caps_alphabet)
                    li_tag = self.soup.new_tag("li")
                    li_tag['class'] = "roman"
                    ol_tag_for_caps_alphabet.wrap(li_tag)
                    if roman != "i":
                        ol_tag_for_roman.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_roman)
                    if self.number != 1:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    if self.roman_number == "i":
                        parent_tag.append(ol_tag_for_roman)
                    li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    tag.attrs['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{caps_alpha_id}"
                    self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["caps_roman", "section", "sub_section"])
                    if self.caps_alpha == 'Z':
                        self.caps_alpha = 'A'
                    else:
                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                else:
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.roman_number}\)', '', tag.text.strip())
                    if self.roman_number != "i":
                        ol_tag_for_roman.append(tag)
                    else:
                        tag.wrap(ol_tag_for_roman)
                    if re.search(fr'^\(A\)|^\({self.number}\)', next_tag.text.strip()):
                        self.caps_alpha = "A"
                    self.initialize(ol_tag_for_roman, ["caps_roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["number", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["caps_alpha", "section", "sub_section"])
                    tag['class'] = "roman"
                    if self.inner_alphabet != "a":
                        parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alpha')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    elif self.caps_roman != "I":
                        parent_tag = ol_tag_for_caps_roman.find_all('li', class_='caps_roman')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    elif self.number != 1:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    else:
                        parent_tag = None
                        tag['id'] = f"{tag_id}ol{ol_count}-{self.roman_number}"
                    if self.roman_number == "i" and parent_tag:
                        parent_tag.append(ol_tag_for_roman)
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    if re.search(fr'^\(i\)', next_tag.text.strip()):
                        self.roman_number = 'i'
                        self.number = 1
            elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)|^\({self.inner_alphabet}\)', tag.text.strip()) and (self.alphabet != "ii" or (self.inner_roman != "ii" and self.roman_number != "ii")):
                prev_li = tag
                if re.search(fr'^\({self.inner_alphabet}\)', tag.text.strip()) and self.inner_alphabet == self.alphabet:
                    sibling_of_alpha = tag.find_next_sibling(lambda sibling_tag: re.search(r'^\([1-9]\)|^\(ii\)|^History of Section\.', sibling_tag.text.strip()))
                    if ol_tag_for_alphabet.li and re.search(fr'^\(1\)', sibling_of_alpha.text.strip()):
                        self.inner_alphabet = "a"
                        self.number = 1
                if re.search(fr'^\({self.inner_alphabet}\)', tag.text.strip()) and (self.number != 1 or self.caps_alpha != "A" or self.inner_num != 1):
                    if self.inner_alphabet == "a":
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                    elif re.search(fr'^\({self.inner_alphabet}\)\s?\(i\)', tag.text.strip()):
                        self.roman_number = "i"
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_roman['class'] = "roman"
                    if re.search(fr'^\({self.inner_alphabet}\)\s?\({self.roman_number}\)', tag.text.strip()):
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_alphabet}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                        if self.roman_number != "i":
                            ol_tag_for_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_roman)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{self.inner_alphabet}"
                        li_tag['class'] = "inner_alpha"
                        tag.attrs['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{self.inner_alphabet}-{self.roman_number}'
                        tag['class'] = "roman"
                        ol_tag_for_roman.wrap(li_tag)
                        if self.inner_alphabet != "a":
                            ol_tag_for_inner_alphabet.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_inner_alphabet)
                        if self.inner_alphabet == "a":
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_inner_alphabet)
                        self.initialize(ol_tag_for_inner_alphabet, ["inner_num", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["inner_roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["caps_roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["caps_alpha", "section", "sub_section"])
                        self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                        self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                    else:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_alphabet}\)', '', tag.text.strip())
                        if self.inner_alphabet != "a":
                            ol_tag_for_inner_alphabet.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_alphabet)
                        self.initialize(ol_tag_for_inner_alphabet, ["inner_num", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["inner_roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["caps_roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["caps_alpha", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["roman", "section", "sub_section"])
                        if re.search(fr'^\(i\)', next_tag.text.strip()):
                            self.roman_number = "i"
                        if self.inner_roman != "i":
                            parent_tag = ol_tag_for_inner_roman.find_all('li', class_='inner_roman')[-1]
                        elif self.caps_roman != "I":
                            parent_tag = ol_tag_for_caps_roman.find_all('li', class_='caps_roman')[-1]
                        elif self.inner_num != 1:
                            parent_tag = ol_tag_for_inner_number.find_all('li', class_='inner_num')[-1]
                        elif self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                        if self.inner_alphabet == "a":
                            parent_tag.append(ol_tag_for_inner_alphabet)
                        tag['class'] = "inner_alpha"
                        tag.attrs['id'] = f"{parent_tag.attrs['id']}{self.inner_alphabet}"
                        self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                else:
                    alpha_id = re.search(fr'^\((?P<alpha_id>{self.alphabet}{self.alphabet}?)\)', tag.text.strip()).group('alpha_id')
                    if alpha_id == "a":
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    if re.search(fr'^\({self.alphabet}\)\s?\(', tag.text.strip()):
                        self.number = 1
                        self.roman_number = 'i'
                        self.inner_roman = 'i'
                        self.caps_alpha = 'A'
                        self.inner_num = 1
                        self.caps_roman = 'I'
                        self.inner_alphabet = 'a'
                        self.inner_caps_roman = 'I'
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_roman['class'] = "roman"
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_number['class'] = "number"
                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                        ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                    if re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)', tag.text.strip()):
                        if re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.roman_number}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{self.alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}"
                            li_tag_for_number['class'] = "number"
                            ol_tag_for_roman.wrap(li_tag_for_number)
                            li_tag_for_number.wrap(ol_tag_for_number)
                            ol_tag_for_number.wrap(li_tag_for_alphabet)
                            li_tag_for_alphabet.wrap(ol_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}-{self.roman_number}"
                            tag['class'] = "roman"
                            self.number += 1
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                        elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.inner_alphabet}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.inner_alphabet}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_inner_alphabet)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{self.alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}"
                            li_tag_for_number['class'] = "number"
                            ol_tag_for_inner_alphabet.wrap(li_tag_for_number)
                            li_tag_for_number.wrap(ol_tag_for_number)
                            ol_tag_for_number.wrap(li_tag_for_alphabet)
                            li_tag_for_alphabet.wrap(ol_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}-{self.inner_alphabet}"
                            tag['class'] = "inner_alpha"
                            self.number += 1
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                        elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            if re.search('[IVX]+', self.caps_alpha):
                                caps_alpha_id = f'-{self.caps_alpha}'
                            else:
                                caps_alpha_id = self.caps_alpha
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_caps_alphabet)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{self.alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}"
                            li_tag_for_number['class'] = "number"
                            ol_tag_for_caps_alphabet.wrap(li_tag_for_number)
                            li_tag_for_number.wrap(ol_tag_for_number)
                            ol_tag_for_number.wrap(li_tag_for_alphabet)
                            li_tag_for_alphabet.wrap(ol_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.number}{caps_alpha_id}"
                            tag['class'] = "caps_alpha"
                            self.number += 1
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        else:
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_number)
                            li_tag = self.soup.new_tag("li")
                            li_tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                            li_tag['class'] = "alphabet"
                            ol_tag_for_number.wrap(li_tag)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}{self.number}"
                            tag['class'] = "number"
                            li_tag.wrap(ol_tag_for_alphabet)
                            self.number += 1
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            sibling_tag = ol_tag_for_alphabet.find_next_sibling(lambda sib_tag: re.search(r'^“\(a\)|^\([a-z]\)|^History of Section\.', sib_tag.text.strip()))
                            if not re.search(r'^History of Section\.', sibling_tag.text.strip()) and not re.search(r'^“?\([avxi]\)', sibling_tag.text.strip()):#" matches inner_alphabet "(a) 23.html
                                self.alphabet = re.search(r'^\((?P<alpha>[a-z])\)', sibling_tag.text.strip()).group('alpha')
                    elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.roman_number}\)', tag.text.strip()) and not self.number != 1:
                        self.number = 1
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.roman_number}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_roman)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{tag_id}ol{ol_count}{self.alphabet}"
                        li_tag['class'] = "alphabet"
                        ol_tag_for_roman.wrap(li_tag)
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.alphabet}-{self.roman_number}"
                        tag['class'] = "roman"
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_alphabet)
                        self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                        self.alphabet = chr(ord(self.alphabet) + 1)
                    else:
                        if self.alphabet == "i" and re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)', next_tag.text.strip()):
                            sibling_of_i = tag.find_next_sibling(lambda sibling_tag: re.search(r'^\(ii\)|^History of Section\.', sibling_tag.text.strip()))
                            if re.search(r'^\(ii\)', sibling_of_i.text.strip()):
                                if self.roman_number == 'i':
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    ol_tag_for_roman['class'] = "roman"
                                    self.inner_caps_roman = "I"
                                    self.inner_roman = "i"
                                    self.inner_num = 1
                                if re.search(fr'^\({self.roman_number}\)\s?\(A\)', tag.text.strip()):
                                    self.caps_alpha = "A"
                                if re.search(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                                    caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                                    if re.search('[IVX]+', caps_alpha_id):
                                        caps_alpha_id = f'-{caps_alpha_id}'
                                    tag.name = "li"
                                    tag.string = re.sub(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                                    tag['class'] = "caps_alpha"
                                    tag.wrap(ol_tag_for_caps_alphabet)
                                    li_tag = self.soup.new_tag("li")
                                    if self.number != 1:
                                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                                    elif ol_tag_for_alphabet.li:
                                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                                    li_tag['class'] = "roman"
                                    li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                                    tag.attrs['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{caps_alpha_id}"
                                    if self.roman_number == "i":
                                        parent_tag.append(ol_tag_for_roman)
                                    ol_tag_for_caps_alphabet.wrap(li_tag)
                                    if self.caps_alpha == 'Z':
                                        self.caps_alpha = 'A'
                                    else:
                                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                                    li_tag.wrap(ol_tag_for_roman)
                                    self.initialize(ol_tag_for_roman, ["caps_roman", "section", "sub_section"])
                                    self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                                else:
                                    tag.name = "li"
                                    tag.string = re.sub(fr'^\({self.roman_number}\)', '', tag.text.strip())
                                    if self.roman_number != "i":
                                        ol_tag_for_roman.append(tag)
                                    else:
                                        tag.wrap(ol_tag_for_roman)
                                    self.initialize(ol_tag_for_roman, ["caps_roman", "section", "sub_section"])
                                    self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                                    self.initialize(ol_tag_for_roman, ["number", "section", "sub_section"])
                                    self.initialize(ol_tag_for_roman, ["caps_alpha", "section", "sub_section"])
                                    tag['class'] = "roman"
                                    if self.number != 1:
                                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                                    elif ol_tag_for_alphabet.li:
                                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                                    if self.roman_number == "i":
                                        parent_tag.append(ol_tag_for_roman)
                                    tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            else:
                                self.number = 1
                                self.roman_number = 'i'
                                self.inner_roman = 'i'
                                self.caps_alpha = 'A'
                                self.inner_num = 1
                                self.caps_roman = 'I'
                                self.inner_alphabet = 'a'
                                self.inner_caps_roman = 'I'
                                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)', '', tag.text.strip())
                                if ol_tag_for_alphabet.li:
                                    ol_tag_for_alphabet.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_alphabet)
                                tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                                if self.alphabet == "z":
                                    self.alphabet = 'a'
                                else:
                                    self.alphabet = chr(ord(self.alphabet) + 1)
                                tag['class'] = "alphabet"
                        else:
                            self.number = 1
                            self.roman_number = 'i'
                            self.inner_roman = 'i'
                            self.caps_alpha = 'A'
                            self.inner_num = 1
                            self.caps_roman = 'I'
                            self.inner_alphabet = 'a'
                            self.inner_caps_roman = 'I'
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)', '', tag.text.strip())
                            if ol_tag_for_alphabet.li and not ol_tag_for_alphabet.has_attr('start'):
                                ol_tag_for_alphabet.append(tag)
                            else:
                                tag.wrap(ol_tag_for_alphabet)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                            if self.alphabet == "z":
                                self.alphabet = 'a'
                            else:
                                self.alphabet = chr(ord(self.alphabet) + 1)
                            sibling_tag = ol_tag_for_alphabet.find_next_sibling(lambda sib_tag: re.search(r'^“\(a\)|^\([a-z]\)|^History of Section\.', sib_tag.text.strip()))
                            if not re.search(r'^History of Section\.', sibling_tag.text.strip()) and not re.search(r'^“?\([avxi]\)', sibling_tag.text.strip()):
                                self.alphabet = re.search(r'^\((?P<alpha>[a-z])\)', sibling_tag.text.strip()).group('alpha')
                            tag['class'] = "alphabet"
            elif re.search(fr'^\({self.number}\)|^\({self.inner_num}\)', tag.text.strip()):
                prev_li = tag
                if re.search(fr'^\({self.inner_num}\)', tag.text.strip()) and ((self.inner_num != self.number or (self.number == self.inner_num and self.number != 1)) or (self.roman_number != "i" or self.caps_alpha != "A")):
                    if self.inner_num == 1:
                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                        ol_tag_for_inner_number['class'] = "inner_num"
                    if re.search(fr'^\({self.inner_num}\)\s?\(i\)', tag.text.strip()):
                        self.inner_roman = "i"
                        ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_inner_roman['class'] = "inner_roman"
                    if re.search(fr'^\({self.inner_num}\)\s?\({self.inner_roman}\)', tag.text.strip()):
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_num}\)\s?\({self.inner_roman}\)', '', tag.text.strip())
                        if self.inner_roman != "i":
                            ol_tag_for_inner_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_roman)
                        self.initialize(ol_tag_for_inner_number, ["inner_alphabet", "section", "sub_section"])
                        tag['class'] = "inner_roman"
                        li_tag = self.soup.new_tag("li")
                        if self.caps_alpha != "A":
                            parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                        elif self.inner_alphabet != "a":
                            parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alpha')[-1]
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                        if self.inner_num == 1:
                            parent_tag.append(ol_tag_for_inner_number)
                        li_tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num}"
                        tag.attrs['id'] = f'{parent_tag.attrs["id"]}{self.inner_num}-{self.inner_roman}'
                        li_tag['class'] = "inner_num"
                        li_tag.append(ol_tag_for_inner_roman)
                        ol_tag_for_inner_number.append(li_tag)
                        self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
                        self.inner_num += 1
                    else:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_num}\)', '', tag.text.strip())
                        if self.inner_num != 1:
                            ol_tag_for_inner_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_number)
                        self.initialize(ol_tag_for_inner_number, ["inner_roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_number, ["inner_alphabet", "section", "sub_section"])
                        if re.search(r'^\w+', next_tag.text.strip()):
                            next_tag_alpha = next_tag.find_next_sibling()
                        else:
                            next_tag_alpha = next_tag
                        if re.search(fr'^\(a\)', next_tag_alpha.text.strip()):
                            self.inner_alphabet = "a"
                            self.inner_roman = "i"
                        if self.inner_roman != "i":
                            parent_tag = ol_tag_for_inner_roman.find_all('li', class_='inner_roman')[-1]
                        elif self.caps_roman != "I":
                            parent_tag = ol_tag_for_caps_roman.find_all('li', class_='caps_roman')[-1]
                        elif self.caps_alpha != "A":
                            parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                        elif self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                        elif self.inner_alphabet != "a":
                            parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alpha')[-1]
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                        if self.inner_num == 1:
                            parent_tag.append(ol_tag_for_inner_number)
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num}"
                        tag['class'] = "inner_num"
                        self.inner_num += 1
                else:
                    if self.number == 1:
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_number['class'] = "number"
                    self.roman_number = 'i'
                    self.inner_roman = "i"
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                    self.caps_roman = 'I'
                    self.inner_alphabet = 'a'
                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                    ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                    self.inner_num = 1
                    self.inner_caps_roman = 'I'
                    if re.search(fr'^\({self.number}\)\s?(\(i\)\s?)?\(A\)', tag.text.strip()):
                        self.caps_alpha = "A"
                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                        ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                    if re.search(fr'^\({self.number}\)\s?\({self.roman_number}\)', tag.text.strip()):
                        if re.search(fr'^\({self.number}\)\s?\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                            if re.search('[IVX]+', caps_alpha_id):
                                caps_alpha_id = f'-{caps_alpha_id}'
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_caps_alphabet)
                            tag['class'] = "caps_alpha"
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_roman = self.soup.new_tag("li")
                            li_tag_for_number['class'] = "number"
                            li_tag_for_roman['class'] = "roman"
                            ol_tag_for_caps_alphabet.wrap(li_tag_for_roman)
                            li_tag_for_roman.wrap(ol_tag_for_roman)
                            ol_tag_for_roman.wrap(li_tag_for_number)
                            li_tag_for_number.wrap(ol_tag_for_number)
                            if ol_tag_for_alphabet.li:
                                li_tag_for_number['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}"
                                li_tag_for_roman['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}-{self.roman_number}"
                                tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}-{self.roman_number}{caps_alpha_id}"
                                if self.number == 1:
                                    ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_number)
                            else:
                                li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.number}"
                                li_tag_for_roman['id'] = f"{tag_id}ol{ol_count}{self.number}-{self.roman_number}"
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}-{self.roman_number}{caps_alpha_id}"
                            self.number += 1
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            if self.caps_alpha == 'Z':
                                self.caps_alpha = 'A'
                            else:
                                self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        else:
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                            if self.roman_number != "i":
                                ol_tag_for_roman.append(tag)
                            else:
                                tag.wrap(ol_tag_for_roman)
                            li_tag = self.soup.new_tag("li")
                            li_tag['class'] = "number"
                            ol_tag_for_roman.wrap(li_tag)
                            tag['class'] = "roman"
                            if self.number != 1:
                                ol_tag_for_number.append(li_tag)
                            else:
                                li_tag.wrap(ol_tag_for_number)
                            if ol_tag_for_alphabet.li:
                                tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}-{self.roman_number}"
                                li_tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}"
                                if self.number == 1:
                                    ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_number)
                            else:
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}-{self.roman_number}"
                                li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                            self.initialize(ol_tag_for_number, ["caps_alpha", "section", "sub_section"])
                            self.number += 1
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    elif re.search(fr'^\({self.number}\)\s?\({self.inner_alphabet}\)', tag.text.strip()):
                        if re.search(fr'^\({self.number}\)\s?\({self.inner_alphabet}\)\s?\({self.roman_number}\)', tag.text.strip()):
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.inner_alphabet}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_inner_alphabet = self.soup.new_tag("li")
                            li_tag_for_inner_alphabet['id'] = f"{tag_id}ol{ol_count}{self.number}{self.inner_alphabet}"
                            li_tag_for_inner_alphabet['class'] = "inner_alpha"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{self.inner_alphabet}-{self.roman_number}"
                            ol_tag_for_roman.wrap(li_tag_for_inner_alphabet)
                            li_tag_for_inner_alphabet.wrap(ol_tag_for_inner_alphabet)
                            ol_tag_for_inner_alphabet.wrap(li_tag_for_number)
                            if self.number != 1:
                                ol_tag_for_number.append(li_tag_for_number)
                            else:
                                li_tag_for_number.wrap(ol_tag_for_number)
                            tag['class'] = 'roman'
                            self.number += 1
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                        else:
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.inner_alphabet}\)', '', tag.text.strip())
                            if self.inner_alphabet != "a":
                                ol_tag_for_inner_alphabet.append(tag)
                            else:
                                tag.wrap(ol_tag_for_inner_alphabet)
                            li_tag = self.soup.new_tag("li")
                            li_tag['class'] = "number"
                            ol_tag_for_inner_alphabet.wrap(li_tag)
                            tag['class'] = "inner_alpha"
                            if self.number != 1:
                                ol_tag_for_number.append(li_tag)
                            else:
                                li_tag.wrap(ol_tag_for_number)
                            if ol_tag_for_alphabet.li:
                                li_tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}"
                                tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.number}{self.inner_alphabet}"
                                if self.number == 1:
                                    ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_number)
                            else:
                                li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{self.inner_alphabet}"
                            self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                            self.number += 1
                    elif re.search(fr'^\({self.number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        caps_alpha_id = re.search(fr'\((?P<caps_alpha_id>{self.caps_alpha}{self.caps_alpha}?)\)', tag.text.strip()).group('caps_alpha_id')
                        if re.search('[IVX]+', caps_alpha_id):
                            caps_alpha_id = f'-{caps_alpha_id}'
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '', tag.text.strip())
                        tag['class'] = "caps_alpha"
                        li_tag = self.soup.new_tag("li")
                        tag.wrap(ol_tag_for_caps_alphabet)
                        if ol_tag_for_alphabet.li:
                            li_tag['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.number}'
                            tag.attrs['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.number}{caps_alpha_id}'
                            if self.number == 1:
                                ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_number)
                        else:
                            li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{caps_alpha_id}"
                        li_tag['class'] = "number"
                        ol_tag_for_caps_alphabet.wrap(li_tag)
                        if self.caps_alpha == 'Z':
                            self.caps_alpha = 'A'
                        else:
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        if self.number != 1:
                            ol_tag_for_number.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_number)
                        self.number += 1
                    else:
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.number}\)', '', tag.text.strip())
                        tag['class'] = "number"
                        if self.number != 1:
                            ol_tag_for_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_number)
                        if re.search(r'^\(A\)', next_tag.text.strip()):
                            self.caps_alpha = "A"
                        self.initialize(ol_tag_for_number, ["caps_alpha", "section", "sub_section"])
                        if ol_tag_for_alphabet.li:
                            parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                            tag['id'] = f"{parent_tag.attrs['id']}{self.number}"
                        elif self.caps_alpha != "A":
                            parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                            tag['id'] = f"{parent_tag.attrs['id']}{self.number}"
                        else:
                            parent_tag = None
                            tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                        if self.number == 1 and parent_tag:
                            parent_tag.append(ol_tag_for_number)
                        self.number += 1
                        if re.search(r'^\(i\)', next_tag.text.strip()):
                            if self.alphabet == "i" and self.roman_number == "i" and not re.search(r'^\(ii\)|^\(B\)', next_tag.find_next_sibling().text.strip()):
                                self.number = 1
                        elif re.search(r'^\w+', next_tag.text.strip()) and re.search(r'^\(i\)', next_tag.find_next_sibling().text.strip()):
                            if self.alphabet == "i" and self.roman_number == "i" and not re.search(r'^\(ii\)|^\(B\)', next_tag.find_next_sibling().find_next_sibling().text.strip()):
                                next_tag['id'] = f"{prev_li['id']}.{count_of_p_tag:02}"
                                next_tag['class'] = "text"
                                prev_li.append(next_tag)
                                self.number = 1
            elif prev_li and tag.name not in ['h2', 'h3', 'h4', 'h5']:
                if re.search(r'^Section \d+\.', tag.text.strip()):
                    self.alphabet = 'a'
                    self.number = 1
                    if re.search(r'^\(a\)|^\(\d\)', next_tag.text.strip()):
                        ol_count += 1
                elif re.search('^Part [IVXCL]+', tag.text.strip(), re.IGNORECASE):
                    self.alphabet = 'a'
                    ol_count = 1
                    if re.search('^Part [IVXCL]+', tag.text.strip()):
                        tag['class'] = "h3_part"
                elif re.search(r'^[IVXCL]+\. Purposes\.', tag.text.strip()):
                    self.alphabet = 'a'
                    ol_count += 1
                else:
                    tag['id'] = f"{prev_li['id']}.{count_of_p_tag:02}"
                    count_of_p_tag += 1
                    prev_li.append(tag)
            if tag.name in ["h2", "h3", "h4", "h5"]:
                self.alphabet = 'a'
                self.number = 1
                self.roman_number = 'i'
                self.inner_roman = 'i'
                self.caps_alpha = 'A'
                self.inner_num = 1
                self.caps_roman = 'I'
                self.inner_alphabet = 'a'
                self.inner_caps_roman = 'I'
                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                ol_count = 1
                prev_li = None
                count_of_p_tag = 1
                if tag.name == "h3":
                    tag['class'] = "section"
                elif tag.name == "h4":
                    tag['class'] = "sub_section"
        for tag in self.soup.main.find_all():
            if (tag.name == "li" and tag['class'] != "note" and not re.search(r'p\d+', tag.get("class")[0])) or (tag.name == "p" and tag['class'] == "text") or tag.name in ['ol']:
                del tag["class"]
            if tag.name == "b" and len(tag.text.strip()) == 0:
                tag.decompose()
        print('ol tags added')

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_Notes_to_decision_analysis_nav_tag_con()
        else:
            self.create_Notes_to_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")

    def replace_tags_constitution(self):
        super(RIParseHtml, self).replace_tags_constitution()
        note_to_decision_list: list = []
        note_to_decision_id: list = []
        self.h4_cur_id_list: list = []
        inner_case_tag = None
        case_tag = None
        h4_count = 1
        h5count = 1
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^NOTES TO DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict['ol_of_p']] and not re.search('^Click to view', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            note_to_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict['head4']] and tag.b and not re.search(r'Collateral References\.', tag.b.text):
                            tag.name = "h5"
                            tag_text = re.sub(r'\W+', '', tag.text.strip()).lower()
                            if tag.text.strip() in note_to_decision_list:
                                if re.search(r'^—\s*\w+', tag.text.strip()):
                                    inner_case_tag = tag
                                    p_tag_id = f'{case_tag.get("id")}-{tag_text}'
                                elif re.search(r'^— —\s*\w+', tag.text.strip()):
                                    p_tag_id = f'{inner_case_tag.get("id")}-{tag_text}'
                                else:
                                    p_tag_id = f'{tag.find_previous(["h3", "h2"]).get("id")}-notetodecision-{tag_text}'
                                    case_tag = tag
                            else:
                                p_tag_id = f'{tag.find_previous(["h3", "h2"]).get("id")}-notetodecision-{tag_text}'
                            if p_tag_id in note_to_decision_id:
                                tag["id"] = f'{p_tag_id}.{h5count:02}'
                                h5count += 1
                            else:
                                tag["id"] = f'{p_tag_id}'
                                h5count = 1
                            note_to_decision_id.append(p_tag_id)
                        elif tag.name in ["h2", "h3", "h4"]:
                            break
                if p_tag.text.strip() in self.h4_head:
                    header4_tag_text = re.sub(r'\W+', '', p_tag.text.strip()).lower()
                    h4_tag_id = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-{header4_tag_text}'
                    if h4_tag_id in self.h4_cur_id_list:
                        p_tag['id'] = f'{h4_tag_id}.{h4_count}'
                        h4_count += 1
                    else:
                        p_tag['id'] = f'{h4_tag_id}'
                    self.h4_cur_id_list.append(h4_tag_id)
            elif p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["head4"]] or p_tag.get("class") == [self.tag_type_dict["ol_of_p"]]:
                    if re.search(r"^History of Section\.", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'\W+', '', new_tag.text.strip()).lower()
                        new_tag['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"
            elif p_tag.name == "h3" and self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()):
                chap_no = self.regex_pattern_obj.section_pattern_con.search(p_tag.text.strip()).group('id')
                p_tag['id'] = f'{p_tag.find_previous(["h2", "h3"], ["oneh2", "gen", "amd"]).get("id")}-s{chap_no.zfill(2)}'

