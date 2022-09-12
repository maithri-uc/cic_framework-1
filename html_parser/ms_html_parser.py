"""
    - this file accepts the text util generated html and parse it
    - here the html is converted in such a way that it matches the html5 standards
    - the run method is calls the run_title or run_constitution method of ParseHtml class
    - this method based on the file type(constitution files or title files) decides which methods to run
"""

import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns, CustomisedRegexMS
import roman
from loguru import logger


class MSParseHtml(ParseHtml, RegexPatterns):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):
        """directory to store regex patterns """
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict = {
                'head1': r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES',
                'ul': r'^Preamble', 'head2': '^Article I',
                'junk1': '^Text$',
                'head3': r'^§ \d\.', 'ol_of_i': '^—', 'head4': r'Compiler’s Notes\.', 'ol_p': r'HISTORY:'}

            self.h2_order = ['article', '', '', '', '']
            self.h2_text_con: list = ['Articles of Amendment']
        else:
            self.tag_type_dict: dict = {'head1': r'^Title \d+', 'ul': r'^Chapter \d+',
                                        'head2': r'^Chapter \d+', 'ol_p': r'HISTORY:',
                                        'head4': r'Cross References —',
                                        'head3': r'^§§? \d+-\d+-\d+',
                                        'junk1': '^Text|^Annotations',  'ol_of_i': r'\([A-Z a-z0-9]\)'}

            file_no = re.search(r'gov\.ms\.code\.title\.(?P<fno>[\w.]+)\.html', self.input_file_name).group("fno")
            if file_no in ['01', '05']:
                self.h2_order = ['chapter', '', '', '', '']
        self.h4_head: list = ['Editor’s Notes —', 'Editor\'s Notes —', 'Cross References —', 'Comparable Laws from other States —', 'Amendment Notes — ', 'ATTORNEY GENERAL OPINIONS', 'RESEARCH REFERENCES','CJS.','Amendment Notes —',
                              'OPINIONS OF THE ATTORNEY GENERAL','Am. Jur.', 'Lawyers’ Edition.', 'Joint Legislative Committee Note —', 'JUDICIAL DECISIONS','Law Reviews.', 'ALR.']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']

        self.watermark_text = """Release {0} of the Official Code of Mississippi Annotated released {1}. 
        Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
        This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexMS()

    def recreate_tag(self, p_tag):
        new_tag = self.soup.new_tag("p")
        text = p_tag.b.text
        new_tag.string = text
        new_tag['class'] = p_tag['class']
        p_tag.insert_before(new_tag)
        p_tag.string = re.sub(f'{text}', '', p_tag.text.strip())
        return p_tag, new_tag

    def replace_tags_titles(self):
        """
            - regex_pattern_obj  for customised regex class is created
            - h2_order list which has order of h2 tags created
            - calling method of base class
            - replacing all other tags which are not handled in the base class

        """
        super(MSParseHtml, self).replace_tags_titles()
        h4_count = 1
        h5count = 1
        judicial_decision_list: list = []
        judicial_decision_id: list = []
        case_tag = None
        count = 1
        inner_case_tag = None
        h2_list: list = []
        for p_tag in self.soup.find_all():
            if p_tag.name == "h4":
                if re.search(r'^JUDICIAL DECISIONS', p_tag.text.strip()):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["ol_p"]]:
                            tag.name = "li"
                            tag["class"] = "note"
                            judicial_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict["head4"]] and tag.b and tag.name != "h4":
                            if tag.text.strip() in judicial_decision_list:
                                tag.name = "h5"
                                tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                tag_id = f'{tag.find_previous("h3").get("id")}-judicialdecision-{tag_text}'

                                if tag_id in judicial_decision_id:
                                    tag["id"] = f'{tag_id}.{h5count:02}'
                                    h5count += 1
                                else:
                                    tag["id"] = f'{tag_id}'
                                    h5count = 1
                                judicial_decision_id.append(tag_id)
                            else:
                                tag.name = "h5"
                                case_tag = tag
                                tag_text = re.sub(r'[\W\s]+', '', tag.text.strip()).lower()
                                tag_id = f'{tag.find_previous("h3").get("id")}-judicialdecision-{tag_text}'

                                if tag_id in judicial_decision_id:
                                    tag["id"] = f'{tag_id}.{h5count:02}'
                                    h5count += 1
                                else:
                                    tag["id"] = f'{tag_id}'
                                    h5count = 1
                                judicial_decision_id.append(tag_id)
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
                    elif re.search(r"^Section \d+. [a-z ,\-A-Z]+\. \(a\)", p_tag.text.strip()) and re.search(r"^\(b\)", p_tag.find_next_sibling().text.strip()):
                        text_from_b = p_tag.text.split('(a)')
                        p_tag_for_section = self.soup.new_tag("p")
                        p_tag_for_section.string = text_from_b[0]
                        p_tag.string = f"{p_tag.text.strip().replace(f'{text_from_b[0]}', '')}"
                        p_tag.insert_before(p_tag_for_section)
                        p_tag_for_section.attrs['class'] = p_tag['class']
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
            elif p_tag.name == "li" and not re.search('^Chapter \d+|^§§? \d+-\d+-\d+',p_tag.text.strip()) and p_tag.get('class')!= "note":
                h2_list.append(p_tag.text.strip())
                self.c_nav_count+=1
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

    @staticmethod
    def add_p_tag_to_li(tag, next_tag, count_of_p_tag):
        sub_tag = next_tag.find_next_sibling()
        next_tag['id'] = f"{tag['id']}.{count_of_p_tag}"
        tag.append(next_tag)
        next_tag['class'] = "text"
        count_of_p_tag += 1
        next_tag = sub_tag
        return next_tag, count_of_p_tag

    @staticmethod
    def decompose_tag(next_tag):
        sub_tag = next_tag.find_next_sibling()
        next_tag.decompose()
        return sub_tag

    def split_tag(self, tag, split_attr):
        text_from_b = tag.text.split(split_attr)
        p_tag = self.soup.new_tag("p")
        if split_attr in ['.', ':']:
            p_tag.string = f'{text_from_b[0]}{split_attr}'
            tag.string = tag.text.replace(f'{text_from_b[0]}{split_attr}', '')
        else:
            p_tag.string = f'{text_from_b[0]}:'
            tag.string = tag.text.replace(f'{text_from_b[0]}:', '')
        tag.insert_before(p_tag)
        p_tag.attrs['class'] = tag['class']

    def recreate_ol_tag(self):
        for tag in self.soup.main.find_all("p"):
            class_name = tag['class'][0]
            if class_name == self.tag_type_dict['ol_p'] or class_name == self.tag_type_dict['ol_of_i'] or class_name == self.tag_type_dict['head4']:
                if re.search(r'^\(\w\)\s[A-Za-z,; ]+\.\s*\(\w\)', tag.text.strip(), re.IGNORECASE) and tag.b:
                    self.split_tag(tag, '.')
                elif re.search(r'^[A-Za-z ]+:\s*\(\w\)', tag.text.strip(), re.IGNORECASE):
                    self.split_tag(tag, ':')
                elif re.search(r'^\(([a-zA-Z]|\d+)\)\s(\(\w\) )?.+:\s\(\w\)', tag.text.strip()):
                    text = re.search(r'^\(([a-zA-Z]|\d+)\)\s(\((?P<id>\w)\) )?.+:\s\((?P<text>\w)\)', tag.text.strip())
                    alpha = text.group('id')
                    text = text.group('text')
                    text_string = text
                    if text in ['a', 'A']:
                        text = chr(ord(text) + 1)
                    elif text == '1':
                        text = int(text)+1
                    elif text == 'i':
                        text = roman.fromRoman(text.upper())
                        text += 1
                        text = roman.toRoman(text).lower()
                    elif text == 'I':
                        text = roman.fromRoman(text)
                        text += 1
                        text = roman.toRoman(text)
                    if re.search(fr'^\({text}\)', tag.find_next_sibling().text.strip()) and alpha != text_string:
                        self.split_tag(tag, f': ({text_string})')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        self.recreate_ol_tag()
        for tag in self.soup.main.find_all(["h2", "h3", "h4", "p", "h5"]):
            if not tag.name:
                continue
            class_name = tag['class'][0]
            if tag.name in ["h2", "h3", "h4", "h5"]:
                alphabet = 'a'
                number = 1
                roman_number = 'i'
                inner_roman = 'i'
                caps_alpha = 'A'
                inner_num = 1
                caps_roman = 'I'
                inner_alphabet = 'a'
                ol_count = 1
                ol_tag_for_roman = self.soup.new_tag("ol", type='i')
                ol_tag_for_number = self.soup.new_tag("ol")
                ol_tag_for_alphabet = self.soup.new_tag("ol", type='a')
                ol_tag_for_caps_alphabet = self.soup.new_tag("ol", type="A")
                ol_tag_for_caps_roman = self.soup.new_tag("ol", type="I")
                ol_tag_for_inner_number = self.soup.new_tag("ol")
                ol_tag_for_inner_roman = self.soup.new_tag("ol", type="i")
                ol_tag_for_inner_alphabet = self.soup.new_tag("ol", type="a")
                ol_tag_for_inner_caps_roman = self.soup.new_tag("ol", type="I")
                inner_caps_roman = 'I'
                count_of_p_tag = 1
            elif class_name == self.tag_type_dict['ol_p'] or class_name == self.tag_type_dict['ol_of_i'] or class_name == self.tag_type_dict['head4']:
                if tag.i and re.search(r'\(<i>.\s*</i>\s*\)', str(tag)):
                    tag.i.string = re.sub(r'\s+', '', tag.i.text)
                    tag.i.unwrap()
                next_tag = tag.find_next_sibling()
                if not next_tag:  # last tag
                    break
                if next_tag.next_element.name and next_tag.next_element.name == 'br':
                    next_tag.decompose()
                    next_tag = tag.find_next_sibling()
                if re.search(fr'^{number}\.', tag.text.strip()):
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^{number}\.', '', tag.text.strip())
                    tag['class'] = "number"
                    if ol_tag_for_roman.li:
                        tag['id'] = f"{ol_tag_for_roman.find_all('li', class_='roman')[-1].attrs['id']}{number}"
                    tag.wrap(ol_tag_for_number)
                    number += 1
                    while (next_tag.name not in ["h3", "h4", "h2", "h5"]) and (
                            re.search('^“?[a-z A-Z]+', next_tag.text.strip()) or next_tag.next_element.name == "br"):
                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                            next_tag = self.decompose_tag(next_tag)
                        elif re.search(fr'^{caps_alpha}{caps_alpha}?\.|^{inner_alphabet}\.', next_tag.text.strip()):
                            break
                        else:
                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                    count_of_p_tag = 1
                    if next_tag.name in ["h3", "h4", "h2", "h5"]:
                        if ol_tag_for_roman.li:
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_number)
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                        else:

                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                    elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                        if ol_tag_for_roman.li:
                            ol_tag_for_roman.find_all("li", class_="roman")[-1].append(ol_tag_for_number)
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = "i"
                        else:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_number)
                            ol_tag_for_number = self.soup.new_tag("ol")
                            number = 1
                    elif re.search(fr'^\({roman_number}\)', next_tag.text.strip()):
                        ol_tag_for_roman.find_all("li",class_="roman")[-1].append(ol_tag_for_number)
                        ol_tag_for_number=self.soup.new_tag("ol")
                        number=1
                elif re.search(fr'^\({roman_number}\)', tag.text.strip()) and (ol_tag_for_alphabet.li and alphabet != roman_number) :
                    tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                    tag.name = "li"
                    tag.string = re.sub(fr'^\({roman_number}\)', '', tag.text.strip())
                    if ol_tag_for_roman.li:
                        ol_tag_for_roman.append(tag)
                    else:
                        tag.wrap(ol_tag_for_roman)
                    tag['class'] = "roman"
                    if ol_tag_for_alphabet.li:
                        tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}-{roman_number}"
                    elif ol_tag_for_number.li:
                        tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}-{roman_number}"
                    else:
                        tag['id'] = f"{tag_id}ol{ol_count}-{roman_number}"
                    roman_number = roman.fromRoman(roman_number.upper())
                    roman_number += 1
                    roman_number = roman.toRoman(roman_number).lower()
                    while next_tag.name not in ["h3", "h4", "h2", "h5"] and (re.search(
                            r'^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\(\d+\)|^\([a-z]+\)',
                            next_tag.text.strip()) or (
                                                                                     next_tag.next_element and next_tag.next_element.name == "br")):
                        if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                            next_tag = self.decompose_tag(next_tag)
                        elif re.search(
                                r"^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\([a-z]+\)|^\(\d+\)",
                                next_tag.text.strip()):
                            if re.search(fr'^{inner_alphabet}{inner_alphabet}?\.', next_tag.text.strip()):
                                break
                            elif re.search(r'^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                roman_id = re.search(r'^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',
                                                     next_tag.text.strip()).group('roman_id')
                                if roman_id != roman_number and roman_id != alphabet:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                else:
                                    break
                            elif re.search(r"^“?[a-z A-Z]+|^\[[A-Z a-z]+|^\([\w ]{4,}", next_tag.text.strip()):
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)

                            elif re.search(r"^\([A-Z]{1,2}\)", next_tag.text.strip()):
                                alpha_id = re.search(r"^\((?P<alpha_id>[A-Z]+)\)", next_tag.text.strip()).group(
                                    'alpha_id')
                                if alpha_id[
                                    0] != caps_alpha and alpha_id != caps_roman and alpha_id != inner_caps_roman:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                else:
                                    break
                            elif re.search(r"^\([a-z]{1,2}\)", next_tag.text.strip()):
                                alpha_id = re.search(r"^\((?P<alpha_id>[a-z]+)\)", next_tag.text.strip()).group(
                                    'alpha_id')
                                if alpha_id[0] != alphabet and alpha_id[0] != inner_alphabet:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                else:
                                    break
                            elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                    'number_id')
                                if number_id != str(number) and number_id != str(inner_num):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                else:
                                    break
                    count_of_p_tag = 1
                    if re.search(fr'^\({number}\)', next_tag.text.strip()) and number != 1:
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = 'i'
                            ol_tag_for_alphabet = self.soup.new_tag("ol",type="a")
                            alphabet = "a"
                        else:
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = 'i'
                    elif re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()) and alphabet != "a":
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                            ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                            roman_number = 'i'
                    elif re.search(fr'^\({inner_alphabet}\)|^{inner_alphabet}{inner_alphabet}?\.',
                                   next_tag.text.strip()) and inner_alphabet != 'a':
                        ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(ol_tag_for_roman)
                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                        roman_number = "i"
                    elif next_tag.name in ["h3", "h4", "h2", "h5"]:
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_roman)
                            if ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li",class_="number")[-1].append(ol_tag_for_alphabet)
                        elif ol_tag_for_number.li:
                            ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                elif re.search(fr'^\({number}\)|^\({inner_num}\)',tag.text.strip()):
                    if re.search(fr'^\({number}\)', tag.text.strip()) and not ol_tag_for_alphabet.li:
                        if re.search(fr'^\({number}\)\s?\({alphabet}{alphabet}?\)', tag.text.strip()):
                            alpha_id = re.search(fr'\((?P<alpha_id>{alphabet}{alphabet}?)\)', tag.text.strip()).group('alpha_id')
                            tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\)\s?\({alphabet}{alphabet}?\)', '', tag.text.strip())
                            tag.wrap(ol_tag_for_alphabet)
                            li_tag = self.soup.new_tag("li")
                            li_tag['id'] = f"{tag_id}ol{ol_count}{number}"
                            li_tag['class'] = "number"
                            ol_tag_for_alphabet.wrap(li_tag)
                            tag.attrs['id'] = f"{tag_id}ol{ol_count}{number}{alpha_id}"
                            tag['class'] = "alphabet"
                            li_tag.wrap(ol_tag_for_number)
                            number += 1
                            alphabet = chr(ord(alphabet) + 1)
                            while (re.search(r"^[a-z A-Z]+|^\([\w ]{4,}",
                                             next_tag.text.strip()) or next_tag.next_element.name == "br") and next_tag.name != "h4" and next_tag.name != "h3":
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                else:
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            count_of_p_tag = 1
                            if re.search(fr'^\({number}\)', next_tag.text.strip()) :
                                ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                                ol_tag_for_alphabet = self.soup.new_tag("ol",type="a")
                                alphabet = "a"
                        else:
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({number}\)', '', tag.text.strip())
                            tag['class'] = "number"
                            tag['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{number}"

                            if ol_tag_for_number.li:
                                ol_tag_for_number.append(tag)
                            else:
                                tag.wrap(ol_tag_for_number)
                            number += 1
                            while next_tag.name != "h4" and next_tag.name != "h5" and next_tag.name != "h3" and (re.search(
                                    r"^[a-z A-Z]+|^\((ix|iv|v?i{0,3})\)|^\(\d+\)|^\([a-z]+\)|^\([A-Z]+\)",
                                    next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search(
                                        r"^\([a-z]+\)|^[a-z A-Z]+|^\(\d+\)|^\((ix|iv|v?i{0,3})\)|^\([A-Z]+\) ",
                                        next_tag.text.strip()):

                                    if re.search(r'^\([a-z]{1,2}\)', next_tag.text.strip()):
                                        alphabet_id = re.search(r'^\((?P<alphabet_id>([a-z]+))\)',
                                                                next_tag.text.strip()).group('alphabet_id')
                                        if alphabet_id[0] != alphabet and alphabet_id[
                                            0] != inner_alphabet and alphabet_id != roman_number and alphabet_id != inner_roman:
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                        else:
                                            break
                                    elif re.search(
                                            r"^[a-z A-Z]+",
                                            next_tag.text.strip()):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    elif re.search(r'^\(\d+\)', next_tag.text.strip()):
                                        number_id = re.search(r'^\((?P<number_id>(\d+))\)', next_tag.text.strip()).group(
                                            'number_id')
                                        if number_id != str(number) and number_id != str(inner_num):
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                        else:
                                            break

                                    elif re.search(r'^\([A-Z]{1,2}\) ', next_tag.text.strip()):
                                        alphabet_id = re.search(r'^\((?P<alphabet_id>([A-Z]+))\)',
                                                                next_tag.text.strip()).group('alphabet_id')
                                        if alphabet_id != caps_alpha and alphabet_id != caps_roman and alphabet_id != inner_caps_roman:
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                        else:
                                            break
                            count_of_p_tag = 1
                    else:
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({inner_num}\)', '', tag.text.strip())
                        if ol_tag_for_inner_number.li:
                            ol_tag_for_inner_number.append(tag)
                        else:
                            tag.wrap(ol_tag_for_inner_number)

                        if ol_tag_for_alphabet.li:
                            tag.attrs['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}{inner_num}"

                        tag['class'] = "inner_num"
                        inner_num = inner_num + 1
                        while (re.search(r'^“?[a-z A-Z]+|^\(\d+\)', next_tag.text.strip()) or (
                                next_tag.next_element and next_tag.next_element.name == "br")) and next_tag.name not in [
                            "h3", "h4", "h2", "h5"]:
                            if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                next_tag = self.decompose_tag(next_tag)
                            elif re.search("^“?[a-z A-Z]+",
                                           next_tag.text.strip()) and next_tag.name not in ["h3", "h4", "h2", "h5"]:
                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                            elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                number_id = re.search(r"^\((?P<number_id>\d+)\)", next_tag.text.strip()).group(
                                    'number_id')
                                if number_id != str(number) and number_id != str(inner_num):
                                    next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                else:
                                    break
                        count_of_p_tag = 1

                        if re.search(fr'^\({alphabet}{alphabet}?\)', next_tag.text.strip()):
                            ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(ol_tag_for_inner_number)
                            ol_tag_for_inner_number = self.soup.new_tag("ol")
                            inner_num = 1
                        elif next_tag.name in ["h3", "h4", "h2", "h5"]:
                            if ol_tag_for_alphabet.li:
                                ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                    ol_tag_for_inner_number)
                elif re.search(fr'^\({alphabet}{alphabet}?\)|^\({inner_alphabet}\)', tag.text.strip()):
                    if re.search(fr'^\({alphabet}{alphabet}?\)\s?\({roman_number}\)', tag.text.strip()):
                        tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                        tag.name = "li"
                        tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)\s?\({roman_number}\)', '', tag.text.strip())
                        tag.wrap(ol_tag_for_roman)
                        li_tag = self.soup.new_tag("li")
                        li_tag['id'] = f"{tag_id}ol{ol_count}{alphabet}"
                        li_tag['class'] = "alphabet"
                        ol_tag_for_roman.wrap(li_tag)
                        tag.attrs['id'] = f"{tag_id}ol{ol_count}{alphabet}-{roman_number}"
                        tag['class'] = "roman"
                        if ol_tag_for_alphabet.li:
                            ol_tag_for_alphabet.append(li_tag)
                        else:
                            li_tag.wrap(ol_tag_for_alphabet)
                        roman_number = roman.fromRoman(roman_number.upper())
                        roman_number += 1
                        roman_number = roman.toRoman(roman_number).lower()
                        alphabet = chr(ord(alphabet) + 1)
                    else:
                        alpha_id = re.search(fr'^\((?P<alpha_id>{alphabet}{alphabet}?)\)', tag.text.strip()).group(
                            'alpha_id')
                        if alphabet == "i" :
                            sibling_of_i = tag.find_next_sibling(
                                lambda sibling_tag: re.search(r'^\(ii\)|^HISTORY:|^\(i\)',
                                                              sibling_tag.text.strip()))
                            if re.search(r'^\(ii\)', sibling_of_i.text.strip()):
                                tag_id = tag.find_previous({'h5', 'h4', 'h3'}).get('id')
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({roman_number}\)', '', tag.text.strip())
                                if ol_tag_for_roman.li:
                                    ol_tag_for_roman.append(tag)
                                else:
                                    tag.wrap(ol_tag_for_roman)
                                tag['class'] = "roman"
                                if ol_tag_for_alphabet.li:
                                    tag['id'] = f"{ol_tag_for_alphabet.find_all('li', class_='alphabet')[-1].attrs['id']}-{roman_number}"
                                elif ol_tag_for_number.li:
                                    tag['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}-{roman_number}"
                                else:
                                    tag['id'] = f"{tag_id}ol{ol_count}-{roman_number}"
                                roman_number = roman.fromRoman(roman_number.upper())
                                roman_number += 1
                                roman_number = roman.toRoman(roman_number).lower()
                                while next_tag.name not in ["h3", "h4", "h2", "h5"] and (re.search(
                                        r'^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\(\d+\)|^\([a-z]+\)',
                                        next_tag.text.strip()) or (
                                                                                                 next_tag.next_element and next_tag.next_element.name == "br")):
                                    if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                        next_tag = self.decompose_tag(next_tag)
                                    elif re.search(
                                            r"^“?[a-z A-Z]+|^\([\w ]{4,}|^\[[A-Z a-z]+|^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)|^\([A-Z]+\)|^\([a-z]+\)|^\(\d+\)",
                                            next_tag.text.strip()):
                                        if re.search(fr'^{inner_alphabet}{inner_alphabet}?\.', next_tag.text.strip()):
                                            break
                                        elif re.search(r'^\((xc|xl|l?x{0,3})(ix|iv|v?i{0,3})\)', next_tag.text.strip()):
                                            roman_id = re.search(r'^\((?P<roman_id>(xc|xl|l?x{0,3})(ix|iv|v?i{0,3}))\)',
                                                                 next_tag.text.strip()).group('roman_id')
                                            if roman_id != roman_number and roman_id != alphabet:
                                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                                count_of_p_tag)
                                            else:
                                                break
                                        elif re.search(r"^“?[a-z A-Z]+|^\[[A-Z a-z]+|^\([\w ]{4,}",
                                                       next_tag.text.strip()):
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                            count_of_p_tag)

                                        elif re.search(r"^\([A-Z]{1,2}\)", next_tag.text.strip()):
                                            alpha_id = re.search(r"^\((?P<alpha_id>[A-Z]+)\)",
                                                                 next_tag.text.strip()).group(
                                                'alpha_id')
                                            if alpha_id[
                                                0] != caps_alpha and alpha_id != caps_roman and alpha_id != inner_caps_roman:
                                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                                count_of_p_tag)
                                            else:
                                                break
                                        elif re.search(r"^\([a-z]{1,2}\)", next_tag.text.strip()):
                                            alpha_id = re.search(r"^\((?P<alpha_id>[a-z]+)\)",
                                                                 next_tag.text.strip()).group(
                                                'alpha_id')
                                            if alpha_id[0] != alphabet and alpha_id[0] != inner_alphabet:
                                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                                count_of_p_tag)
                                            else:
                                                break
                                        elif re.search(r"^\(\d+\)", next_tag.text.strip()):
                                            number_id = re.search(r"^\((?P<number_id>\d+)\)",
                                                                  next_tag.text.strip()).group(
                                                'number_id')
                                            if number_id != str(number) and number_id != str(inner_num):
                                                next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                                count_of_p_tag)
                                            else:
                                                break
                                count_of_p_tag = 1
                                if re.search(fr'^\({number}\)', next_tag.text.strip()) and number != 1:
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_alphabet)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = 'i'
                                        ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                        alphabet = "a"
                                    else:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = 'i'
                                elif re.search(fr'^\({roman_number}\)',next_tag.text.strip()):
                                    continue
                                elif re.search(fr'^\({alphabet}{alphabet}?\)',next_tag.text.strip()) and alphabet != "a":
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                        ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                        roman_number = 'i'
                                elif re.search(fr'^\({inner_alphabet}\)|^{inner_alphabet}{inner_alphabet}?\.',
                                               next_tag.text.strip()) and inner_alphabet != 'a':
                                    ol_tag_for_inner_alphabet.find_all("li", class_="inner_alpha")[-1].append(
                                        ol_tag_for_roman)
                                    ol_tag_for_roman = self.soup.new_tag("ol", type="i")
                                    roman_number = "i"
                                elif next_tag.name in ["h3", "h4", "h2", "h5"]:
                                    if ol_tag_for_alphabet.li:
                                        ol_tag_for_alphabet.find_all("li", class_="alphabet")[-1].append(
                                            ol_tag_for_roman)
                                        if ol_tag_for_number.li:
                                            ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                                ol_tag_for_alphabet)
                                    elif ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_roman)
                            else:
                                tag.name = "li"
                                tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)', '', tag.text.strip())
                                if ol_tag_for_number.li:
                                    tag.attrs['id'] = f"{ol_tag_for_number.find_all('li', class_='number')[-1].attrs['id']}{alpha_id}"
                                else:
                                    tag.attrs['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{alpha_id}"
                                tag.wrap(ol_tag_for_alphabet)
                                if alphabet == "z":
                                    alphabet = 'a'
                                else:
                                    alphabet = chr(ord(alphabet) + 1)
                                tag['class'] = "alphabet"
                                while (next_tag.name != "h4" and next_tag.name != "h3") and (
                                        re.search(r'^\(\d+\)|^[a-z A-Z]+', next_tag.text.strip()) or (
                                        next_tag.next_element and next_tag.next_element.name == "br")):
                                    if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                        next_tag = self.decompose_tag(next_tag)
                                    elif re.search(fr'^\(\d+\)', next_tag.text.strip()):
                                        number_id = re.search(fr'^\((?P<number_id>\d+)\)', next_tag.text.strip()).group(
                                            'number_id')
                                        if number_id != str(number) and number != str(inner_num):
                                            next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag,
                                                                                            count_of_p_tag)
                                        else:
                                            break
                                count_of_p_tag = 1
                                if re.search(fr'^\({number}\)', next_tag.text.strip()) and ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li", class_="number")[-1].append(ol_tag_for_alphabet)
                                    ol_tag_for_alphabet = self.soup.new_tag("ol", type="a")
                                    alphabet = 'a'
                                elif next_tag.name in ["h3", "h4", "h5"]:
                                    if ol_tag_for_number.li:
                                        ol_tag_for_number.find_all("li", class_="number")[-1].append(
                                            ol_tag_for_alphabet)
                        else:
                            tag.name = "li"
                            tag.string = re.sub(fr'^\({alphabet}{alphabet}?\)', '', tag.text.strip())
                            if ol_tag_for_number.li:
                                tag.attrs['id'] = f"{ol_tag_for_number.find_all('li',class_='number')[-1].attrs['id']}{alpha_id}"
                            else:
                                tag.attrs['id'] = f"{tag.find_previous({'h5', 'h4', 'h3', }).get('id')}ol{ol_count}{alpha_id}"
                            tag.wrap(ol_tag_for_alphabet)
                            if alphabet == "z":
                                alphabet = 'a'
                            else:
                                alphabet = chr(ord(alphabet) + 1)
                            tag['class'] = "alphabet"
                            while (next_tag.name != "h4" and next_tag.name != "h3") and (re.search(r'^\(\d+\)|^[a-z A-Z]+', next_tag.text.strip()) or (next_tag.next_element and next_tag.next_element.name == "br")):
                                if next_tag.next_element.name == "br" or next_tag.get('class') == [self.tag_type_dict["junk1"]]:
                                    next_tag = self.decompose_tag(next_tag)
                                elif re.search(fr'^\(\d+\)', next_tag.text.strip()):
                                    number_id = re.search(fr'^\((?P<number_id>\d+)\)', next_tag.text.strip()).group(
                                        'number_id')
                                    if number_id != str(number) and number != str(inner_num):
                                        next_tag, count_of_p_tag = self.add_p_tag_to_li(tag, next_tag, count_of_p_tag)
                                    else:
                                        break
                            count_of_p_tag = 1
                            if re.search(fr'^\({number}\)',next_tag.text.strip()) and ol_tag_for_number.li:
                                ol_tag_for_number.find_all("li",class_="number")[-1].append(ol_tag_for_alphabet)
                                ol_tag_for_alphabet=self.soup.new_tag("ol",type="a")
                                alphabet = 'a'
                            elif next_tag.name in ["h3","h4","h5"]:
                                if ol_tag_for_number.li:
                                    ol_tag_for_number.find_all("li",class_="number")[-1].append(ol_tag_for_alphabet)

        for tag in self.soup.main.find_all(["li", "p"]):
            if (tag.name == "li" and tag['class'] != "note") or (tag.name == "p" and tag['class'] == "text"):
                del tag["class"]
            if tag.name == "p" and not tag.text:
                tag.decompose()


        print('ol tags added')

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_judicial_decision_analysis_nav_tag()
        else:
            super(MSParseHtml, self).create_judicial_decision_analysis_nav_tag()
        logger.info("Note to decision nav is created in child class")


