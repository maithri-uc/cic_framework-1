import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns, CustomisedRegexTN
import roman
import html_parse_runner


class TNParseHtml(ParseHtml, RegexPatterns):

    def __init__(self, state_key,path,release_number,input_file_name):
        super().__init__()

        """Meta Data"""
        self.state_key = state_key
        self.path = path
        self.release_number = release_number
        self.input_file_name = input_file_name

        self.tag_type_dict: dict = {'head1': r'TITLE \d', 'ul': r'^\d+-\d+-\d+', 'head2': r'^CHAPTER \d',
                                    'head4': 'NOTES TO DECISIONS', 'head3': r'^\d+-\d+([a-z])?-\d+(\.\d+)?',
                                    'ol_p': r'^\(\d\)', 'junk1': '^Annotations$', 'normalp': r'^Law Reviews\.',
                                    'note_tag': r'^1\.'}

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS']
        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']
        self.watermark_text = """Release {0} of the Official Code of Tennessee Annotated released {1}. 
               Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
               This document is not subject to copyright and is in the public domain.
               """

        self.run()

    def replace_tags_titles(self):
        self.regex_pattern_obj = CustomisedRegexTN()
        self.h2_order: list = ['chapter', 'article', 'subchapter', 'part', '']

        super(TNParseHtml, self).replace_tags_titles()

        for p_tag in self.soup.find_all():
            if p_tag.name == "p":
                if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                    if re.search(r'^\d+\.\s*—\w+', p_tag.text.strip()):
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
                        if re.search(r'^\d+\.', p_tag.text.strip()):
                            p_tag.name = "h5"
                            case_tag = p_tag
                            tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                            p_tag[
                                "id"] = f'{p_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{tag_text}'

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        cap_alpha = 'A'
        small_roman = 'i'
        small_roman_inner_alpha = 'a'
        small_roman_inner_alpha_num = 1
        ol_head = 1
        alpha_ol = self.soup.new_tag("ol", Class="alpha")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_ol = self.soup.new_tag("ol", type="i")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")
        small_letter_inner_ol = self.soup.new_tag("ol", Class="alpha")
        roman_inner_alpha_num_ol = self.soup.new_tag("ol")
        previous_alpha_li = None
        previous_num_li = None
        previous_inner_li = None
        previous_roman_li = None
        previous_roman_inner_alpha_li = None
        previous_roman_inner_alpha_num_li = None
        alpha_li_id = None
        ol_count = 0
        sub_ol_id = None
        sec_sub_ol = None
        sec_sub_li = None
        sub_alpha_ol = None
        prev_chap_id = None
        for p_tag in self.soup.find_all(lambda tag: tag.name == 'p' and re.search(r'\w+', tag.get_text())):

            if not re.search(r'\w+', p_tag.get_text()):
                continue
            if chap_id := p_tag.findPrevious(lambda tag: tag.name in ['h2', 'h3', 'h4']):
                sec_id = chap_id["id"]
                if sec_id != prev_chap_id:
                    ol_count = 0
                prev_chap_id = sec_id
                set_string = True
                data_str = p_tag.get_text().strip()
                p_tag.string = data_str
                if re.search('Except as otherwise provided in this subdivision', data_str, re.I):
                    print()

                if re.search(rf'^\({main_sec_alpha}\)', data_str) and not (
                        previous_roman_li and previous_roman_inner_alpha_li):
                    cap_alpha = 'A'
                    small_roman_inner_alpha = 'a'
                    small_roman_inner_alpha_num = 1
                    sec_sub_ol = None
                    previous_roman_li = None
                    previous_roman_inner_alpha_li = None
                    previous_roman_inner_alpha_num_li = None
                    p_tag.name = 'li'
                    previous_alpha_li = p_tag
                    if main_sec_alpha == 'a':
                        ol_count += 1
                        p_tag.wrap(alpha_ol)
                    else:
                        alpha_ol.append(p_tag)
                    num_ol = self.soup.new_tag("ol")
                    previous_num_li = None
                    previous_inner_li = None
                    ol_head = 1
                    small_roman = 'i'
                    alpha_li_id = f'{sec_id}ol{ol_count}{main_sec_alpha}'
                    p_tag['id'] = alpha_li_id
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                    if re.search(r'^\(\w\)\s*\(\d\)', data_str):
                        small_roman = 'i'
                        small_roman_inner_alpha = 'a'
                        small_roman_inner_alpha_num = 1
                        previous_roman_li = None
                        previous_roman_inner_alpha_li = None
                        li_num = re.search(r'^\(\w\)\s*\((?P<num>\d)\)', data_str).group('num')
                        p_tag.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
                        new_li = self.soup.new_tag('p')
                        new_li.string = re.sub(r'^\(\w\)\s*\(\d\)', '', data_str)
                        p_tag.string.replace_with(new_li)
                        new_li.wrap(num_ol)
                        new_li.name = 'li'
                        previous_num_li = new_li
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        set_string = False
                        ol_head += 1
                        num_li_id = f'{alpha_li_id}{li_num}'
                        new_li['id'] = num_li_id
                        if re.search(r'^\(\w\)\s*\(\d\)\s*\(\w\)', data_str):
                            small_roman = 'i'
                            small_roman_inner_alpha = 'a'
                            small_roman_inner_alpha_num = 1
                            previous_roman_li = None
                            previous_roman_inner_alpha_li = None
                            li_alpha = re.search(r'^\(\w\)\s*\(\d\)\s*\((?P<alpha>\w)\)', data_str).group('alpha')
                            new_li = self.soup.new_tag('p')
                            new_li.string = re.sub(r'^\(\w+\)\s*\(\d\)\s*\(\w\)', '', data_str)
                            previous_num_li.string.replace_with(new_li)
                            new_li.wrap(cap_alpha_ol)
                            new_li.name = 'li'
                            previous_inner_li = new_li
                            inner_ol = self.soup.new_tag("ol", type="i")
                            cap_alpha_li_id = f'{num_li_id}{li_alpha}'
                            new_li['id'] = cap_alpha_li_id
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            else:
                                cap_alpha = chr(ord(cap_alpha) + 1)
                            if re.search(r'^\(\w\)\s*\(\d\)\s*\(\w\)\s*\(\w+\)', data_str):
                                previous_roman_inner_alpha_li = None
                                previous_roman_inner_alpha_num_li = None
                                small_roman_inner_alpha = 'a'
                                li_roman = re.search(r'^\(\w\)\s*\(\d+\)\s*\([A-Z]+\)\s*\((?P<roman>\w+)\)',
                                                     data_str).group(
                                    'roman')
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\(\w\)\s*\(\d+\)\s*\([A-Z]+\)\s*\(\w+\)', '', data_str)
                                previous_inner_li.string.replace_with(new_li)
                                new_li.wrap(inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                new_li['id'] = small_roman_id
                                previous_roman_li = new_li
                                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1)
                elif re.search(r'^\(\w+(\.\d)?\)', p_tag.text.strip()):
                    if re.search(r'^\(\d+\.\d\)', p_tag.text.strip()):
                        if previous_num_li:
                            previous_num_li.append(p_tag)
                        continue

                    if re.search(rf'^\({ol_head}\)', p_tag.text.strip()) and not (
                            previous_roman_inner_alpha_li and previous_roman_inner_alpha_num_li):
                        cap_alpha = "A"
                        small_roman = 'i'
                        small_roman_inner_alpha = 'a'
                        small_roman_inner_alpha_num = 1
                        incr_ol_count = False
                        previous_roman_li = None
                        previous_roman_inner_alpha_li = None
                        previous_roman_inner_alpha_num_li = None
                        if previous_alpha_li:
                            previous_alpha_li.append(p_tag)
                        previous_num_li = p_tag
                        p_tag.name = "li"
                        if ol_head == 1:
                            incr_ol_count = True
                            p_tag.wrap(num_ol)
                        else:
                            num_ol.append(p_tag)
                        cap_alpha_ol = self.soup.new_tag("ol", type="A")
                        previous_inner_li = None
                        if alpha_li_id:
                            num_li_id = f'{alpha_li_id}{ol_head}'
                        else:
                            if incr_ol_count:
                                ol_count += 1
                            num_li_id = f'{sec_id}ol{ol_count}{ol_head}'
                        p_tag['id'] = num_li_id
                        ol_head += 1
                        if re.search(r'^\(\d+\)\s*\(\w+\)', p_tag.text.strip()):
                            small_roman = 'i'
                            small_roman_inner_alpha = 'a'
                            small_roman_inner_alpha_num = 1
                            previous_roman_li = None
                            previous_roman_inner_alpha_li = None
                            previous_roman_inner_alpha_num_li = None
                            li_alpha = re.search(r'^\(\d+\)\s*\((?P<alpha>\w+)\)', p_tag.text.strip()).group('alpha')
                            new_li = self.soup.new_tag('p')
                            new_li.string = re.sub(r'^\(\d+\)\s*\(\w+\)', '', p_tag.text.strip())
                            p_tag.string.replace_with(new_li)
                            new_li.wrap(cap_alpha_ol)
                            new_li.name = 'li'
                            previous_inner_li = new_li
                            set_string = False
                            inner_ol = self.soup.new_tag("ol", type="i")
                            cap_alpha_li_id = f'{num_li_id}{li_alpha}'
                            new_li['id'] = f'{num_li_id}{li_alpha}'
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            else:
                                cap_alpha = chr(ord(cap_alpha) + 1)
                            if re.search(r'^\(\d+\)\s*\([A-Z]+\)\s*\(\w+\)', data_str):
                                previous_roman_inner_alpha_li = None
                                previous_roman_inner_alpha_num_li = None
                                small_roman_inner_alpha = 'a'
                                li_roman = re.search(r'^\(\d+\)\s*\([A-Z]+\)\s*\((?P<roman>\w+)\)', data_str).group(
                                    'roman')
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\(\d+\)\s*\([A-Z]+\)\s*\(\w+\)', '', data_str)
                                p_tag.string.replace_with(new_li)
                                new_li.wrap(inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                new_li['id'] = small_roman_id
                                previous_roman_li = new_li
                                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1)
                    elif re.search(r'^\(\d+\)', p_tag.text.strip()) and sec_sub_ol:
                        previous_roman_inner_alpha_num_li = None
                        previous_roman_inner_alpha_li = None
                        digit = re.search(r'^\((?P<sec_digit>\d+)\)', data_str).group('sec_digit')
                        sec_sub_li = self.soup.new_tag('li')
                        sec_sub_li.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
                        sec_sub_li['id'] = f"{sub_ol_id}{digit}"
                        sec_sub_ol.append(sec_sub_li)
                        sub_alpha_ol = self.soup.new_tag('ol', type='A')
                        sec_sub_li.append(sub_alpha_ol)
                        p_tag.decompose()
                        continue
                    elif previous_num_li:
                        if cap_alpha_match := re.search(fr'^\({cap_alpha}+\)|(^\([A-Z]+(\.\d+)?\))',
                                                        p_tag.text.strip()):
                            small_roman = 'i'
                            small_roman_inner_alpha = 'a'
                            small_roman_inner_alpha_num = 1
                            li_alpha = re.search(r'^\((?P<alpha>\w+(\.\d+)?)\)', data_str).group('alpha')
                            previous_num_li.append(p_tag)
                            p_tag.name = 'li'
                            previous_roman_li = None
                            previous_roman_inner_alpha_li = None
                            previous_roman_inner_alpha_num_li = None
                            if sec_sub_ol:
                                p_tag['id'] = f'{sec_sub_li["id"]}{li_alpha}'
                                if re.search(r'\d+', cap_alpha_match.group(0)):
                                    p_tag.name = 'p'
                                    previous_inner_li.apend(p_tag)
                                else:
                                    sub_alpha_ol.append(p_tag)
                            else:
                                if re.search(r'\d+', cap_alpha_match.group(0)):
                                    p_tag.name = 'p'
                                    previous_inner_li.insert(len(previous_inner_li.contents), p_tag)
                                else:
                                    p_tag.wrap(cap_alpha_ol)
                                    previous_inner_li = p_tag
                                inner_ol = self.soup.new_tag("ol", type="i")
                                cap_alpha_li_id = f'{num_li_id}{li_alpha}'
                                p_tag['id'] = cap_alpha_li_id
                            if re.search(r'^\([A-Z]+\)\s*\(\w+\)', p_tag.text.strip()):
                                small_roman_inner_alpha = 'a'
                                small_roman_inner_alpha_num = 1
                                previous_roman_inner_alpha_li = None
                                previous_roman_inner_alpha_num_li = None
                                li_roman = re.search(r'^\([A-Z]+\)\s*\((?P<roman>\w+)\)', data_str).group('roman')
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\([A-Z]+\)\s*\(\w+\)', '', p_tag.text.strip())
                                p_tag.string.replace_with(new_li)
                                new_li.wrap(inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_id = f'{cap_alpha_li_id}{li_roman}'
                                new_li['id'] = small_roman_id
                                previous_roman_li = new_li
                                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1)
                            if cap_alpha == 'Z':
                                cap_alpha = 'A'
                            elif not re.search(r'\d+', cap_alpha_match.group(0)):
                                cap_alpha = chr(ord(cap_alpha) + 1)

                            if re.search(r'^\([A-Z]+\)\s*\(\w+\)\s*\(a\)', data_str):
                                new_li = self.soup.new_tag('p')
                                new_li.string = re.sub(r'^\([A-Z]+\)\s*\(\w+\)\s*\(a\)', '', data_str)
                                p_tag.string.replace_with(new_li)
                                new_li.wrap(small_letter_inner_ol)
                                new_li.name = 'li'
                                set_string = False
                                small_roman_inner_alpha_id = f'{cap_alpha_li_id}a'
                                new_li['id'] = small_roman_inner_alpha_id
                                small_roman_inner_alpha = "b"


                        elif previous_inner_li:
                            if alpha_match := re.search(r'^\((?P<alpha>[a-z]+)\)', p_tag.text.strip()):
                                li_roman = alpha_match.group('alpha')
                                if li_roman.upper() == roman.toRoman(roman.fromRoman(small_roman.upper())):
                                    small_roman_inner_alpha = 'a'
                                    small_roman_inner_alpha_num = 1
                                    previous_roman_inner_alpha_li = None
                                    previous_roman_inner_alpha_num_li = None
                                    small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1)
                                    previous_inner_li.append(p_tag)
                                    p_tag.name = 'li'
                                    p_tag.wrap(inner_ol)
                                    roman_ol = self.soup.new_tag("ol", type="I")
                                    small_roman_id = f'{cap_alpha_li_id}{li_roman}'  # title 40
                                    p_tag['id'] = small_roman_id
                                    previous_roman_li = p_tag
                                    small_letter_inner_ol = self.soup.new_tag("ol", type="a")
                                    if re.search(f'^\([a-z]+\)\s*\({small_roman_inner_alpha}\)',
                                                 p_tag.get_text().strip()):
                                        small_roman_inner_alpha_num = 1
                                        previous_roman_inner_alpha_num_li = None
                                        new_li = self.soup.new_tag('p')
                                        new_li.string = re.sub(r'^\([A-Z]\)\s*\(\w+\)', '', p_tag.text.strip())
                                        new_li.name = 'li'
                                        new_li['id'] = f'{small_roman_id}{small_roman_inner_alpha}'
                                        p_tag.string.replace_with(new_li)
                                        new_li.wrap(small_letter_inner_ol)
                                        small_roman_inner_alpha = chr(ord(small_roman_inner_alpha) + 1)
                                        previous_roman_inner_alpha_li = new_li
                                        roman_inner_alpha_num_ol = self.soup.new_tag("ol")
                                elif re.search(f'^\({small_roman_inner_alpha}\)', p_tag.get_text().strip()):

                                    small_roman_inner_alpha_num = 1
                                    previous_roman_li.append(p_tag)
                                    p_tag.wrap(small_letter_inner_ol)
                                    p_tag.name = 'li'
                                    roman_inner_alpha_num_ol = self.soup.new_tag("ol")
                                    small_roman_inner_alpha_id = f'{small_roman_id}{small_roman_inner_alpha}'
                                    p_tag['id'] = small_roman_inner_alpha_id
                                    previous_roman_inner_alpha_li = p_tag
                                    small_roman_inner_alpha = chr(ord(small_roman_inner_alpha) + 1)
                            elif re.search(f'^\({small_roman_inner_alpha_num}\)', p_tag.get_text().strip()):
                                if previous_roman_inner_alpha_li:
                                    previous_roman_inner_alpha_li.append(p_tag)
                                    p_tag.wrap(roman_inner_alpha_num_ol)
                                    p_tag.name = 'li'
                                    small_roman_inner_alpha_num_id = f'{small_roman_inner_alpha_id}{small_roman_inner_alpha_num}'
                                    p_tag['id'] = small_roman_inner_alpha_num_id
                                    small_roman_inner_alpha_num += 1
                                    previous_roman_inner_alpha_num_li = p_tag
                                else:
                                    previous_inner_li.append(p_tag)

                            elif previous_roman_li:
                                if re.search(r'^\([a-z]+\)', p_tag.text.strip()):
                                    li_roman = re.search(r'^\((?P<roman>\w+)\)', data_str).group('roman')
                                    previous_roman_li.append(p_tag)
                                    p_tag.wrap(roman_ol)
                                    p_tag.name = 'li'
                                    p_tag['id'] = f'{small_roman_id}{li_roman}'
                            else:
                                previous_inner_li.insert(len(previous_num_li.contents), p_tag)

                elif re.search(r'^Acts\s|^Code\s|^T\.C\.A|^Article\s', p_tag.get_text().strip(), re.I) or (
                        p_tag.find_previous_sibling()
                        and re.search(r'^\d+-\d+-\d+', p_tag.find_previous_sibling().get_text())):
                    set_string = False
                    ol_head = 1
                    main_sec_alpha = 'a'
                    cap_alpha = "A"
                    small_roman = 'i'
                    small_roman_inner_alpha = 'a'
                    small_roman_inner_alpha_num = 1
                    previous_roman_inner_alpha_li = None
                    previous_roman_inner_alpha_num_li = None
                    previous_alpha_li = None
                    previous_num_li = None
                    previous_inner_li = None
                    alpha_li_id = None
                    previous_roman_li = None
                    sec_sub_ol = None
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    num_ol = self.soup.new_tag("ol")
                    inner_ol = self.soup.new_tag("ol", type="i")
                    roman_ol = self.soup.new_tag("ol", type="I")
                    small_letter_inner_ol = self.soup.new_tag("ol", Class="alpha")
                    roman_inner_alpha_num_ol = self.soup.new_tag("ol")

                else:
                    if previous_inner_li:
                        previous_inner_li.append(p_tag)
                    elif previous_num_li:
                        previous_num_li.append(p_tag)
                    elif previous_alpha_li:
                        previous_alpha_li.append(p_tag)
                if set_string:
                    p_tag.string = re.sub(r'^\(\w+\)', '', p_tag.text.strip())
        print('ol tags added')

    def create_analysis_nav_tag(self):
        super(TNParseHtml, self).create_Notes_to_decision_analysis_nav_tag()
        print("note to decision nav created")

    def add_cite(self):

        file_name = 'gov.tn.tca.title.'
        cite_p_tags = []
        for tag in self.soup.findAll(lambda tag: re.search(r"(§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                                           r"|\d+ Ga.( App.)? \d+"
                                                           r"|\d+ S.E.(2d)? \d+"
                                                           r"|\d+ U.S.C. § \d+(\(\w\))?"
                                                           r"|\d+ S\. (Ct\.) \d+"
                                                           r"|\d+ L\. (Ed\.) \d+"
                                                           r"|\d+ L\.R\.(A\.)? \d+"
                                                           r"|\d+ Am\. St\.( R\.)? \d+"
                                                           r"|\d+ A\.L\.(R\.)? \d+)",
                                                           tag.get_text()) and tag.name == 'p'
                                                 and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            super(TNParseHtml, self).add_cite(tag, file_name)
        print("cite is added")

    def run(self):
        self.run_titles()
