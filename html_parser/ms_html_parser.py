"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""

import re

from bs4 import BeautifulSoup

from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexMS
import roman
from loguru import logger
from tabulate import tabulate


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
        self.inner_alphabet = "a"
        self.caps_roman = "I"
        self.inner_alphabet_2 = "a"

    def pre_process(self):
        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^The Constitution of the',
                'ul': r'^PREAMBLE', 'head2': '^Article [1I]',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_p': '^—', 'head4': r'Cross References —', 'ol_p': r'^HISTORY:', 'table': r'\w+'}

            self.h2_order = ['article', '', '', '', '']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+', 'ul': r'^Chapter \d+',
                                        'head2': r'^Chapter \d+', 'ol_p': r'HISTORY:',
                                        'head4': r'Cross References —',
                                        'head3': r'^§§? \d+-\d+-\d+',
                                        'junk1': '^Text|^Annotations',  'ol_of_p': r'\([A-Z a-z0-9]\)', 'table': r'\w+'}

            file_no = re.search(r'gov\.ms\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if file_no in ['07', '15', '45', '69', '89', '33', '59']:
                self.h2_order = ['chapter', 'article', '', '']
            elif file_no in ['75']:
                self.h2_order = ['chapter', 'part', 'subpart', '']
            elif file_no in ['23', '79']:
                self.h2_order = ['chapter', 'article', 'subarticle', 'part']
            elif file_no in ['93']:
                self.h2_order = ['chapter', 'article', 'part', '']
            else:
                self.h2_order = ['chapter', '', '', '']
        self.h4_head: list = ['Editor’s Notes —', 'Proposal and Ratification.', 'ETHICS OPINIONS', 'Editor’s note—', 'Amendment Note —', 'Editor\'s Notes. —', 'Editor\'s Notes.—', 'Editor Notes', 'Editor\'s Notes.', 'Editor\'s Note —', 'Cross References —', 'Cross references. —', 'Cross References. —', 'Joint Legislative Committee Note.--–', 'Cross References–', 'Comparable Laws from other States —', 'Amendment Notes — ', 'ATTORNEY GENERAL OPINIONS', 'RESEARCH REFERENCES', 'CJS.', 'Amendment Notes —',
                              'OPINIONS OF THE ATTORNEY GENERAL', 'Joint Legislative Committe Note', 'Editor’s Notes –', 'Editor\'s Notes.--', 'Editor’s Note —', 'Editor’s note. —', 'Joint Legislative Committee Note--', 'Comparable Laws From Other States —', 'Editor\'s Notes. –', 'Joint Legislative Committee Note.--', 'Cross References—', 'Editor Notes -–', 'Editor Notes —', 'Amendment Notes -–', 'Lawyers\' Edition.', 'Editor’s notes —', 'Editor\'s Notes —', 'Editor\'s notes —', 'Editor Notes --',
                              'Editor\'s note—', 'Comparable Laws:', 'Special Note to Chapter', 'Joint Legislative Committee Note—', 'Am. Jur.', 'Practice References.', 'Amendment Notes', 'Federal Aspects—', 'Lawyers’ Edition.', 'Joint Legislative Committee Note —', 'JUDICIAL DECISIONS', 'Judicial Decisions', 'Law Reviews.', 'ALR.', 'Federal Aspects —']
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
        h4_count = 1
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^(JUDICIAL DECISIONS|ETHICS OPINIONS)', p_tag.text.strip(), re.I):
                    a_tag_text = re.sub(r'[\W_]+', '', p_tag.text.strip()).strip().lower()
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and tag.name != "h4" and not re.search('^Analysis', tag.text.strip()):
                            tag.name = "h5"
                            if re.search(r'^(?P<id>\d+)(-\d+)?\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>\d+)(-\d+)?\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous('h3').get('id')}-{a_tag_text}-{tag_text}"
                            elif re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous('h3').get('id')}-{a_tag_text}-{tag_text}"
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
                if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    print(p_tag)
                if p_tag.get("class") == [self.tag_type_dict["ol_p"]]:
                    if re.search(r"^HISTORY:", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', new_tag.text.strip()).lower()
                        new_tag.attrs['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"
                    elif re.search(r"^ARTICLE (\d+|[IVXCL]+)", p_tag.text.strip(), re.I):
                        if re.search(r"^ARTICLE [IVXCL]+$", p_tag.text.strip()) and p_tag.b:
                            sibling_tag = p_tag.find_next_sibling(lambda sib_tag: re.search(r'^\(a\)|^HISTORY:', sib_tag.text.strip()))
                            if re.search(r'^\(a\)', sibling_tag.text.strip()) or (re.search('^[A-Z]{2,}', p_tag.find_next_sibling().text.strip())):
                                p_tag.name = "h4"
                                article_id = re.search(r"^ARTICLE (?P<article_id>[IVXCL]+)", p_tag.text.strip(), re.I).group('article_id')
                                p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_id}"
                        elif re.search(r"^ARTICLE [IVXCL]+\.?$", p_tag.text.strip(), re.I) and p_tag.b:
                            p_tag.name = "h4"
                            article_id = re.search(r"^ARTICLE (?P<article_id>[IVXCL]+)", p_tag.text.strip(), re.I).group('article_id')
                            p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_id}"
                        elif re.search(r"^ARTICLE ([IVXCL]|\d)+[—.]?[A-Z\sa-z]+", p_tag.text.strip(), re.I) and p_tag.b:
                            tag_for_article = self.soup.new_tag("h4")
                            article_number = re.search(r'^(ARTICLE (?P<article_id>([IVXCL]|\d)+))', p_tag.text.strip(), re.I)
                            if p_tag.b:
                                tag_for_article.string = p_tag.b.text.strip()
                                tag_text = re.sub(fr'{p_tag.b.text.strip()}', '', p_tag.text.strip())
                            else:
                                tag_for_article.string = article_number.group()
                                tag_text = re.sub(fr'{article_number.group()}', '', p_tag.text.strip())
                            p_tag.insert_before(tag_for_article)
                            p_tag.clear()
                            p_tag.string = tag_text
                            tag_for_article.attrs['class'] = [self.tag_type_dict['ol_p']]
                            tag_for_article['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{article_number.group('article_id')}"
                    elif re.search(r"^SECTION \d+", p_tag.text.strip()) and p_tag.b:
                        p_tag.name = "h4"
                        section_id = re.search(r"^SECTION (?P<section_id>\d+)", p_tag.text.strip()).group('section_id')
                        p_tag['id'] = f"{p_tag.find_previous_sibling('h3').attrs['id']}a{section_id}"
                elif p_tag.get('class') == [self.tag_type_dict["ol_of_p"]]:
                    if re.search(r'^Editor\'s Note\s*\w+', p_tag.text.strip()) and p_tag.b:
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
                elif p_tag.get('class') == [self.tag_type_dict["head2"]]:
                    if p_tag.text.strip() in h2_list:
                        p_tag.name = "h2"
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        tag_id = f'{p_tag.find_previous("h2", ["oneh2", "twoh2", "threeh2"]).get("id")}-{tag_text}'
                        if tag_id in self.dup_id_list:
                            p_tag["id"] = f'{tag_id}.{self.id_count:02}'
                            self.id_count += 1
                        else:
                            p_tag["id"] = f'{tag_id}'
                            self.id_count = 1
                        self.dup_id_list.append(tag_id)
            elif p_tag.name == "li" and not re.search(r'^Chapter \d+|^§*\s*(?P<id>\d+[-–]\d+[-–]\d+)', p_tag.text.strip()) and p_tag.get('class') != "note":
                h2_list.append(p_tag.text.strip())
                self.c_nav_count += 1
                tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                head_id = f'#{p_tag.find_previous("h2", ["oneh2", "twoh2", "threeh2"]).get("id")}-{tag_text}'
                if head_id in self.list_ids:
                    p_tag['id'] = f'{head_id}.{self.list_id_count:02}-{f"cnav{self.c_nav_count:02}"}'
                    ref_id = f'{head_id}.{self.list_id_count:02}'
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
            elif cls_list[0] == "inner_num_2":
                self.inner_num_2 = 1
            elif cls_list[0] == "inner_alphabet":
                self.inner_alphabet = "a"
            elif cls_list[0] == "alphabet":
                self.alphabet = "a"

    @staticmethod
    def increment(text):
        if re.search('[ivx]+', text):
            text = roman.toRoman(roman.fromRoman(text.upper()) + 1).lower()
        elif re.search('[IVX]+', text):
            text = roman.toRoman(roman.fromRoman(text) + 1)
        elif re.search('[a-zA-Z]', text):
            if len(text) == 2:# oo
                text = chr(ord(text[0]) + 1)
                text = f"{text}{text}"
            else:
                text = chr(ord(text) + 1)
        elif re.search(r'\d+', text):
            text = int(text) + 1
        return text

    def recreate_ol_tag(self):
        for tag in self.soup.main.find_all("p"):
            if re.search('Document\s*Fee \(1\)', tag.text.strip()):
                tag.string = tag.text.strip().replace('\xa0', '')
            class_name = tag.get('class')[0]
            if class_name == self.tag_type_dict['ol_p'] or class_name == self.tag_type_dict['ol_of_p'] or class_name == self.tag_type_dict['head4'] or class_name == self.tag_type_dict['table']:
                if re.search(r'^(\(([a-z\d]+)\)\s(\(\w\) )?)?.{2,}?[:—.]\s*\(\w\)', tag.text.strip()):#2. (i)
                    text = re.search(r'^(\((?P<text_1>([a-z\d]+))\)\s(\((?P<id>\w)\) )?)?.{2,}?(?P<split_attr>[.—:])\s*\((?P<text>\w)\)', tag.text.strip())
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
                    if re.search(fr'^\({text}\)', sibling_tag.text.strip()) and text != text_1 and alpha != text_string and not re.search(fr'^\({text_string}\)', next_tag.text.strip()):
                        text_from_b = re.split(fr'{split_attr}\s+\({text_string}\)', tag.text.strip())
                        p_tag = self.soup.new_tag("p")
                        p_tag.string = f'{text_from_b[0]}{split_attr}'
                        tag.string = tag.text.replace(f'{text_from_b[0]}{split_attr}', '')
                        tag.insert_before(p_tag)
                        if re.search(r'^Section \w+\.', p_tag.text.strip()):
                            p_tag.string.wrap(self.soup.new_tag("b"))
                        p_tag.attrs['class'] = tag['class']
                    elif re.search(r'^Section \w+\.', tag.text.strip()):
                        sibling_tag = tag.find_next_sibling(lambda next_tag: re.search(fr'^\({text}\)|^Section \w+\.', next_tag.text.strip()))
                        if sibling_tag and re.search(fr'^\({text}\)', sibling_tag.text.strip()):
                            text_from_b = re.split(fr'{split_attr}\s+\({text_string}\)', tag.text.strip())
                            p_tag = self.soup.new_tag("p")
                            p_tag.string = f'{text_from_b[0]}{split_attr}'
                            tag.string = tag.text.replace(f'{text_from_b[0]}{split_attr}', '')
                            tag.insert_before(p_tag)
                            if re.search(r'^Section \w+\.', p_tag.text.strip()):
                                p_tag.string.wrap(self.soup.new_tag("b"))
                            p_tag.attrs['class'] = tag['class']
                elif re.search('^Member Lost Number', tag.text.strip(), re.I):
                    tag.string = tag.text.strip().replace('\xa0', '')
                    p_tag = f'<p class={tag["class"][0]}>Member Lost Number Weeks Compensation</p>'
                    tag.insert_before(BeautifulSoup(p_tag, features="html.parser"))
                    for i in re.findall('\(\d+\)[a-z, ]+\d+', tag.text.strip(), re.I):
                        p_tag = f'<p class={tag["class"][0]}>{i}</p>'
                        tag.insert_before(BeautifulSoup(p_tag, features="html.parser"))
                    tag.decompose()
                elif re.search('^Document Fee \([a1]\)', tag.text.strip(), re.I):
                    tag.string = tag.text.strip().replace('\xa0', '')
                    p_tag = f'<p class={tag["class"][0]}>Document Fee</p>'
                    tag.insert_before(BeautifulSoup(p_tag, features="html.parser"))
                    tag.string = tag.text.replace('Document Fee', '')
                    li_text = list(filter(None, re.split('((?:\(\w+\))(?:\(A\))?)', tag.text.strip())))
                    for i in range(0, len(li_text), 2):
                        p_tag = f'<p class={tag["class"][0]}><b>{li_text[i]}</b> {li_text[i + 1]}</p>'
                        tag.insert_before(BeautifulSoup(p_tag, features="html.parser"))
                    tag.decompose()
                elif re.search('^\(a\) At a speed that exceeds the posted speed limit', tag.text.strip(), re.I):
                    li_text = list(filter(None,re.split('(\([a-z]\))', tag.text.strip())))
                    for i in range(0, len(li_text), 2):
                        p_tag = f'<p class={tag["class"][0]}>{li_text[i]} {li_text[i+1]}</p>'
                        tag.insert_before(BeautifulSoup(p_tag, features="html.parser"))
                    tag.decompose()
                elif re.search('a. For each application filed for the purchase', tag.text.strip()):
                    tag_text = re.split(':', tag.text.strip())
                    tag.string = tag_text[0]
                    p_tag = self.soup.new_tag("p")
                    p_tag.string = tag_text[1]
                    p_tag['class'] = tag['class']
                    tag.insert_after(p_tag)
                elif re.search(r'(From and after January 1, \d+(?:, through December \d+, \d+)?:)', tag.text.strip()) and not tag.b:
                    tag_text = list(x for x in filter(None, re.split('(From and after January 1, \d+(?:, through December \d+, \d+)?:)', tag.text.strip())) if x !=" ")
                    for i in range(len(tag_text)):
                        p_tag = self.soup.new_tag("p")
                        p_tag['class'] = tag['class']
                        p_tag.string = tag_text[i]
                        tag.insert_before(p_tag)
                        if re.search('From and after January 1', tag_text[i]):
                            p_tag.string.wrap(self.soup.new_tag("b"))
                    tag.decompose()
                elif re.search('IMPLEMENTATION TABLE FOR AGE OF COMPOUNDING THE ADDITIONAL BENEFIT', tag.text.strip()):
                    p_tag = self.soup.new_tag("p")
                    p_tag['class'] = tag['class']
                    p_tag.string = 'IMPLEMENTATION TABLE FOR AGE OF COMPOUNDING THE ADDITIONAL BENEFIT'
                    tag.insert_before(p_tag)
                    tag.string = tag.text.replace(p_tag.text, '')
                elif re.search('FORM FEE Each individual policy contract, including revisions \$15\.00', tag.text.strip()):
                    p_tag = self.soup.new_tag("p")
                    p_tag['class'] = tag['class']
                    p_tag.string = 'Additional charge for tentative approval same as above. '
                    tag.insert_after(p_tag)
                    tag.string = tag.text.replace(p_tag.text, '')
            elif tag.br and len(tag.text.strip()) == 0:
                tag.decompose()

    def creating_ul_tag(self, tag, text1, pattern, ul_tag, columns=None):
        div_tag = self.soup.new_tag("div")
        if text1:
            for col in range(1, columns):
                li_tag = self.soup.new_tag("li", style="float: left;display: table-row;width: 200px;")
                li_tag['class'] = "table"
                li_tag.string = f'{text1.group(f"col{col}")}'
                li_tag.string.wrap(self.soup.new_tag("b"))
                ul_tag.append(li_tag)
            div_tag.append(ul_tag)
            tag.string = tag.text.strip().replace(text1.group(), '')
        text_1 = list(x for x in filter(None, re.split(pattern, tag.text.strip())) if x !=" ")
        ul_tag = self.soup.new_tag("ul", style='display: table;width: auto;')
        ul_tag['class'] = "table"
        count = 0
        for i in range(len(text_1)):
            li_tag = self.soup.new_tag("li", style="float: left;display: table-row;width: 200px;")
            li_tag['class'] = "table"
            li_tag.string = text_1[i]
            ul_tag.append(li_tag)
            count += 1
            if count in [2, 3, 5, 4] and columns == count+1:
                div_tag.append(ul_tag)
                ul_tag = self.soup.new_tag("ul", style='display: table;width: auto;')
                ul_tag['class'] = "table"
                count = 0
        if ul_tag.li:
            div_tag.append(ul_tag)
        tag.insert_after(div_tag)
        tag.decompose()

    def convert_paragraph_to_alphabetical_ol_tags(self):
        self.recreate_ol_tag()
        self.create_analysis_nav_tag()
        prev_li = None
        ol_count = 1
        count_of_p_tag = 1
        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
        for tag in self.soup.main.find_all(["h2", "h3", "h4", "p"]):
            if not tag.name or (tag.name == "p" and tag.find_previous(['h4','h3']) and re.search(r'^Editor([\'’]s)? Notes?\.? ?([--—–]+)?', tag.find_previous(['h4', 'h3']).text.strip(), re.I)):
                continue
            if tag.i:
                tag.i.unwrap()
            elif tag.b and tag.b.i:
                tag.b.i.unwrap()
            if tag['class'] == "text" or re.search('^a. For each application filed for the purchase of tax-forfeited', tag.text.strip()):
                continue
            next_tag = tag.find_next_sibling()
            if not next_tag:
                break
            if re.search(fr'^{self.inner_num_2}\.', tag.text.strip()):
                if re.search(fr'^{self.inner_num_2}\.\s?a\.', tag.text.strip()):
                    self.inner_alphabet = "a"
                if self.inner_num_2 == 1:
                    ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                    ol_tag_for_inner_number_2['class'] = "inner_num_2"
                if re.search(fr'^{self.inner_num_2}\.\s?{self.inner_alphabet}\.', tag.text.strip()):
                    ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                    ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    self.caps_alpha = "A"
                    tag.string = re.sub(fr'^{self.inner_num_2}\.\s?{self.inner_alphabet}\.', '', tag.text.strip())
                    tag.wrap(ol_tag_for_inner_alphabet)
                    li_tag = self.soup.new_tag("li")
                    li_tag['class'] = "inner_num_2"
                    ol_tag_for_inner_alphabet.wrap(li_tag)
                    tag['class'] = "inner_alphabet"
                    if self.inner_num_2 != 1:
                        ol_tag_for_inner_number_2.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_inner_number_2)
                    if self.roman_number != "i":
                        tag.attrs['id'] = f'{ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs["id"]}{self.inner_num_2}{self.inner_alphabet}'
                        li_tag['id'] = f'{ol_tag_for_roman.find_all("li", class_="roman")[-1].attrs["id"]}{self.inner_num_2}'
                        if self.inner_num_2 == 1:
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_inner_number_2)
                    self.inner_num_2 += 1
                    self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                elif re.search(fr'^{self.inner_num_2}\.\s?\({self.roman_number}\)', tag.text.strip()):
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^{self.inner_num_2}\.\s?\({self.roman_number}\)', '', tag.text.strip())
                    tag.wrap(ol_tag_for_roman)
                    li_tag = self.soup.new_tag("li")
                    li_tag['class'] = "inner_num_2"
                    ol_tag_for_roman.wrap(li_tag)
                    tag['class'] = "inner_alphabet"
                    if self.inner_num_2 != 1:
                        ol_tag_for_inner_number_2.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_inner_number_2)
                    if self.alphabet != "a":
                        tag.attrs['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.inner_num_2}{self.roman_number}'
                        li_tag['id'] = f'{ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].attrs["id"]}{self.inner_num_2}'
                        if self.inner_num_2 == 1:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_inner_number_2)
                    self.inner_num_2 += 1
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                else:
                    prev_li = tag
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
                    self.initialize(ol_tag_for_inner_number_2, ["inner_alphabet", "section", "sub_section"])
                    self.initialize(ol_tag_for_inner_number_2, ["caps_alpha", "section", "sub_section"])
                    self.initialize(ol_tag_for_inner_number_2, ["roman", "section", "sub_section"])
                    if re.search(r'a\.', next_tag.text.strip()):
                        self.inner_alphabet = "a"
                    if self.inner_alphabet != "a":
                        parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alphabet')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                    elif self.caps_alpha != "A":
                        parent_tag = ol_tag_for_caps_alphabet.find_all('li', class_='caps_alpha')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                    elif self.roman_number != "i":
                        parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                    elif self.outer_caps_alpha != "A":
                        parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_num_2}'
                    elif self.inner_alphabet != "a":
                        parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alphabet')[-1]
                        tag['id'] = f"{parent_tag.attrs['id']}{self.inner_num_2}"
                    else:
                        parent_tag = None
                        tag['id'] = f"{tag_id}ol{ol_count}{self.inner_num_2}"
                    if self.inner_num_2 == 1 and parent_tag:
                        parent_tag.append(ol_tag_for_inner_number_2)
                    self.inner_num_2 += 1
            elif re.search(fr'^{self.outer_caps_alpha}\. |^\({self.outer_caps_alpha}\)', tag.text.strip()) and ((self.alphabet == "a" and self.number == 1 and self.inner_num == 1) or self.outer_caps_alpha != "A"):
                self.number = 1
                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                ol_tag_for_alphabet['class'] = "alphabet"
                self.alphabet = "a"
                self.inner_num = 1
                self.roman_number = "i"
                self.inner_num_2 = 1
                self.inner_alphabet = "a"
                if re.search(fr'^(\({self.outer_caps_alpha}\)|^{self.outer_caps_alpha}\.)\s?\({self.number}\)', tag.text.strip()):
                    ol_tag_for_number = self.soup.new_tag("ol")
                    ol_tag_for_number['class'] = "number"
                    tag.name = "li"
                    tag.string = re.sub(fr'^(\({self.outer_caps_alpha}\)|^{self.outer_caps_alpha}\.)\s?\({self.number}\)', '', tag.text.strip())
                    tag.wrap(ol_tag_for_number)
                    li_tag_for_outer_caps_alpha = self.soup.new_tag("li")
                    li_tag_for_outer_caps_alpha['class'] = "outer_caps_alpha"
                    tag['class'] = "number"
                    ol_tag_for_number.wrap(li_tag_for_outer_caps_alpha)
                    if self.outer_caps_alpha != "A":
                        ol_tag_for_outer_caps_alphabet.append(li_tag_for_outer_caps_alpha)
                    else:
                        li_tag_for_outer_caps_alpha.wrap(ol_tag_for_outer_caps_alphabet)
                    li_tag_for_outer_caps_alpha['id'] = f"{tag_id}ol{ol_count}{self.outer_caps_alpha}"
                    tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.outer_caps_alpha}{self.number}"
                    if self.outer_caps_alpha == 'Z':
                        self.outer_caps_alpha = 'A'
                    else:
                        self.outer_caps_alpha = chr(ord(self.outer_caps_alpha) + 1)
                    self.number += 1
                else:
                    prev_li = tag
                    if self.outer_caps_alpha == "A":
                        ol_tag_for_outer_caps_alphabet = self.soup.new_tag("ol", type="A")
                        ol_tag_for_outer_caps_alphabet['class'] = "outer_caps_alpha"
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^{self.outer_caps_alpha}\.|^\({self.outer_caps_alpha}\)', '', tag.text.strip())
                    tag['class'] = "outer_caps_alpha"
                    if self.outer_caps_alpha != "A":
                        ol_tag_for_outer_caps_alphabet.append(tag)
                    else:
                        tag.wrap(ol_tag_for_outer_caps_alphabet)
                    tag['id'] = f"{tag_id}ol{ol_count}{self.outer_caps_alpha}"
                    self.outer_caps_alpha = chr(ord(self.outer_caps_alpha) + 1)
            elif re.search(fr'^\({self.caps_alpha}\)|^{self.caps_alpha}\.', tag.text.strip()) and tag.b:
                if re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\(i\)', tag.text.strip()):
                    self.roman_number = "i"
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                self.caps_roman = "I"
                if re.search(fr'^\({self.caps_alpha}{self.caps_alpha}?\)\s?\({self.roman_number}\)', tag.text.strip()):
                    self.inner_alphabet = "a"
                    self.inner_num_2 = 1
                    tag.name = "li"
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
                    if self.number != "i":
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    if self.caps_alpha == 'A':
                        parent_tag.append(ol_tag_for_caps_alphabet)
                    li_tag_for_caps_alpha['id'] = f"{parent_tag.attrs['id']}{self.caps_alpha}"
                    tag.attrs['id'] = f"{parent_tag.attrs['id']}{self.caps_alpha}-{self.roman_number}"
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                else:
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
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_num", "section", "sub_section"])
                    if re.search(r'^\(1\)', next_tag.text.strip()):
                        self.inner_num = 1
                    if re.search(r'^1\.', next_tag.text.strip()):
                        self.inner_num_2 = 1
                    self.initialize(ol_tag_for_caps_alphabet, ["roman", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_num_2", "section", "sub_section"])
                    self.initialize(ol_tag_for_caps_alphabet, ["inner_alphabet", "section", "sub_section"])
                    if self.inner_alphabet != "a":
                        parent_tag = ol_tag_for_inner_alphabet.find_all('li', class_='inner_alphabet')[-1]
                    elif self.roman_number != "i":
                        parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                    elif self.inner_num != 1:
                        parent_tag = ol_tag_for_inner_number.find_all('li', class_='inner_num')[-1]
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    elif self.number != 1:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    if self.caps_alpha == "A":
                        parent_tag.append(ol_tag_for_caps_alphabet)
                    tag['id'] = f"{parent_tag.attrs['id']}{self.caps_alpha}"
                    if self.caps_alpha == "Z":
                        self.caps_alpha = 'A'
                    else:
                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
            elif re.search(fr'^\(({self.number}|{self.number}-[a-z])\)|^\(({self.inner_num}|{self.inner_num}[A-Z])\)', tag.text.strip()):
                prev_li = tag
                if re.search(fr'^\(({self.inner_num}|{self.inner_num}[A-Z])\)', tag.text.strip()) and (ol_tag_for_alphabet.li or self.number != 1):
                    self.inner_alphabet = "a"
                    if self.inner_num == 1:
                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                        ol_tag_for_inner_number['class'] = "inner_num"
                    self.inner_alphabet_2 = "a"
                    if re.search(fr'^\({self.inner_num}\)\s?\(', tag.text.strip()):
                        self.caps_alpha= "A"
                        self.roman_number = "i"
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
                    elif re.search(fr'^\({self.inner_num}\)\s?\({self.roman_number}\)', tag.text.strip()):
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_roman['class'] = "roman"
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_num}\)\s?\({self.roman_number}\)', '', tag.text.strip())
                        if self.roman_number != "i":
                            ol_tag_for_roman.append(tag)
                        else:
                            tag.wrap(ol_tag_for_roman)
                        li_tag = self.soup.new_tag("li")
                        li_tag['class'] = "inner_num"
                        ol_tag_for_roman.wrap(li_tag)
                        tag['class'] = "roman"
                        if self.inner_num != 1:
                            ol_tag_for_inner_number.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_inner_number)
                        if ol_tag_for_alphabet.li:
                            tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.inner_num}-{self.roman_number}"
                            li_tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{self.inner_num}"
                            if self.inner_num == 1:
                                ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].append(ol_tag_for_inner_number)
                        else:
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.inner_num}-{self.roman_number}"
                            li_tag['id'] = f"{tag_id}ol{ol_count}{self.inner_num}"
                        self.inner_num += 1
                        self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    else:
                        num_id = re.search(fr'^\(((?P<id>{self.inner_num}|{self.inner_num}[A-Z]))\)', tag.text.strip()).group('id')
                        if re.search(r'\d+[A-Z]', num_id):
                            caps_id = re.search(r'\d+(?P<caps_id>[A-Z])', num_id)
                            num_id = re.sub('[A-Z]', f'-{caps_id.group("caps_id")}', num_id)
                        tag.name = "li"
                        tag.string = re.sub(fr'^\(({self.inner_num}|{self.inner_num}[A-Z])\)', '', tag.text.strip())
                        tag['class'] = "inner_num"
                        if self.inner_num != 1:
                            ol_tag_for_inner_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_number)
                        if re.search(R'^\(A\)', next_tag.text.strip()):
                            self.caps_alpha = "A"
                        self.initialize(ol_tag_for_inner_number, ["roman", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_number, ["caps_alpha", "section", "sub_section"])
                        if self.caps_alpha != "A":
                            parent_tag = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1]
                        elif self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all("li", class_="roman")[-1]
                        elif ol_tag_for_alphabet.li:
                            parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                        if self.inner_num == 1:
                            parent_tag.append(ol_tag_for_inner_number)
                        tag['id'] = f'{parent_tag.attrs["id"]}{num_id}'
                        sibling_tag = ol_tag_for_inner_number.find_next(lambda sib_tag: re.search(fr'^\({self.inner_num}[A-Z]\)|^HISTORY:', sib_tag.text.strip()))
                        if re.search('^HISTORY:', sibling_tag.text.strip()):
                            self.inner_num += 1
                else:
                    num_id = re.search(fr'^\(((?P<id>{self.number}|{self.number}-?[a-zA-Z]))\)', tag.text.strip()).group('id')
                    if num_id == '1':
                        ol_tag_for_number = self.soup.new_tag("ol")
                        ol_tag_for_number['class'] = "number"
                    self.alphabet = "a"
                    self.inner_alphabet_2 = "a"
                    self.caps_alpha = "A"
                    self.inner_alphabet = "a"
                    self.roman_number = "i"
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    ol_tag_for_alphabet['class'] = "alphabet"
                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                    ol_tag_for_roman['class'] = "roman"
                    self.inner_num_2 = 1
                    if re.search(fr'^\({self.number}\)\s?\({self.alphabet}\)', tag.text.strip()):
                        if re.search(fr'^\({self.number}\)\s?\({self.alphabet}\)\s?\({self.roman_number}\)', tag.text.strip()):
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
                            if self.outer_caps_alpha != "A":
                                li_tag['id'] = f'{ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1].attrs["id"]}{self.number}'
                                tag.attrs['id'] = f'{ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1].attrs["id"]}{self.number}{self.alphabet}'
                                if self.number == 1:
                                    ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1].append(ol_tag_for_number)
                            else:
                                li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}{self.alphabet}"
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.number += 1
                    elif re.search(fr'^\({self.number}\)\s?\({self.roman_number}\)', tag.text.strip()):
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
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.number}-{self.roman_number}"
                        li_tag['id'] = f"{tag_id}ol{ol_count}{self.number}"
                        self.number += 1
                        self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                    else:
                        tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.number}\)|^\({self.number}-[a-z]\)', '', tag.text.strip())
                        tag['class'] = "number"
                        if self.number != 1:
                            ol_tag_for_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_number)
                        self.initialize(ol_tag_for_number, ["caps_roman", "section", "sub_section"])
                        if self.outer_caps_alpha != "A":
                            tag['id'] = f'{ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1].attrs["id"]}{num_id}'
                            if self.number == 1:
                                ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1].append(ol_tag_for_number)
                        elif self.caps_roman != "I":
                            tag['id'] = f'{ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].attrs["id"]}{num_id}'
                            if self.number == 1:
                                ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1].append(ol_tag_for_number)
                        else:
                            tag['id'] = f"{tag_id}ol{ol_count}{num_id}"
                        sibling_tag = ol_tag_for_number.find_next(lambda sib_tag: re.search(fr'^\({self.number}-[a-z]\)|^HISTORY:', sib_tag.text.strip()))
                        if re.search('^HISTORY:', sibling_tag.text.strip()):
                            self.number += 1
            elif re.search(fr'^\({self.caps_roman}\)|^{self.caps_roman}\. ', tag.text.strip()):
                tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                prev_li = tag
                if self.caps_roman == 'I':
                    ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                    ol_tag_for_caps_roman['class'] = "caps_roman"
                tag.name = "li"
                tag.string = re.sub(fr'^\({self.caps_roman}\)|^{self.caps_roman}\.', '', tag.text.strip())
                if self.caps_roman != "I":
                    ol_tag_for_caps_roman.append(tag)
                else:
                    tag.wrap(ol_tag_for_caps_roman)
                self.initialize(ol_tag_for_caps_roman, ["number", "section", "sub_section"])
                self.initialize(ol_tag_for_caps_roman, ["alphabet", "section", "sub_section"])
                if self.roman_number != "i":
                    parent_tag = ol_tag_for_roman.find_all('li', class_='roman')[-1]
                    tag['id'] = f"{parent_tag.attrs['id']}-{self.caps_roman}"
                else:
                    parent_tag = None
                    tag['id'] = f"{tag_id}ol{ol_count}-{self.caps_roman}"
                if parent_tag and self.caps_roman == "I":
                    parent_tag.append(ol_tag_for_caps_roman)
                tag['class'] = "caps_roman"
                self.caps_roman = roman.toRoman(roman.fromRoman(self.caps_roman) + 1)
            elif re.search(fr'^\({self.roman_number}\)|^{self.roman_number}\.', tag.text.strip()) and self.alphabet != self.roman_number and self.inner_alphabet != self.roman_number:
                if re.search(fr'^\({self.roman_number}\)\s?(\(|1\.)', tag.text.strip()):
                    self.caps_alpha = "A"
                    self.inner_num_2 = 1
                if re.search(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                    ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                    ol_tag_for_caps_alphabet['class'] = "caps_alpha"
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
                    if ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    elif self.number != 1:
                        parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                    if self.roman_number == "i":
                        parent_tag.append(ol_tag_for_roman)
                    li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    tag.attrs['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{self.caps_alpha}"
                    self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                elif re.search(fr'^\({self.roman_number}\)\s?{self.inner_num_2}\.', tag.text.strip()):
                    ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                    ol_tag_for_inner_number_2['class'] = "inner_num_2"
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.roman_number}\)\s?{self.inner_num_2}\.', '', tag.text.strip())
                    tag['class'] = "inner_num_2"
                    tag.wrap(ol_tag_for_inner_number_2)
                    li_tag = self.soup.new_tag("li")
                    li_tag['class'] = "roman"
                    ol_tag_for_inner_number_2.wrap(li_tag)
                    if roman != "i":
                        ol_tag_for_roman.append(li_tag)
                    else:
                        li_tag.wrap(ol_tag_for_roman)
                    if ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                    li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                    tag.attrs['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{self.inner_num_2}"
                    if self.roman_number == "i":
                        parent_tag.append(ol_tag_for_roman)
                    self.inner_num_2 += 1
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                else:
                    prev_li = tag
                    if self.roman_number == "i":
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_roman['class'] = "roman"
                    self.inner_roman = "i"
                    tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.roman_number}\)|^{self.roman_number}\.', '', tag.text.strip())
                    tag['class'] = "roman"
                    if self.roman_number != "i":
                        ol_tag_for_roman.append(tag)
                    else:
                        tag.wrap(ol_tag_for_roman)
                    self.initialize(ol_tag_for_roman, ["caps_alpha", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["inner_num", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                    self.initialize(ol_tag_for_roman, ["inner_num_2", "section", "sub_section"])
                    if re.search(r'^\(A\)|A\.', next_tag.text.strip()):
                        self.caps_alpha = "A"
                    elif re.search(r'^1\.', next_tag.text.strip()):
                        self.inner_num_2 = 1
                    if self.caps_alpha != "A":
                        parent_tag = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif self.inner_num != 1:
                        parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif self.inner_alphabet != "a":
                        parent_tag = ol_tag_for_inner_alphabet.find_all("li", class_="inner_alphabet")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif self.inner_num_2 != 1:
                        parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif self.number != 1:
                        parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    elif self.outer_caps_alpha != "A":
                        parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                    else:
                        parent_tag = None
                        tag['id'] = f"{tag_id}ol{ol_count}-{self.roman_number}"
                    if parent_tag and self.roman_number == "i":
                        parent_tag.append(ol_tag_for_roman)
                    self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
            elif re.search(fr'^\({self.inner_roman}\)', tag.text.strip()) and self.roman_number != "i" and self.inner_roman != self.alphabet and self.inner_roman != self.inner_alphabet_2:
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
                elif ol_tag_for_alphabet.li:
                    parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                    tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                if self.inner_roman == "i":
                    parent_tag.append(ol_tag_for_inner_roman)
                self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
            elif re.search(fr'^\({self.alphabet}{{1,5}}\)|^\({self.inner_alphabet_2}\)|^{self.inner_alphabet}\.|^\(l\)', tag.text.strip()):
                if re.search(fr'^{self.inner_alphabet}\.', tag.text.strip()) or (re.search(fr'^\(l\)', tag.text.strip()) and self.inner_alphabet_2 != "l" and self.alphabet != "l"):
                    if self.inner_alphabet == "a":
                        ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                        ol_tag_for_inner_alphabet['class'] = "inner_alphabet"
                    if re.search(fr'^{self.inner_alphabet}\.\s?{self.inner_num_2}\.', tag.text.strip()):
                        ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                        ol_tag_for_inner_number_2['class'] = "inner_num_2"
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^{self.inner_alphabet}\.\s?{self.inner_num_2}\.', '', tag.text.strip())
                        tag.wrap(ol_tag_for_inner_number_2)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{tag_id}ol{ol_count}{self.inner_alphabet}"
                        li_tag['class'] = "inner_alphabet"
                        ol_tag_for_inner_number_2.wrap(li_tag)
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.inner_alphabet}{self.inner_num_2}"
                        tag['class'] = "inner_num_2"
                        if self.inner_alphabet != "a":
                            ol_tag_for_inner_alphabet.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_inner_alphabet)
                        self.inner_num_2 += 1
                        self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                    else:
                        tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.inner_alphabet}\)|^{self.inner_alphabet}\.', '', tag.text.strip())
                        tag['class'] = "inner_alphabet"
                        if self.inner_alphabet != "a":
                            ol_tag_for_inner_alphabet.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_alphabet)
                        self.initialize(ol_tag_for_inner_alphabet, ["caps_alpha", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["alphabet", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["inner_num_2", "section", "sub_section"])
                        self.initialize(ol_tag_for_inner_alphabet, ["roman", "section", "sub_section"])
                        if re.search(r'^i\.', next_tag.text.strip()) and chr(ord(self.inner_alphabet) + 1) != "i":
                            self.roman_number = "i"
                        if self.inner_num_2 != 1:
                            parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet}'
                        elif self.roman_number != "i":
                            parent_tag = ol_tag_for_roman.find_all("li", class_="roman")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet}'
                        elif self.inner_num != 1:
                            parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet}'
                        elif ol_tag_for_alphabet.li:
                            parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet}'
                        elif self.number != 1:
                            parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                            tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet}'
                        else:
                            parent_tag = None
                            tag['id'] = f'{tag_id}ol{ol_count}{self.inner_alphabet}'
                        if parent_tag and self.inner_alphabet == "a":
                            parent_tag.append(ol_tag_for_inner_alphabet)
                        self.inner_alphabet = chr(ord(self.inner_alphabet) + 1)
                elif re.search(fr'^\({self.inner_alphabet_2}\)', tag.text.strip()) and (ol_tag_for_alphabet.li or self.roman_number != "i"):
                    if self.inner_alphabet_2 == "a":
                        ol_tag_for_inner_alphabet_2 = self.soup.new_tag("ol", type="a")
                        ol_tag_for_inner_alphabet_2['class'] = "inner_alphabet_2"
                    tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({self.inner_alphabet_2}\)', '', tag.text.strip())
                    tag['class'] = "inner_alphabet_2"
                    if self.inner_alphabet_2 != "a":
                        ol_tag_for_inner_alphabet_2.append(tag)
                    else:
                        tag.wrap(ol_tag_for_inner_alphabet_2)
                    self.initialize(ol_tag_for_inner_alphabet_2, ["caps_alpha", "section", "sub_section"])
                    self.initialize(ol_tag_for_inner_alphabet_2, ["alphabet", "section", "sub_section"])
                    self.initialize(ol_tag_for_inner_alphabet_2, ["inner_num_2", "section", "sub_section"])
                    if self.inner_num_2 != 1:
                        parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet_2}'
                    elif self.roman_number != "i":
                        parent_tag = ol_tag_for_roman.find_all("li", class_="roman")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet_2}'
                    elif self.inner_num != 1:
                        parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet_2}'
                    elif ol_tag_for_alphabet.li:
                        parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                        tag['id'] = f'{parent_tag.attrs["id"]}{self.inner_alphabet_2}'
                    else:
                        parent_tag = None
                        tag['id'] = f'{tag_id}ol{ol_count}{self.inner_alphabet_2}'
                    if parent_tag and self.inner_alphabet_2 == "a":
                        parent_tag.append(ol_tag_for_inner_alphabet_2)
                    self.inner_alphabet_2 = chr(ord(self.inner_alphabet_2) + 1)
                else:
                    alpha_id = re.search(fr'^\((?P<alpha_id>{self.alphabet}{{1,5}})\)', tag.text.strip()).group('alpha_id')
                    prev_li = tag
                    if alpha_id == "a":
                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                        ol_tag_for_alphabet['class'] = "alphabet"
                    if re.search(fr'^\({self.alphabet}{{1,5}}\)\s?\(', tag.text.strip()):
                        self.inner_alphabet = "a"
                        self.inner_num = 1
                        self.inner_num_2 = 1
                        self.caps_alpha = "A"
                        self.roman_number = "i"
                        self.inner_roman = "i"
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        ol_tag_for_roman['class'] = "roman"
                    if re.search(fr'^\({self.alphabet}{{1,5}}\)\s?\({self.roman_number}\)', tag.text.strip()):
                        if re.search(fr'^\({self.alphabet}{{1,5}}\)\s?\({self.roman_number}\)\s?{self.inner_num_2}\.', tag.text.strip()):
                            ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                            ol_tag_for_inner_number_2['class'] = "inner_num"
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{self.alphabet}?\)\s?\({self.roman_number}\)\s?{self.inner_num_2}\.', '', tag.text.strip())
                            tag.wrap(ol_tag_for_inner_number_2)
                            li_tag_for_alphabet = self.soup.new_tag("li")
                            li_tag_for_alphabet['class'] = "alphabet"
                            li_tag_for_roman = self.soup.new_tag("li")
                            li_tag_for_roman['class'] = "roman"
                            ol_tag_for_inner_number_2.wrap(li_tag_for_roman)
                            li_tag_for_roman.wrap(ol_tag_for_roman)
                            ol_tag_for_roman.wrap(li_tag_for_alphabet)
                            if self.alphabet != 'a':
                                ol_tag_for_alphabet.append(li_tag_for_alphabet)
                            else:
                                li_tag_for_alphabet.wrap(ol_tag_for_alphabet)
                            tag['class'] = "inner_num_2"
                            if self.number != 1:
                                li_tag_for_alphabet['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{self.alphabet}'
                                li_tag_for_roman['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{self.alphabet}{self.roman_number}'
                                tag.attrs['id'] = f'{ol_tag_for_number.find_all("li", class_="number")[-1].attrs["id"]}{self.alphabet}{self.roman_number}-{self.inner_num_2}'
                                if self.alphabet == 'a':
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                            else:
                                li_tag_for_alphabet['id'] = f"{tag_id}ol{ol_count}{self.alphabet}"
                                li_tag_for_roman['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.roman_number}"
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{self.alphabet}{self.roman_number}-{self.inner_num_2}"
                            self.inner_num_2 += 1
                            self.alphabet = chr(ord(self.alphabet) + 1)
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                        else:
                            self.inner_num_2 = 1
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{{1,5}}\)\s?\({self.roman_number}\)', '', tag.text.strip())
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
                                parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                                li_tag['id'] = f"{parent_tag.attrs['id']}{alpha_id}"
                                tag.attrs['id'] = f"{parent_tag.attrs['id']}{alpha_id}-{self.roman_number}"
                            elif self.caps_roman != "I":
                                parent_tag = ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1]
                                li_tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}-{self.roman_number}'
                            else:
                                parent_tag = None
                                li_tag['id'] = f"{tag_id}ol{ol_count}{alpha_id}"
                                tag.attrs['id'] = f"{tag_id}ol{ol_count}{alpha_id}-{self.roman_number}"
                            if alpha_id == "a" and parent_tag:
                                parent_tag.append(ol_tag_for_alphabet)
                            self.roman_number = roman.toRoman(roman.fromRoman(self.roman_number.upper()) + 1).lower()
                            if self.alphabet == "z":
                                self.alphabet = "a"
                            else:
                                self.alphabet = chr(ord(self.alphabet) + 1)
                            sibling_tag = ol_tag_for_alphabet.find_next(
                                lambda sib_tag: re.search(r'^\([a-z]\)|^HISTORY:', sib_tag.text.strip()))
                            if not re.search(r'^HISTORY:', sibling_tag.text.strip()) and not re.search(r'^\([avxi]\)', sibling_tag.text.strip()):
                                self.alphabet = re.search(r'^\((?P<alpha>[a-z])\)', sibling_tag.text.strip()).group('alpha')
                    elif re.search(fr'^\({self.alphabet}{{1,5}}{self.alphabet}?\)\s?\({self.inner_num}\)', tag.text.strip()):
                        ol_tag_for_inner_number = self.soup.new_tag("ol")
                        ol_tag_for_inner_number['class'] = "inner_num"
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({self.alphabet}{{1,5}}\)\s?\({self.inner_num}\)', '', tag.text.strip())
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
                        if self.alphabet == "z":
                            self.alphabet = "a"
                        else:
                            self.alphabet = chr(ord(self.alphabet) + 1)
                    else:
                        if alpha_id == "i" or alpha_id == "v":
                            if alpha_id == "i":
                                sibling_of_tag = tag.find_next_sibling(lambda sibling_tag: re.search(r'^\(ii\)|^HISTORY:|^\([ij]\)', sibling_tag.text.strip()))
                            elif alpha_id == "v":
                                sibling_of_tag = tag.find_next_sibling(lambda sibling_tag: re.search(r'^\([wvi]\)|^HISTORY:', sibling_tag.text.strip()))
                            if re.search(r'^\(ii\)|^\(v\)', sibling_of_tag.text.strip()):
                                if re.search(fr'^\({self.roman_number}\)', tag.text.strip()):
                                    if re.search(fr'^\({self.roman_number}\)\s?\(A\)', tag.text.strip()):
                                        self.caps_alpha = "A"
                                    if re.search(fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', tag.text.strip()):
                                        ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                                        ol_tag_for_caps_alphabet['class'] = "caps_alpha"
                                        tag.name = "li"
                                        tag.string = re.sub(
                                            fr'^\({self.roman_number}\)\s?\({self.caps_alpha}{self.caps_alpha}?\)', '',
                                            tag.text.strip())
                                        tag['class'] = "caps_alpha"
                                        tag.wrap(ol_tag_for_caps_alphabet)
                                        li_tag = self.soup.new_tag("li")
                                        li_tag['class'] = "roman"
                                        ol_tag_for_caps_alphabet.wrap(li_tag)
                                        if roman != "i":
                                            ol_tag_for_roman.append(li_tag)
                                        else:
                                            li_tag.wrap(ol_tag_for_roman)
                                        if ol_tag_for_alphabet.li:
                                            parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                                        elif self.number != 1:
                                            parent_tag = ol_tag_for_number.find_all('li', class_='number')[-1]
                                        if self.roman_number == "i":
                                            parent_tag.append(ol_tag_for_roman)
                                        li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                                        tag.attrs[
                                            'id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{self.caps_alpha}"
                                        self.caps_alpha = chr(ord(self.caps_alpha) + 1)
                                        self.roman_number = roman.toRoman(
                                            roman.fromRoman(self.roman_number.upper()) + 1).lower()
                                    elif re.search(fr'^\({self.roman_number}\)\s?{self.inner_num_2}\.', tag.text.strip()):
                                        ol_tag_for_inner_number_2 = self.soup.new_tag("ol")
                                        ol_tag_for_inner_number_2['class'] = "inner_num_2"
                                        tag.name = "li"
                                        tag.string = re.sub(fr'^\({self.roman_number}\)\s?{self.inner_num_2}\.', '',
                                                            tag.text.strip())
                                        tag['class'] = "inner_num_2"
                                        tag.wrap(ol_tag_for_inner_number_2)
                                        li_tag = self.soup.new_tag("li")
                                        li_tag['class'] = "roman"
                                        ol_tag_for_inner_number_2.wrap(li_tag)
                                        if roman != "i":
                                            ol_tag_for_roman.append(li_tag)
                                        else:
                                            li_tag.wrap(ol_tag_for_roman)
                                        if ol_tag_for_alphabet.li:
                                            parent_tag = ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1]
                                        li_tag['id'] = f"{parent_tag.attrs['id']}-{self.roman_number}"
                                        tag.attrs[
                                            'id'] = f"{parent_tag.attrs['id']}-{self.roman_number}{self.inner_num_2}"
                                        self.inner_num_2 += 1
                                        self.roman_number = roman.toRoman(
                                            roman.fromRoman(self.roman_number.upper()) + 1).lower()
                                    else:
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
                                        self.initialize(ol_tag_for_roman, ["inner_num", "section", "sub_section"])
                                        self.initialize(ol_tag_for_roman, ["inner_alphabet", "section", "sub_section"])
                                        self.initialize(ol_tag_for_roman, ["inner_num_2", "section", "sub_section"])
                                        if re.search(r'^\(A\)|A\.', next_tag.text.strip()):
                                            self.caps_alpha = "A"
                                        elif re.search(r'^1\.', next_tag.text.strip()):
                                            self.inner_num_2 = 1
                                        if self.caps_alpha != "A":
                                            parent_tag = ol_tag_for_caps_alphabet.find_all("li", class_="caps_alpha")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif self.inner_num != 1:
                                            parent_tag = ol_tag_for_inner_number.find_all("li", class_="inner_num")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif self.inner_alphabet != "a":
                                            parent_tag = ol_tag_for_inner_alphabet.find_all("li", class_="inner_alphabet")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif self.inner_num_2 != 1:
                                            parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif ol_tag_for_alphabet.li:
                                            parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif self.number != 1:
                                            parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        elif self.outer_caps_alpha != "A":
                                            parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                                            tag['id'] = f'{parent_tag.attrs["id"]}-{self.roman_number}'
                                        else:
                                            parent_tag = None
                                            tag['id'] = f"{tag_id}ol{ol_count}-{self.roman_number}"
                                        if parent_tag and self.roman_number == "i":
                                            parent_tag.append(ol_tag_for_roman)
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
                                    elif ol_tag_for_alphabet.li:
                                        parent_tag = ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1]
                                        tag['id'] = f'{parent_tag.attrs["id"]}-{self.inner_roman}'
                                    if self.inner_roman == "i":
                                        parent_tag.append(ol_tag_for_inner_roman)
                                    self.inner_roman = roman.toRoman(roman.fromRoman(self.inner_roman.upper()) + 1).lower()
                            else:
                                self.caps_alpha = "A"
                                self.roman_number = "i"
                                self.inner_roman = "i"
                                tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({self.alphabet}{{1,5}}\)', '', tag.text.strip())
                                tag['class'] = "alphabet"
                                if alpha_id != "a":
                                    ol_tag_for_alphabet.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_alphabet)
                                self.initialize(ol_tag_for_alphabet, ["inner_num_2", "section", "sub_section"])
                                self.initialize(ol_tag_for_alphabet, ["inner_alphabet", "section", "sub_section"])
                                self.initialize(ol_tag_for_alphabet, ["inner_num", "section", "sub_section"])
                                if self.number != 1:
                                    parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                                    tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                                elif self.inner_num_2 != 1:
                                    parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
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
                                sibling_tag = ol_tag_for_alphabet.find_next(lambda sib_tag: re.search(r'^\([a-z]\)|^HISTORY:', sib_tag.text.strip()))
                                if not re.search(r'^HISTORY:', sibling_tag.text.strip()) and not re.search(r'^\([avxi]\)', sibling_tag.text.strip()):
                                    self.alphabet = re.search(r'^\((?P<alpha>[a-z])\)', sibling_tag.text.strip()).group('alpha')
                        else:
                            self.caps_alpha = "A"
                            self.roman_number = "i"
                            self.inner_roman = "i"
                            tag_id = tag.find_previous({'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({self.alphabet}{{1,5}}\)', '', tag.text.strip())
                            tag['class'] = "alphabet"
                            if alpha_id != "a":
                                ol_tag_for_alphabet.append(tag)
                            else:
                                tag.wrap(ol_tag_for_alphabet)
                            self.initialize(ol_tag_for_alphabet, ["inner_num_2", "section", "sub_section"])
                            self.initialize(ol_tag_for_alphabet, ["inner_alphabet", "section", "sub_section"])
                            self.initialize(ol_tag_for_alphabet, ["inner_num", "section", "sub_section"])
                            if re.search(r'^\(i\)', next_tag.text.strip()):
                                self.inner_num_2 = 1
                            if self.number != 1:
                                parent_tag = ol_tag_for_number.find_all("li", class_="number")[-1]
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                            elif self.inner_num_2 != 1:
                                parent_tag = ol_tag_for_inner_number_2.find_all("li", class_="inner_num_2")[-1]
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                            elif self.outer_caps_alpha != "A":
                                parent_tag = ol_tag_for_outer_caps_alphabet.find_all("li", class_="outer_caps_alpha")[-1]
                                tag['id'] = f'{parent_tag.attrs["id"]}{alpha_id}'
                            elif self.caps_roman != "I":
                                parent_tag = ol_tag_for_caps_roman.find_all("li", class_="caps_roman")[-1]
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
                            if self.alphabet != "a" and len(alpha_id) == 1:
                                sibling_tag = ol_tag_for_alphabet.find_next(lambda sib_tag: re.search(r'^\([a-z]\)|^HISTORY:|^RESEARCH REFERENCES', sib_tag.text.strip()))
                                if not re.search(r'^HISTORY:|^\([avxi]\)|^RESEARCH REFERENCES', sibling_tag.text.strip()):
                                    self.alphabet = re.search(r'^\((?P<alpha>[a-z])\)', sibling_tag.text.strip()).group('alpha')
            elif tag.name not in ['h2', 'h3', 'h4', 'h5']:
                if re.search(r'^[IVXCL]+\. [A-Z ]+', tag.text.strip()):
                    prev_li = None
                    self.alphabet = 'a'
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    self.roman_number = "i"
                    ol_count += 1
                elif re.search(r'^Section \w+\.?|^§ \d+\.|^Class \d+\. .+\. —', tag.text.strip(), re.I):
                    prev_li = None
                    self.alphabet = 'a'
                    self.outer_caps_alpha = "A"
                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                    self.number = 1
                    self.roman_number = "i"
                    ol_count += 1
                elif prev_li:
                    if re.search('^The invoice|^The payment', tag.text.strip()) and not re.search(fr'^\({self.alphabet}\)', next_tag.text.strip()):
                        self.alphabet = "a"
                    else:
                        tag.attrs['id'] = f"{prev_li['id']}.{count_of_p_tag:02}"
                        count_of_p_tag += 1
                        prev_li.append(tag)
            if tag.name in ["h2", "h3", "h4"]:
                self.alphabet = 'a'
                self.number = 1
                self.inner_alphabet = "a"
                self.roman_number = 'i'
                self.inner_num = 1
                self.inner_num_2 = 1
                self.caps_alpha = "A"
                self.outer_caps_alpha = "A"
                self.inner_roman = "i"
                self.caps_roman = "I"
                self.inner_alphabet_2 = "a"
                ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
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
            if tag.name == "p" and (re.search(r'^\([a-zA-Z0-9]+\)', tag.text.strip()) or (re.search(r'^\w\.', tag.text.strip()) and tag.b)) and tag.name != "p8":
                print(tag)

        print('ol tags added')

    def create_judicial_decision_analysis_nav_tag(self):
        analysis_num_tag = None
        a_tag_id = None
        inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
        for analysis_p_tag in self.soup.findAll('p', [self.tag_type_dict['ol_p'], self.tag_type_dict['table']]):
            if analysis_p_tag.find_previous(["h4"]):
                if re.search(r'^(JUDICIAL DECISIONS|ETHICS OPINIONS)', analysis_p_tag.find_previous(["h4", "h3"]).text.strip(), re.I):
                    text = re.sub(r'[\W_]+', '', analysis_p_tag.find_previous("h4").text.strip()).strip().lower()
                    if re.search(r'^\d+\.\s(—|– –?)\s*\w+', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        a_tag_text = re.search(r'^(?P<id>\d+)\.', analysis_p_tag.text.strip()).group("id")
                        if not re.search(r'^\d+\.\s(—|– –?)\s*\w+', analysis_p_tag.find_previous("li").text.strip()):
                            text_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(text_ul_tag)
                            analysis_num_tag.append(text_ul_tag)
                        else:
                            text_ul_tag.append(analysis_p_tag)
                        a_tag_id = f"#{analysis_p_tag.find_previous(['h3','h2']).get('id')}-{text}-{a_tag_text}"
                    elif re.search(r'^\d+(-\d+)?\.', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        analysis_num_tag = analysis_p_tag
                        if not re.search(r'^\d+(-\d+)?\.', analysis_p_tag.find_previous("li").text.strip()) or re.search(r'^1(-\d+)?\.', analysis_p_tag.text.strip()):
                            inner_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(inner_ul_tag)
                            if analysis_p_tag.find_previous("li") and re.search(r'^[IVX]+\.',  analysis_p_tag.find_previous("li").text.strip()):
                                analysis_rom_tag.append(inner_ul_tag)
                        else:
                            inner_ul_tag.append(analysis_p_tag)
                        a_tag_text = re.search(r'^(?P<id>\d+)(-\d+)?\.', analysis_p_tag.text.strip()).group("id")
                        analysis_num_tag_id = f"#{analysis_p_tag.find_previous(['h3','h2']).get('id')}-{text}-{a_tag_text}"
                        a_tag_id = analysis_num_tag_id
                    elif re.search(r'^[IVX]+\.', analysis_p_tag.text.strip()):
                        analysis_p_tag.name = "li"
                        analysis_rom_tag = analysis_p_tag
                        if re.search(r'^I\.', analysis_p_tag.text.strip()) or re.search(r'^I\.', analysis_p_tag.find_previous(['h5', 'h4']).text.strip()):
                            outer_ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                            analysis_p_tag.wrap(outer_ul_tag)
                        else:
                            outer_ul_tag.append(analysis_p_tag)
                        a_tag_text = re.search(r'^(?P<id>[IVX]+)\.', analysis_p_tag.text.strip()).group("id")
                        analysis_rom_tag_id = f"#{analysis_p_tag.find_previous(['h3','h2']).get('id')}-{text}-{a_tag_text}"
                        a_tag_id = analysis_rom_tag_id
                    elif re.search('^Analysis', analysis_p_tag.text.strip()):
                        continue
                    if analysis_p_tag.name == "li":
                        anchor = self.soup.new_tag('a', href=a_tag_id)
                        anchor.string = analysis_p_tag.text
                        analysis_p_tag.string = ''
                        analysis_p_tag.append(anchor)

    def create_analysis_nav_tag(self):
        self.create_judicial_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")

    def replace_tags_constitution(self):
        super(MSParseHtml, self).replace_tags_constitution()
        h5count = 1
        judicial_decision_id: list = []
        h2_list: list = []
        analysis_tag_id = None
        h4_count = 1
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^JUDICIAL DECISIONS', p_tag.text.strip(), re.I):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and tag.name != "h4":
                            tag.name = "h5"
                            if re.search(r'^(?P<id>\d+)(-\d+)?\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>\d+)(-\d+)?\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous(['h3','h2']).get('id')}-judicialdecisions-{tag_text}"
                            elif re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()):
                                tag_text = re.search(r'^(?P<id>[IVX]+)\.', tag.text.strip()).group("id")
                                analysis_tag_id = f"{tag.find_previous('h3').get('id')}-judicialdecisions-{tag_text}"
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
                if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    print(p_tag)
                elif p_tag.get('class') == [self.tag_type_dict["ol_p"]]:
                    if re.search(r'^Proposal and Ratification\.\s*\w+', p_tag.text.strip()) and p_tag.b:
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
                if p_tag.get("class") == [self.tag_type_dict["ol_p"]]:
                    if re.search(r"^HISTORY:", p_tag.text.strip()):
                        p_tag, new_tag = self.recreate_tag(p_tag)
                        new_tag.name = "h4"
                        sub_section_id = re.sub(r'[^a-zA-Z0-9]', '', new_tag.text.strip()).lower()
                        new_tag.attrs['id'] = f"{new_tag.find_previous_sibling(['h3', 'h2']).get('id')}-{sub_section_id}"

    def creating_table(self, pattern, tag, text=None, column=None):
        col_1 = []
        col_2 = []
        col_3 = []
        col_4 = []
        header = []
        count = 0
        if text:
            for col in range(1, column):
                header.append(f'{text.group(f"col{col}")}     ')
            tag.string = re.sub(text.group(), '', tag.text.strip())
        text_1 = list(x for x in filter(None, re.split(pattern, tag.text.strip())) if x != " ")
        for i in text_1:
            if re.search(pattern, i):
                count += 1
                if count == 1:
                    col_2.append(i)
                elif count == 2:
                    col_3.append(i)
                elif count == 3:
                    col_4.append(i)
            else:
                col_1.append(i)
                count = 0
        table = []
        for i in range(len(col_1)):
            if len(col_1) != len(col_2):
                col_2.append(' ')
            if col_3 and col_4:
                table.append([col_1[i], col_2[i], col_3[i], col_4[i]])
            else:
                table.append([col_1[i], col_2[i]])
        table = tabulate(table, headers=header, tablefmt="html", stralign="left")
        tag.insert_after(table)
        tag.decompose()

    def creating_formatted_table(self):
        for tag in self.soup.find_all("p", class_=[self.tag_type_dict['table'],self.tag_type_dict['ol_of_p']]):
            text = tag.text.strip()
            ul_tag = self.soup.new_tag("ul", style='display: table;width: auto;')
            ul_tag['class'] = "table"
            if re.search('^Plan Type A B C', tag.text.strip()):
                tag.string = 'Plan Type'
                text = text.replace(tag.text.strip(), '')
                div_tag = self.soup.new_tag("div")
                for i in re.findall('([A-Z](?![a-z])|[.\d+]+)', text):
                    li_tag = self.soup.new_tag("li", style="float: left;display: table-row;width: 200px;")
                    li_tag['class'] = "table"
                    li_tag.string = i
                    ul_tag.append(li_tag)
                    if i == 'C':
                        div_tag.append(ul_tag)
                        ul_tag = self.soup.new_tag("ul", style='display: table;width: auto;')
                        ul_tag['class'] = "table"
                div_tag.append(ul_tag)
                tag.insert_after(div_tag)
            elif re.search('^TRUE VALUE ASSESSED VALUE', tag.text.strip()):
                tag.string = 'TRUE VALUE OF HOMESTEAD ASSESSED VALUE OF HOMESTEAD HOMESTEAD EXEMPTION $ 1 – $ 1,000 $ 1 – $ 150 $ 6.00 1,001 – 2,000 151 – 300 12.00 2,001 – 3,000 301 – 450 18.00 3,001 – 4,000 451 – 600 24.00 4,001 – 5,000 601 – 750 30.00 5,001 – 6,000 751 – 900 36.00 6,001 – 7,000 901 – 1,050 42.00 7,001 – 8,000 1,051 – 1,200 48.00 8,001 – 9,000 1,201 – 1,350 54.00 9,001 – 10,000 1,351 – 1,500 60.00 10,001 – 11,000 1,501 – 1,650 66.00 11,001 – 12,000 1,651 – 1,800 72.00 12,001 – 13,000 1,801 – 1,950 78.00 13,001 – 14,000 1,951 – 2,100 84.00 14,001 – 15,000 2,101 – 2,250 90.00 15,001 – 16,000 2,251 – 2,400 96.00 16,001 – 17,000 2,401 – 2,550 102.00 17,001 – 18,000 2,551 – 2,700 108.00 18,001 – 19,000 2,701 – 2,850 114.00 19,001 – 20,000 2,851 – 3,000 120.00 20,001 – 21,000 3,001 – 3,150 126.00 21,001 – 22,000 3,151 – 3,300 132.00 22,001 – 23,000 3,301 – 3,450 138.00 23,001 – 24,000 3,451 – 3,600 144.00 24,001 – 25,000 3,601 – 3,750 150.00 25,001 – 26,000 3,751 – 3,900 156.00 26,001 – 27,000 3,901 – 4,050 162.00 27,001 – 28,000 4,051 – 4,200 168.00 28,001 – 29,000 4,201 – 4,350 174.00 29,001 – 30,000 4,351 – 4,500 180.00 30,001 – 31,000 4,501 – 4,650 186.00 31,001 – 32,000 4,651 – 4,800 192.00 32,001 – 33,000 4,801 – 4,950 198.00 33,001 – 34,000 4,951 – 5,100 204.00 34,001 – 35,000 5,101 – 5,250 210.00 35,001 – 36,000 5,251 – 5,400 216.00 36,001 – 37,000 5,401 – 5,550 222.00 37,001 – 38,000 5,551 – 5,700 228.00 38,001 – 39,000 5,701 – 5,850 234.00 39,001 – 40,000 5,581 – 6,000 240.00 40,001 – 41,000 6,001 – 6,150 246.00 41,001 – 42,000 6,151 – 6,300 252.00 42,001 – 43,000 6,301 – 6,450 258.00 43,001 – 44,000 6,451 – 6,600 264.00 44,001 – 45,000 6,601 – 6,750 270.00 45,001 – 46,000 6,751 – 6,900 276.00 46,001 – 47,000 6,901 – 7,050 282.00 47,001 – 48,000 7,051 – 7,200 288.00 48,001 – 49,000 7,201 – 7,350 294.00 49,001 and above 7,351 and above 300.00'
                text1 = re.search('(?P<col1>TRUE VALUE OF HOMESTEAD )(?P<col2>ASSESSED VALUE OF HOMESTEAD )(?P<col3>HOMESTEAD EXEMPTION)', tag.text.strip(),re.I)
                pattern = r'((?:[ \$\d,]+–[ \$\d,]+)?\d+\.00)|(–)|([\d,]+ and above)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 4)
            elif re.search('^ASSESSED VALUE HOMESTEAD OF', tag.text.strip()):
                tag.string ='ASSESSED VALUE OF HOMESTEAD HOMESTEAD EXEMPTION $ 1 - $ 150 $ 6.00 151 - 300 12.00 301 - 450 18.00 451 - 600 24.00 601 - 750 30.00 751 - 900 36.00 901 - 1,050 42.00 1,051 - 1,200 48.00 1,201 - 1,350 54.00 1,351 - 1,500 60.00 1,501 - 1,650 66.00 1,651 - 1,800 72.00 1,801 - 1,950 78.00 1,951 - 2,100 84.00 2,101 - 2,250 90.00 2,251 - 2,400 96.00 2,401 - 2,550 102.00 2,551 - 2,700 108.00 2,701 - 2,850 114.00 2,851 - 3,000 120.00 3,001 - 3,150 126.00 3,151 - 3,300 132.00 3,301 - 3,450 138.00 3,451 - 3,600 144.00 3,601 - 3,750 150.00 3,751 - 3,900 156.00 3,901 - 4,050 162.00 4,051 - 4,200 168.00 4,201 - 4,350 174.00 4,351 - 4,500 180.00 4,501 - 4,650 186.00 4,651 - 4,800 192.00 4,801 - 4,950 198.00 4,951 - 5,100 204.00 5,101 - 5,250 210.00 5,251 - 5,400 216.00 5,401 - 5,550 222.00 5,551 - 5,700 228.00 5,701 - 5,850 234.00 5,851 - 6,000 240.00 6,001 - 6,150 246.00 6,151 - 6,300 252.00 6,301 - 6,450 258.00 6,451 - 6,600 264.00 6,601 - 6,750 270.00 6,751 - 6,900 276.00 6,901 - 7,050 282.00 7,051 - 7,200 288.00 7,201 - 7,350 294.00 7,351 and above 300.00'
                text1 = re.search('(?P<col1>ASSESSED VALUE OF HOMESTEAD )(?P<col2>HOMESTEAD EXEMPTION)', tag.text.strip(),re.I)
                pattern = r'((?:-[ \$]+[\d,]+[\$ ]+)?\d+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('Percentage of Total Admitted Assets in Qualifying Ta', tag.text.strip()):
                tag.string = 'Percentage of Total Admitted Assets in Qualifying Mississippi Investments Percentage of Premium Tax Payable 1% 99% 2% 98% 3% 97% 4% 96% 5% 95% 6% 94% 7% 93% 8% 92% 9% 91% 10% 80% 15% 70% 20% 60% 25% 50%'
                text1 = re.search('(?P<col1>Percentage.+Investments )(?P<col2>Percentage .+Payable)', tag.text.strip(),re.I)
                pattern = r'(\d{1,2}%)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Operating Period ofSeasonal Ind', tag.text.strip()):
                text1 = re.search('(?P<col1>Operating.+Industry )(?P<col2>Wages Earned .+Period)', tag.text.strip(), re.I)
                pattern = r'(\d+ Times Weekly Benefit Amount)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Guarantee ?Duration', tag.text.strip()):
                text1 = re.search('(?P<col1>Guarantee ?Duration \(Years\) )(?P<col2>Weighting Factors?( for Plan Type A B C )?)', tag.text.strip(), re.I)
                pattern = r'((?:\.\d+ ?){1,3})'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Age at Disability Duration 60', tag.text.strip()):
                text1 = re.search('(?P<col1>Age at Disability )(?P<col2>Duration)', tag.text.strip(), re.I)
                pattern = r'(to age \d+|one year)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search(r'^Alcorn State University \$4,416,000.00 Delta', tag.text.strip()):
                tag.string = 'Alcorn State University $4,416,000.00 Delta State University 1,882,000.00 Jackson State University 2,396,000.00 Mississippi State University 9,810,000.00 Mississippi University for Women 1,909,000.00 Mississippi Valley State University 1,775,000.00 University of Mississippi 6,086,000.00 University of Southern Mississippi 5,971,000.00 University of Southern Mississippi–Gulf Park Campus 309,000.00 University Medical Center 3,465,000.00 Gulf Coast Research Laboratory 260,000.00 Education and Research Center 475,000.00 Division of Agriculture, Forestry and Veterinary Medicine 1,246,000.00'
                text1 = None
                pattern = r'([$\d,]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag)
            elif re.search('^2300 = Support Services', tag.text.strip()):
                text1 = None
                pattern = r'(\d+ =)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag)
            elif re.search('^Number of Students', tag.text.strip()):
                tag.string = 'Number of Students Per School Library Number of Certified School Librarians 0 — 499 Students 1/2 Full-time Equivalent Certified Librarian 500 or More Students 1 Full-time Certified Librarian'
                text1 = re.search('(?P<col1>Number.+Library )(?P<col2>Number of Certified .+Librarians)', tag.text.strip(), re.I)
                pattern = r'([\d/]+ Full-time.+?Certified Librarian)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Years of Experience Salary 0-4 years', tag.text.strip()):
                text1 = re.search('(?P<col1>Years of Experience )(?P<col2>Salary)', tag.text.strip(), re.I)
                pattern = r'((?:Over )?\d+(?:-\d+)? years)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^FORM FEE Each individual policy contract, including revisions \$15\.00', tag.text.strip()):
                text1 = re.search('(?P<col1>FORM )(?P<col2>FEE )', tag.text.strip(), re.I)
                pattern = r'([$\d]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^FUND AMOUNT.+Fund \[Deleted\]', tag.text.strip()):
                text1 = re.search('(?P<col1>FUND )(?P<col2>AMOUNT )', tag.text.strip(), re.I)
                pattern = r'(\[Deleted\]|\$\d+.\d+)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Years Exp. AAAA AAA AA A 0 40,608.00 39,444.00', tag.text.strip()):
                text1 = re.search('(?P<col1>Years Exp\. )(?P<col2>AAAA )(?P<col3>AAA )(?P<col4>AA )(?P<col5>A )', tag.text.strip(), re.I)
                pattern = r'([\d,]+.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 6)
            elif re.search('^(Chief Justice of the Supreme Court|Chief Judge of the Court of Appeals|Chancery Judges, each \$)', tag.text.strip()):
                text1 = None
                pattern = r'((?:\$ ?)?[\d,]+\.\d+)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag)
            elif re.search('^MAXIMUM CERTIFICATEDGROSS WEIGHT', tag.text.strip()):
                text1 = re.search('(?P<col1>MAXIMUM.+POUNDS )(?P<col2>FEE)', tag.text.strip(), re.I)
                pattern = r'((?:\$ )?[\d,]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^AMOUNT IN EXCESS OF LEGAL HIGHWAY WEIGHT', tag.text.strip()):
                text1 = re.search('(?P<col1>AMOUNT.+POUNDS )(?P<col2>PENALTY)', tag.text.strip(), re.I)
                pattern = r'([\d,]+ (?:(?:to [\d,]+)|(?:or more)))'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Insurer A Insurer B ', tag.text.strip()):
                text1 = re.search('(?P<col1>Insurer A )(?P<col2>Insurer B )', tag.text.strip(), re.I)
                pattern = r'(\d+% or more)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^AGE AT WHICH COMPOUNDING THE ADDITIONAL', tag.text.strip()):
                tag.string = 'PHASE AGE AT WHICH COMPOUNDING THE ADDITIONAL BENEFIT BEGINS Phase 1 Age 59 Phase 2 Age 58 Phase 3 Age 57 Phase 4 Age 56 Phase 5 Age 55'
                text1 = re.search('(?P<col1>PHASE )(?P<col2>AGE.+BEGINS)', tag.text.strip(), re.I)
                pattern = r'(Phase \d+)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Continuous Accrual Rate Accrual Rate Service', tag.text.strip()):
                tag.string = 'Continuous Service Accrual Rate (Monthly) Accrual Rate (Annually) 1 month to 3 years 12 hours per month 18 days per year 37 months to 8 years 14 hours per month 21 days per year 97 months to 15 years 16 hours per month 24 days per year Over 15 years 18 hours per month 27 days per year'
                text1 = re.search('(?P<col1>Continuous Service )(?P<col2>Accrual Rate \(Monthly\) )(?P<col3>Accrual Rate \(Annually\))', tag.text.strip(), re.I)
                pattern = r'(\d+ hours per month)|(\d+ days per year)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 4)
            elif re.search('^Sick Leave Percentage Percentage', tag.text.strip()):
                tag.string = 'Sick Leave Balance as of June 30, 1984 Percentage Converted to Personal Leave Percentage Converted to Major Medical Leave 1 – 200 hours 20% 80% 201 – 400 hours 25% 75% 401 – 600 hours 30% 70% 601 or more hours 35% 65%'
                text1 = re.search('(?P<col1>Sick Leave.+1984 )(?P<col2>Percentage.+Personal Leave )(?P<col3>Percentage.+Medical Leave)',tag.text.strip(), re.I)
                pattern = r'(\d+%)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 4)
            elif re.search('^Number Of Children Percentage Of Adjusted', tag.text.strip()):
                tag.string = 'Number Of Children Due Support Percentage Of Adjusted Gross Income That Should Be Awarded For Support 1 14% 2 20% 3 22% 4 24% 5 or more 26%'
                text1 = re.search('(?P<col1>Number Of.+Due Support )(?P<col2>Percentage.+For Support)', tag.text.strip(), re.I)
                pattern = r'(\d+[ a-z]+)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Month of Transfer', tag.text.strip()):
                text1 = re.search('(?P<col1>Month of Transfer.+)(?P<col2>Percentage.+Portion)', tag.text.strip(), re.DOTALL)
                pattern = r'(\d+%)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^Dismissal of any affidavit, complaint or charge in', tag.text.strip()):
                text1 = None
                pattern = r'((?:\$ ?)?[\d]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag)
            elif re.search('^TONS GENERATED/RELEASED', tag.text.strip()):
                text1 = re.search('(?P<col1>TONS GENERATED/RELEASED )(?P<col2>ANNUAL FEE)', tag.text.strip(), re.DOTALL)
                pattern = r'((?:\$ ?)[\d,]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search('^TONS GENERATED/RELEASED', tag.text.strip()):
                text1 = re.search('(?P<col1>TONS GENERATED/RELEASED )(?P<col2>ANNUAL FEE)', tag.text.strip(), re.DOTALL)
                pattern = r'((?:\$ ?)[\d,]+\.00)'
                self.creating_ul_tag(tag, text1, pattern, ul_tag, 3)
            elif re.search(r'^Governor \$122,160\.00 Attorney General 108,960\.00', tag.text.strip()):
                pattern = r'((?:\$)?[\d,]+\.00)'
                self.creating_table(pattern, tag, column=3)
            elif re.search('^Size of Sheet Per Page', tag.text.strip()):
                text = re.search('(?P<col1>Size of Sheet )(?P<col2>Per Page)', tag.text.strip(), re.DOTALL)
                pattern = r'((?:\$)?(?:\d+)?\.\d+)'
                self.creating_table(pattern, tag, text, 3)
            elif re.search(r'^a\. For each application filed for the purchase', tag.text.strip()):
                pattern = r'((?:\$)?(?:\d+)?\.\d+)'
                self.creating_table(pattern,tag, column=3)
            elif re.search('^Distance in Feet', tag.text.strip(), re.I):
                pattern = r'(\d+,\d+[ a-z]+)'
                text = re.search('(?P<col1>.*Distance in Feet.+Axles) (?P<col2>Maximum.+Axles)', tag.text.strip())
                self.creating_table(pattern, tag, text, 3)
            elif re.search('^GROSS COMMON PRIVATE WEIGHT OF AND COMMERCIAL', tag.text.strip()):
                tag.string = 'GROSS WEIGHT OF VEHICLE NOT TO EXCEED IN POUNDS COMMON AND CONTRACT CARRIERS OF PROPERTY PRIVATE COMMERCIAL AND NONCOMMERCIAL CARRIERS OF PROPERTY PRIVATE CARRIERS OF PROPERTY 0000-6000 $7.20 $7.20 $7.20 6001-10000 33.60 25.20 16.80 10001-16000 78.40 70.70 39.20 16001-20000 156.00 129.00 78.00 20001-26000 228.00 192.00 114.00 26001-30000 300.00 247.00 150.00 30001-36000 384.00 318.00 192.00 36001-40000 456.00 378.00 228.00 40001-42000 504.00 420.00 264.00 42001-44000 528.00 444.00 276.00 44001-46000 552.00 456.00 282.00 46001-48000 588.00 492.00 300.00 48001-50000 612.00 507.00 312.00 50001-52000 660.00 540.00 336.00 52001-54000 684.00 564.00 348.00 54001-56000 708.00 588.00 360.00 56001-58000 756.00 624.00 384.00 58001-60000 780.00 642.00 396.00 60001-62000 828.00 828.00 420.00 62001-64000 852.00 852.00 432.00 64001-66000 900.00 900.00 482.00 66001-68000 936.00 936.00 504.00 68001-70000 972.00 972.00 516.00 70001-72000 996.00 996.00 528.00 72001-74000 1,128.00 1,128.00 576.00 74001-76000 1,248.00 1,248.00 612.00 76001-78000 1,380.00 1,380.00 720.00 78001-80000 1,512.00 1,512.00 864.00'
                text = re.search('(?P<col1>GROSS WEIGHT.+POUNDS )(?P<col2>COMMON.+PROPERTY )(?P<col3>PRIVATE.+PROPERTY )(?P<col4>PRIVATE.+PROPERTY )', tag.text.strip(), re.I)
                pattern = r'(\$?[\d,]+\.\d+)'
                self.creating_table(pattern, tag, text, 5)
