"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""

import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexMS
import roman
from loguru import logger


class MSParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.alphabet = 'a'
        self.number = 1
        self.roman_number = 'i'
        self.caps_alpha = 'A'
        self.inner_num = 1
        self.inner_num_2 = 1
        self.outer_caps_alpha = "A"
        self.inner_roman = "i"

    def pre_process(self):
        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES',
                'ul': r'^Preamble', 'head2': '^Article I',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_p': '^—', 'head4': r'Compiler’s Notes\.', 'ol_p': r'HISTORY:'}

            self.h2_order = ['article', '', '', '', '']
            self.h2_text_con: list = ['Articles of Amendment']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+', 'ul': r'^Chapter \d+',
                                        'head2': r'^Chapter \d+', 'ol_p': r'HISTORY:',
                                        'head4': r'Cross References —',
                                        'head3': r'^§§? \d+-\d+-\d+',
                                        'junk1': '^Text|^Annotations',  'ol_of_p': r'\([A-Z a-z0-9]\)'}

            file_no = re.search(r'gov\.ms\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if file_no in ['07', '15', '45', '69', '89', '33', '59']:
                self.h2_order = ['chapter', 'article', '', '']
            elif file_no in ['75']:
                self.h2_order = ['chapter', 'part', 'subpart', '']
            elif file_no in ['23', '79']:
                self.h2_order = ['chapter', 'article', 'subarticle', 'part']
            elif file_no in ['93']:
                self.h2_order = ['chapter', 'article', 'part']
            else:
                self.h2_order = ['chapter', '', '', '']
        self.h4_head: list = ['Editor’s Notes —', 'Editor\'s Notes —', 'Cross References —', 'Comparable Laws from other States —', 'Amendment Notes — ', 'ATTORNEY GENERAL OPINIONS', 'RESEARCH REFERENCES','CJS.','Amendment Notes —',
                              'OPINIONS OF THE ATTORNEY GENERAL','Am. Jur.', 'Federal Aspects—', 'Lawyers’ Edition.', 'Joint Legislative Committee Note —', 'JUDICIAL DECISIONS','Law Reviews.', 'ALR.']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']

        self.watermark_text = """Release {0} of the Official Code of Mississippi Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexMS()

    def recreate_tag(self, p_tag):
        new_tag = self.soup.new_tag("p")
        new_tag.string = p_tag.b.text
        new_tag['class'] = p_tag['class']
        p_tag.insert_before(new_tag)
        p_tag.string = re.sub(f'{p_tag.b.text}', '', p_tag.text.strip())
        return p_tag, new_tag

    def replace_tags_titles(self):
        super(MSParseHtml, self).replace_tags_titles()
        h5count = 1
        judicial_decision_id: list = []
        h2_list: list = []
        analysis_tag_id = None
        analysis_tag = None
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^JUDICIAL DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and tag.name != "h4":
                            tag.name = "h5"
                            if re.search(r'^(?P<id>\d+)\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>\d+)\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous('h3').get('id')}-judicialdecision-{tag_text}"
                            elif re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous('h3').get('id')}-judicialdecision-{tag_text}"
                            if analysis_tag_id in judicial_decision_id:
                                tag["id"] = f'{analysis_tag_id}.{h5count:02}'
                                h5count += 1
                            else:
                                tag["id"] = f'{analysis_tag_id}'
                                h5count = 1
                            judicial_decision_id.append(analysis_tag_id)
                        elif tag.name in ["h2", "h3", "h4"]:
                            break
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["ul"]]:
                    p_tag.name = "li"
                    h2_list.append(p_tag.text.strip())
                    p_tag.wrap(self.ul_tag)
                elif p_tag.get("class") == [self.tag_type_dict["ol_p"]]:
                    if re.search(r"^HISTORY:", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', new_tag.text.strip()).lower()
                        new_tag.attrs['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"
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
                            tag_for_article.attrs['class'] = [self.tag_type_dict['ol_p']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_id')}"
                        elif re.search(r'^Article \d+\.', p_tag.text.strip()):
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search(r'^(Article (?P<article_number>\d+)\.)', p_tag.text.strip())
                            tag_for_article.string = article_number.group()
                            tag_text = p_tag.text.replace(f'{article_number.group()}', '')
                            p_tag.insert_before(tag_for_article)
                            p_tag.clear()
                            p_tag.string = tag_text
                            tag_for_article.attrs['class'] = [self.tag_type_dict['ol_p']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_number')}"
                elif p_tag.get('class') == [self.tag_type_dict["head2"]]:
                    if p_tag.text.strip() in h2_list:
                        p_tag.name = "h2"
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        tag_id = f'{p_tag.find_previous("h2",class_="oneh2").get("id")}-{tag_text}'
                        if tag_id in self.dup_id_list:
                            p_tag["id"] = f'{tag_id}.{self.id_count:02}'
                            self.id_count += 1
                        else:
                            p_tag["id"] = f'{tag_id}'
                            self.id_count = 1
                        self.dup_id_list.append(tag_id)
            elif p_tag.name == "li" and not re.search(r'^Chapter \d+|^§§? \d+-\d+-\d+',p_tag.text.strip()) and p_tag.get('class')!= "note":
                h2_list.append(p_tag.text.strip())
                self.c_nav_count += 1
                tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                head_id = f'#{p_tag.find_previous("h2").get("id")}-{tag_text}'
                if head_id in self.list_ids:
                    p_tag['id'] = f'{head_id}.{self.list_id_count:02}-{f"cnav{self.c_nav_count:02}"}'
                    ref_id= f'{head_id}.{self.list_id_count:02}'
                    self.list_id_count += 1
                else:
                    p_tag['id'] = f'{head_id}-{f"cnav{self.c_nav_count:02}"}'
                    ref_id = f'{head_id}'
                    self.list_id_count = 1
                self.list_ids.append(head_id)
                anchor = self.soup.new_tag('a', href=ref_id)
                anchor.string = p_tag.text
                p_tag.string = ''
                p_tag.append(anchor)
            elif p_tag.name == "h2" and p_tag.get("class") == "oneh2":
                self.c_nav_count = 0
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

    def initialize(self, ol_tag, cls_list):
        prev_tag = ol_tag.find_previous(["ol", "h3", "h4"], cls_list)
        if prev_tag.name != "ol":
            if cls_list[0] == "caps_alpha":
                self.caps_alpha = "A"
            elif cls_list[0] == "number":
                self.number = 1
            elif cls_list[0] == "inner_num":
                self.inner_num = 1
            elif cls_list[0] == "inner_roman":
                self.inner_roman = "i"
            elif cls_list[0] == "roman":
                self.roman_number = "i"

    def split_tag(self, tag, split_attr, split_by):
        text_from_b = re.split(split_attr, tag.text.strip())
        p_tag = self.soup.new_tag("p")
        p_tag.string = f'{text_from_b[0]}{split_by}'
        tag.string = tag.text.replace(f'{text_from_b[0]}{split_by}', '')
        tag.insert_before(p_tag)
        if re.search(r'^Section \d+\.', p_tag.text.strip()):
            p_tag.string.wrap(self.soup.new_tag("b"))
        p_tag.attrs['class'] = tag['class']

    @staticmethod
    def increment(text):
        if re.search('[ivx]+', text):
            text = roman.toRoman(roman.fromRoman(text.upper()) + 1).lower()
        elif re.search('[IVX]+', text):
            text = roman.toRoman(roman.fromRoman(text) + 1)
        elif re.search('[a-zA-Z]', text):
            if len(text) == 2:
                text = chr(ord(text[0]) + 1)
                text = f"{text}{text}"
            else:
                text = chr(ord(text) + 1)
        elif re.search(r'\d+', text):
            text = int(text) + 1
        return text

    def recreate_ol_tag(self):
        for tag in self.soup.main.find_all("p"):
            class_name = tag.get('class')[0]
            if class_name == self.tag_type_dict['ol_p'] or class_name == self.tag_type_dict['ol_of_p'] or class_name == self.tag_type_dict['head4']:
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
                        sibling_tag = tag.find_next_sibling(lambda next_tag: re.search(fr'^\({text}\)|^\({text_1}\)',  next_tag.text.strip()) or next_tag.name == "h4")
                    else:
                        sibling_tag = tag.find_next_sibling()
                    next_tag = tag.find_next_sibling()
                    if next_tag.br:
                        next_tag = next_tag.find_next_sibling()
                    if re.search(fr'^\({text}\)', sibling_tag.text.strip()) and text != text_1 and alpha != text_string and not re.search(
                            fr'\({text_string}\)', next_tag.text.strip()):
                        self.split_tag(tag, fr'{split_attr}\s+\({text_string}\)', split_attr)
                    elif re.search('Section \d+\.', tag.text.strip()):
                        sibling_tag = tag.find_next_sibling(lambda next_tag: re.search(fr'^\({text}\)|^Section \d+\.', next_tag.text.strip()))
                        if re.search(fr'^\({text}\)', sibling_tag.text.strip()):
                            self.split_tag(tag, fr'{split_attr}\s+\({text_string}\)', split_attr)
            elif tag.br and len(tag.text.strip()) == 0:
                tag.decompose()

    def convert_paragraph_to_alphabetical_ol_tags(self):
        self.recreate_ol_tag()
        self.create_analysis_nav_tag()
        prev_li = None
        ol_count = 1
        count_of_p_tag = 1
        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
        for tag in self.soup.main.find_all(["h2", "h3", "h4", "p"]):
            if not tag.name:
                continue
            if tag.i:
                tag.i.unwrap
            if tag['class'] == "text":
                continue
            next_tag = tag.find_next_sibling()
            if not next_tag:
                break
            if re.search('Complies with the rules of the Commission.', tag.text):
                print()
            if re.search(fr'^{self.inner_num_2}\.', tag.text.strip()):
                prev_li = tag
                if self.inner_num_2 == 1:
                    ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                    ol_tag_for_inner_number_2['class'] = "inner_num_2"
                self.inner_roman = "i"
                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                tag.name = "li"
                tag.string = re.sub(fr'^{self.inner_num_2}\.', '', tag.text.strip())
                tag['class'] = "inner_num_2"
                if self.inner_num_2 != 1:
                    ol_tag_for_inner_number_2.append(tag)
                else:
                    tag.wrap(ol_tag_for_inner_number_2)
                self.initialize(ol_tag_for_inner_number_2, ["alphabet", "section", "sub_section"])
                if self.outer_caps_alpha != "A":
                    parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_num_2}'
                elif self.roman_number != "i":
                    parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                    tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                elif self.alphabet != "a":
                    parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                else:
                    parent_tag = None
                    tag['id'] = f"{tag_id}ol{ol_count}{self.inner_num_2}"
                if self.inner_num_2 == 1 and parent_tag:
                    parent_tag.append(ol_tag_for_inner_number_2)
                self.inner_num_2 += 1
            elif re.search(fr'^{self.outer_caps_alpha}\.|^\({self.outer_caps_alpha}\)', tag.text.strip()) and ((self.alphabet == "a" and self.number == 1 and self.inner_num == 1) or self.outer_caps_alpha != "A"):
                prev_li = tag
                if self.outer_caps_alpha == "A":
                    ol_tag_for_outer_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_outer_caps_alphabet['class'] = "outer_caps_alpha"
                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                tag.name = "li"
                tag.string = re.sub(fr'^{self.outer_caps_alpha}\.', '', tag.text.strip())
                tag['class'] = "outer_caps_alpha"
                if self.outer_caps_alpha != "A":
                    ol_tag_for_outer_caps_alphabet.append(tag)
                else:
                    tag.wrap(ol_tag_for_outer_caps_alphabet)
                self.inner_num = 1
                tag['id'] = f"{tag_id}ol{ol_count}{self.outer_caps_alpha}"
                self.outer_caps_alpha = chr(ord(self.outer_caps_alpha) + 1)
            elif re.search(fr'^\({self.caps_alpha}\)|^{self.caps_alpha}\.', tag.text.strip()):
                prev_li = tag
                if self.caps_alpha == "A":
                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                tag.name = "li"
                tag.string = re.sub(fr'^\({self.caps_alpha}\)|^{self.caps_alpha}\.', '', tag.text.strip())
                tag['class'] = "caps_alpha"
                if self.caps_alpha != "A":
                    ol_tag_for_caps_alphabet.append(tag)
                else:
                    tag.wrap(ol_tag_for_caps_alphabet)
                self.initialize(ol_tag_for_caps_alphabet, ["roman", "section", "sub_section"])
                if self.number != 1:
                    parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                elif self.inner_num != 1:
                    parent_tag = ol_tag_for_inner_number.find_all('li', class_='inner_num')[-1]
                elif self.roman_number != "i":
                    parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                elif self.alphabet != "a":
                    parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                if self.caps_alpha == "A":
                    parent_tag.append(ol_tag_for_caps_alphabet)
                tag['id'] = f"{parent_tag.attrs['id']}{self.caps_alpha}"
                if self.caps_alpha == "Z":
                    self.caps_alpha = 'A'
                else:
                    self.caps_alpha = chr(ord(self.caps_alpha) + 1)
            elif re.search(fr'^\({self.number}\)|^\({self.inner_num}\)', tag.text.strip()):
                prev_li = tag
                if re.search(fr'^\({self.inner_num}\)', tag.text.strip()) and ol_tag_for_alphabet.li:
                    if self.inner_num == 1:
                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                        ol_tag_for_inner_number['class'] = "inner_num"
                    self.caps_alpha = "A"
                    if re.search(fr'^\({self.inner_num}\)\s?\({self.caps_alpha}\)', tag.text.strip()):
                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                        ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_num}\)\s?\({self.caps_alpha}\)', '', tag.text.strip())
                        tag['class'] = "caps_alpha"
                        li_tag = self.soup.new_tag("li")
                        tag.wrap(ol_tag_for_caps_alphabet)
                        if ol_tag_for_alphabet.li:
                            li_tag['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.inner_num}'
                            tag.attrs['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.inner_num}{self.caps_alpha}'
                            if self.inner_num == 1:
                                ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_inner_number)
                        li_tag['class'] = "inner_num"
                        ol_tag_for_caps_alphabet.wrap(li_tag)
                        if self.caps_alpha == 'Z':
                            self.caps_alpha = 'A'
                        else:
                            self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                        if self.inner_num != 1:
                            ol_tag_for_inner_number.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_inner_number)
                        self.inner_num += 1
                    else:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_num}\)', '', tag.text.strip())
                        tag['class'] = "inner_num"
                        if self.inner_num != 1:
                            ol_tag_for_inner_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_number)
                        self.initialize(ol_tag_for_inner_number, ["roman", "section", "sub_section"])
                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_inner_number)
                        tag['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.inner_num}'
                        self.inner_num += 1
                else:
                    if self.number == 1:
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_number['class'] = "number"
                    self.alphabet = "a"
                    self.caps_alpha = "A"
                    self.roman_number = "i"
                    if re.search(fr'^\({self.number}\)\s?\({self.alphabet}\)', tag.text.strip()):
                        if re.search(fr'^\({self.number}\)\s?\({self.alphabet}\)\s?\({self.roman_number}\)', tag.text.strip()):
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            ol_tag_for_roman['class'] = "roman"
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.alphabet}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_roman)
                            li_tag_for_number = self.soup.new_tag("li")
                            li_tag_for_number['id'] = f"{tag_id}ol{ol_count}{self.number}"
                            li_tag_for_number['class'] = "number"
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{self.number}{self.alphabet}"
                            li_tag_for_alphabet['class'] = "alphabet"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{self.alphabet}-{self.roman_number}"
                            ol_tag_for_roman.wrap(li_tag_for_alphabet)
                            li_tag_for_alphabet.wrap(ol_tag_for_alphabet)
                            ol_tag_for_alphabet.wrap(li_tag_for_number)
                            if self.number != 1:
                                ol_tag_for_number.append(li_tag_for_number)
                            else:
                                li_tag_for_number.wrap(ol_tag_for_number)
                            tag['class'] = 'roman'
                            self.number += 1
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            self.alphabet = chr(ord(self.alphabet) + 1)
                        else:
                            ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                            ol_tag_for_alphabet['class'] = "alphabet"
                            tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.number}\)\s?\({self.alphabet}\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_alphabet)
                            li_tag = self.soup.new_tag("li")
                            li_tag['class'] = "number"
                            ol_tag_for_alphabet.wrap(li_tag)
                            tag['class'] = "alphabet"
                            if self.number != 1:
                                ol_tag_for_number.append(li_tag)
                            else:
                                li_tag.wrap(ol_tag_for_number)
                            li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{self.alphabet}"
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.number += 1
                    else:
                        tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.number}\)', '', tag.text.strip())
                        tag['class'] = "number"
                        if self.number != 1:
                            ol_tag_for_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_number)
                        tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                        self.number += 1
            elif re.search(fr'^\({self.roman_number}\)', tag.text.strip()) and self.alphabet != self.roman_number:
                prev_li = tag
                if self.roman_number == "i":
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                self.inner_roman = "i"
                tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                tag.name = "li"
                tag.string = re.sub(fr'^\({self.roman_number}\)', '', tag.text.strip())
                tag['class'] = "roman"
                if self.roman_number != "i":
                    ol_tag_for_roman.append(tag)
                else:
                    tag.wrap(ol_tag_for_roman)
                self.initialize(ol_tag_for_roman, ["caps_alpha", "section", "sub_section"])
                if re.search('^\(A\)', next_tag.text.strip()):
                    self.caps_alpha = "A"
                self.inner_num_2 = 1
                if self.caps_alpha != "A":
                    parent_tag = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                elif self.inner_num != 1:
                    parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                elif self.alphabet != "a":
                    parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                else:
                    parent_tag = None
                    tag['id'] = f"{tag_id}ol{ol_count}-{self.roman_number}"
                if parent_tag and self.roman_number == "i":
                    parent_tag.append(ol_tag_for_roman)
                self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
            elif re.search(fr'^\({self.inner_roman}\)', tag.text.strip()) and self.roman_number != "i" and self.inner_roman != self.alphabet:
                prev_li = tag
                if self.inner_roman == "i":
                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_inner_roman['class'] = "inner_roman"
                tag.name = "li"
                tag.string = re.sub(fr'^\({self.inner_roman}\)', '', tag.text.strip())
                tag['class'] = "inner_roman"
                if self.inner_roman != "i":
                    ol_tag_for_inner_roman.append(tag)
                else:
                    tag.wrap(ol_tag_for_inner_roman)
                if self.inner_num_2 != 1:
                    parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                elif self.roman_number != "i":
                    parent_tag = ol_tag_for_roman.find_all("li", class_="roman")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                elif self.alphabet != "a":
                    parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                if self.inner_roman == "i":
                    parent_tag.append(ol_tag_for_inner_roman)
                self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
            elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)', tag.text.strip()):
                alpha_id = re.search(fr'^\((?P<alpha_id>{self.alphabet}{self.alphabet}?)\)', tag.text.strip()).group('alpha_id')
                prev_li = tag
                if alpha_id == "a":
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    ol_tag_for_alphabet['class'] = "alphabet"
                if re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\(', tag.text.strip()):
                    self.inner_num = 1
                    self.caps_alpha = "A"
                    self.roman_number = "i"
                    self.inner_roman = "i"
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                if re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.roman_number}\)', tag.text.strip()):
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.roman_number}\)', '', tag.text.strip())
                    tag.wrap(ol_tag_for_roman)
                    li_tag = self.soup.new_tag("li")
                    li_tag['class'] = "alphabet"
                    ol_tag_for_roman.wrap(li_tag)
                    tag['class'] = "roman"
                    if ol_tag_for_alphabet.li:
                        ol_tag_for_alphabet.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_alphabet)
                    if self.number != 1:
                        li_tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{alpha_id}"
                        tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{alpha_id}-{self.roman_number}"
                        if alpha_id == "a":
                            ol_tag_for_number.find_all('li', class_='number')[-1].append(ol_tag_for_alphabet)
                    else:
                        li_tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}-{self.roman_number}"
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    self.alphabet = chr(ord(self.alphabet) + 1)
                elif re.search(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.inner_num}\)', tag.text.strip()):
                    ol_tag_for_inner_number = self.soup.new_tag("ol")
                    ol_tag_for_inner_number['class'] = "inner_num"
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.inner_num}\)', '', tag.text.strip())
                    tag.wrap(ol_tag_for_inner_number)
                    li_tag = self.soup.new_tag("li")
                    li_tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                    li_tag['class'] = "alphabet"
                    ol_tag_for_inner_number.wrap(li_tag)
                    tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}{self.inner_num}"
                    tag['class'] = "inner_num"
                    if alpha_id != "a":
                        ol_tag_for_alphabet.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_alphabet)
                    self.inner_num += 1
                    self.alphabet = chr(ord(self.alphabet) + 1)
                else:
                    if alpha_id == "i":
                        sibling_of_i = tag.find_next_sibling(lambda sibling_tag: re.search(r'^\(ii\)|^HISTORY:|^\(i\)|\(j\)', sibling_tag.text.strip()))
                        if re.search(r'^\(ii\)', sibling_of_i.text.strip()):
                            if re.search(fr'^\({self.roman_number}\)', tag.text.strip()):
                                prev_li = tag
                                self.inner_num = 1
                                if self.roman_number == "i":
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    ol_tag_for_roman['class'] = "roman"
                                tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({self.roman_number}\)', '', tag.text.strip())
                                tag['class'] = "roman"
                                if self.roman_number != "i":
                                    ol_tag_for_roman.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_roman)
                                self.initialize(ol_tag_for_roman, ["inner_num", "section", "sub_section"])
                                if self.alphabet != "a":
                                    tag[
                                        'id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}-{self.roman_number}'
                                    if self.roman_number == "i":
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                else:
                                    tag['id'] = f"{tag_id}ol{ol_count}-{self.roman_number}"
                                self.roman_number = roman.toRoman(
                                    roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            else:
                                if self.inner_roman == "i":
                                    ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                                    ol_tag_for_inner_roman['class'] = "inner_roman"
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({self.inner_roman}\)', '', tag.text.strip())
                                tag['class'] = "inner_roman"
                                if self.inner_roman != "i":
                                    ol_tag_for_inner_roman.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_inner_roman)
                                if self.inner_num_2 != 1:
                                    parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                                elif self.roman_number != "i":
                                    parent_tag = ol_tag_for_roman.find_all("li", class_="roman")[-1]
                                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                                elif self.alphabet != "a":
                                    parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                                if self.inner_roman == "i":
                                    parent_tag.append(ol_tag_for_inner_roman)
                                self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
                        else:
                            self.roman_number = "i"
                            self.inner_roman = "i"
                            self.caps_alpha = "A"
                            self.inner_num = 1
                            tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)', '', tag.text.strip())
                            tag['class'] = "alphabet"
                            if alpha_id != "a":
                                ol_tag_for_alphabet.append(tag)
                            else:
                                tag.wrap(ol_tag_for_alphabet)
                            if self.number != 1:
                                parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                            elif self.inner_num != 1:
                                parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                            else:
                                parent_tag = None
                                tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                            if alpha_id == "a" and parent_tag:
                                parent_tag.append(ol_tag_for_alphabet)
                            if self.alphabet == "z":
                                self.alphabet = "a"
                            else:
                                self.alphabet = chr(ord(self.alphabet) + 1)
                    else:
                        self.caps_alpha = "A"
                        self.inner_num = 1
                        self.roman_number = "i"
                        self.inner_roman = "i"
                        tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)', '', tag.text.strip())
                        tag['class'] = "alphabet"
                        if alpha_id != "a":
                            ol_tag_for_alphabet.append(tag)
                        else:
                            tag.wrap(ol_tag_for_alphabet)
                        self.initialize(ol_tag_for_alphabet, ["inner_num_2", "section", "sub_section"])
                        if self.number != 1:
                            parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                        elif self.outer_caps_alpha != "A":
                            parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                        elif self.inner_num != 1:
                            parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                        else:
                            parent_tag = None
                            tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                        if alpha_id == "a" and parent_tag:
                            parent_tag.append(ol_tag_for_alphabet)
                        if self.alphabet == "z":
                            self.alphabet = "a"
                        else:
                            self.alphabet = chr(ord(self.alphabet) + 1)
            elif prev_li and tag.name not in ['h2', 'h3', 'h4', 'h5']:
                if re.search(r'^[IVXCL]+\. [A-Z ]+', tag.text.strip()):
                    self.alphabet = 'a'
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    self.roman_number = "i"
                    ol_count += 1
                elif re.search(r'^Section \d+\.', tag.text.strip()):
                    self.alphabet = 'a'
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    self.number = 1
                    self.roman_number = "i"
                    if re.search(r'^\(a\)|^\(\d\)', next_tag.text.strip()):
                        ol_count += 1
                else:
                    tag['id'] = f"{prev_li['id']}.{count_of_p_tag:02}"
                    count_of_p_tag += 1
                    prev_li.append(tag)
            if tag.name in ["h2", "h3", "h4"]:
                self.alphabet = 'a'
                self.number = 1
                self.roman_number = 'i'
                self.inner_num = 1
                self.inner_num_2 = 1
                self.caps_alpha = "A"
                self.outer_caps_alpha = "A"
                self.inner_roman = "i"
                ol_tag_for_alphabet = self.soup.new_tag("ol", type= "a")
                ol_count = 1
                prev_li = None
                count_of_p_tag = 1
                if tag.name == "h3":
                    tag['class'] = "section"
                elif tag.name == "h4":
                    tag['class'] = "sub_section"
        for tag in self.soup.main.find_all(["li", "p", "ol"]):
            if (tag.name == "li" and tag['class'] != "note") or (tag.name == "p" and tag['class'] == "text") or tag.name in ['ol']:
                del tag["class"]
            if tag.name == "b" and len(tag.text.strip()) == 0:
                tag.decompose()
            if tag.name == "p" and re.search(r'^\([a-zA-Z0-9]+\)', tag.text.strip()):
                print(tag)

        print('ol tags added')

    def create_judicial_decision_analysis_nav_tag(self):
        analysis_num_tag = None
        a_tag_id = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        for analysis_p_tag in self.soup.findAll('p', {'class': self.tag_type_dict['ol_p']}):
            if analysis_p_tag.find_previous(["h4", "h5"]):
                if re.search(r'^JUDICIAL DECISIONS', analysis_p_tag.find_previous(["h4", "h5"]).text.strip()):
                    if re.search(r'^\d+\.\s—\w+', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        a_tag_text = re.search(r'^(?P<id>\d+)\.', analysis_p_tag.text.strip()).group("id")
                        if not re.search(r'^\d+\.\s—\w+', analysis_p_tag.find_previous("li").text.strip()):
                            text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(text_ul_tag)
                            analysis_num_tag.append(text_ul_tag)
                        else:
                            text_ul_tag.append(analysis_p_tag)
                        a_tag_id = f"#{analysis_p_tag.find_previous('h3').get('id')}-judicialdecision-{a_tag_text}"
                    elif re.search(r'^\d+\.', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        analysis_num_tag = analysis_p_tag
                        if not re.search(r'^\d+\.', analysis_p_tag.find_previous("li").text.strip()) or re.search(r'^1\.', analysis_p_tag.text.strip()):
                            inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(inner_ul_tag)
                            if analysis_p_tag.find_previous("li") and re.search(r'^[IVX]+\.', analysis_p_tag.find_previous("li").text.strip()):
                                analysis_rom_tag.append(inner_ul_tag)
                        else:
                            inner_ul_tag.append(analysis_p_tag)
                        a_tag_text = re.search(r'^(?P<id>\d+)\.', analysis_p_tag.text.strip()).group("id")
                        analysis_num_tag_id = f"#{analysis_p_tag.find_previous('h3').get('id')}-judicialdecision-{a_tag_text}"
                        a_tag_id = analysis_num_tag_id
                    elif re.search(r'^[IVX]+\.', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        analysis_rom_tag = analysis_p_tag
                        if re.search(r'^I\.', analysis_p_tag.text.strip()):
                            outer_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(outer_ul_tag)
                        else:
                            outer_ul_tag.append(analysis_p_tag)
                        a_tag_text = re.search(r'^(?P<id>[IVX]+)\.', analysis_p_tag.text.strip()).group("id")
                        analysis_rom_tag_id = f"#{analysis_p_tag.find_previous('h3').get('id')}-judicialdecision-{a_tag_text}"
                        a_tag_id = analysis_rom_tag_id
                    anchor = self.soup.new_tag('a', href=a_tag_id)
                    anchor.string = analysis_p_tag.text
                    analysis_p_tag.string = ''
                    analysis_p_tag.append(anchor)

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_judicial_decision_analysis_nav_tag()
        else:
            self.create_judicial_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")


