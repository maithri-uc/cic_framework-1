import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns
import roman


class NCParseHtml(ParseHtml, RegexPatterns):

    def __init__(self):
        super().__init__()

        self.h2_subchapter_pattern = None
        self.h2_order = None
        self.tag_type_dict: dict = {'head1': r'Chapter \d+',
                                    'ul': r'^Article|^1\.|^(?P<sec_id>\d+([A-Z])*-\d+(\.\d+)*)|^§|^Article 1.',
                                    'head2': r'^ARTICLE \d+\.|^Article 1.|^ARTICLE I\.',
                                    'head4': '^CASE NOTES|^OFFICIAL COMMENT',
                                    'head3': '^§* \d+([A-Z])*-\d+(-\d+)*(\.|,| through)|^§', 'ol_p': r'^\(\d\)|^I\.',
                                    'junk1': '^Annotations$', 'nav': '^Subchapter I\.|^——————————'}

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS']

        self.watermark_text = """Release {0} of the Official Code of Kentucky Annotated released {1}
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """

    def generate_class_name_dict(self):
        super(NCParseHtml, self).generate_class_name_dict()

    def replace_tags_titles(self):
        self.h1_pattern = re.compile(r'Chapter (?P<id>\d+)\.', re.I)
        self.h2_chapter_pattern = re.compile(r'^subchapter\s(?P<id>[IVX]+([a-zA-Z])*)', re.I)
        self.section_pattern = re.compile(
            r'^§+\s*(?P<id>\d+([A-Z])*-\d+([A-Z])*(\.\d+[A-Z]*)*(-\d+)*|\d+([A-Z])*)[:., through]')
        self.h2_subchapter_pattern = re.compile(r'^Subchapter\s(?P<id>[IVX]+[A-Z]?)\.', re.I)

        self.h2_order: list = ["chapter", 'subchapter', 'article', 'part']

        super(NCParseHtml, self).replace_tags_titles()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^CASE NOTES$|^Analysis$', header_tag.text.strip()):
                    cap_roman = "I"
                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f"{header_tag.find_previous({'h4', 'h3'}).get('id')}-notetodecisison-{h5_rom_text}"
                    header_tag['id'] = h5_rom_id
                    cap_alpha = 'A'
                    cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)


                elif cap_alpha and re.search(fr'^{cap_alpha}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_alpha_text = re.search(r'^(?P<h5_id>[A-Z]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_alpha_id = f"{h5_rom_id}-{h5_alpha_text}"
                    header_tag['id'] = h5_alpha_id
                    cap_alpha = chr(ord(cap_alpha) + 1)
                    cap_num = 1

                elif cap_num and re.search(fr'^{cap_num}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    h5_num_text = re.search(r'^(?P<h5_id>\d+)\.', header_tag.text.strip()).group("h5_id")

                    h5_num_id = f"{h5_alpha_id}-{h5_num_text}"
                    header_tag['id'] = h5_num_id
                    cap_num += 1


            if re.search(r'^Analysis', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]]:
                        break
                    else:
                        tag["class"] = "casenote"



    def add_anchor_tags(self):
        super(NCParseHtml, self).add_anchor_tags()
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
        cap_alpha = 'A'
        ol_head = 1
        num_count = 1
        roman_count = 1
        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        inner_ol = self.soup.new_tag("ol", type="i")
        cap_roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        ol_list = []
        ol_head1 = 1
        sec_alpha = 'a'
        sec_alpha1 = 'a'
        alpha_cur_tag2 = None

        for p_tag in self.soup.find_all():
            if p_tag.b:
                p_tag.b.unwrap()
            if p_tag.i:
                p_tag.i.unwrap()
            if p_tag.span:
                p_tag.span.unwrap()

            current_tag_text = p_tag.text.strip()

            if p_tag.name == "h3":
                num_cur_tag = None

            if re.search(rf'^\({ol_head}\)', current_tag_text):
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = 'A'
                main_sec_alpha = "a"
                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)

                    if cap_roman_cur_tag:
                        cap_roman_cur_tag.append(num_ol)
                        prev_num_id = f'{cap_roman_cur_tag.get("id")}{ol_head}'
                        p_tag["id"] = f'{cap_roman_cur_tag.get("id")}{ol_head}'

                    else:
                        prev_head_id = p_tag.find_previous({"h4", "h3"}).get("id")
                        prev_num_id = f'{prev_head_id}ol{ol_count}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'

                    if prev_head_id in ol_list:
                        ol_count += 1
                    else:
                        ol_count = 1
                    ol_list.append(prev_head_id)

                else:
                    num_ol.append(p_tag)
                    p_tag["id"] = f'{prev_num_id}{ol_head}'
                    p_tag.string = re.sub(rf'^\({ol_head}\)|^\({ol_head1}\)', '', current_tag_text)

                p_tag.string = re.sub(rf'^\({ol_head}\)|^\({ol_head1}\)', '', current_tag_text)
                ol_head += 1
                ol_head1 += 1

                if re.search(r'^\(\d+\)(\s)*\([a-z]\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)*\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)*\((?P<pid>\w)\)', current_tag_text)
                    prevnum_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"
                    num_count = 1

                    if re.search(r'^\(\d+\)(\s)?\([a-z]\)\s\d+\.', current_tag_text):
                        num_ol1 = self.soup.new_tag("ol")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)(\s)?\([a-z]\)\s\d+\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)\s(?P<nid>\d+)\.', current_tag_text)
                        prev_id = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}'
                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        num_ol1.append(inner_li_tag)
                        alpha_cur_tag.string = ""
                        alpha_cur_tag.append(num_ol1)
                        num_count = 2

            elif re.search(rf'^\(\s*{main_sec_alpha}\s*\)', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                roman_count = 1
                num_count = 1
                ol_head1 = 1

                if re.search(r'^\(a\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol)
                    if num_cur_tag:
                        prevnum_id = num_cur_tag.get("id")
                        num_cur_tag.append(alpha_ol)
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                    else:
                        prevnum_id = f'{p_tag.find_previous({"h4", "h3"}).get("id")}ol{ol_count}'
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                else:
                    alpha_ol.append(p_tag)
                    p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'

                p_tag.string = re.sub(rf'^\(\s*{main_sec_alpha}\s*\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(r'^\(\w\)\s?1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s?1\.', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*(?P<pid>1)\.', current_tag_text)
                    prev_id = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}'
                    inner_li_tag[
                        "id"] = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    num_ol1.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, num_ol1)
                    num_count = 2
                    sec_alpha = 'a'

            elif re.search(r'^\(\s*\d\d\s*\)', current_tag_text):
                p_tag.name = "li"
                p_tag_text = re.search(r'^\(\s*(?P<id>\d\d)\s*\)', current_tag_text).group("id")
                alpha_ol.append(p_tag)
                p_tag["id"] = f'{prevnum_id}{p_tag_text}'
                p_tag.string = re.sub(r'^\(\s*\d\d\s*\)', '', current_tag_text)

            elif re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_tag = p_tag
                sec_alpha = 'a'

                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    if alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)
                    elif cap_alpha_cur_tag:
                        prev_id = cap_alpha_cur_tag.get("id")
                        cap_alpha_cur_tag.append(num_ol1)
                    elif num_cur_tag:
                        prev_id = num_cur_tag.get("id")
                        num_cur_tag.append(num_ol1)
                    else:
                        prev_id = f'{p_tag.find_previous({"h4", "h3"}).get("id")}ol{ol_count}'
                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{prev_id}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1

                if re.search(r'^\d+\.\s?a\.', current_tag_text):
                    innr_alpha_ol = self.soup.new_tag("ol", type="a")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\d+\.\s?a\.', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag1 = inner_li_tag
                    cur_tag = re.search(r'^(?P<cid>\d+)\.\s?(?P<pid>a)\.', current_tag_text)
                    prevnum_id1 = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                    inner_li_tag[
                        "id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    innr_alpha_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, innr_alpha_ol)
                    sec_alpha = 'b'

            elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag1 = p_tag
                roman_count = 1
                ol_head1 = 1
                if re.search(r'^a\.', current_tag_text):
                    innr_alpha_ol = self.soup.new_tag("ol", type="a")
                    previd = p_tag.find_previous("li")
                    p_tag.wrap(innr_alpha_ol)
                    prevnum_id1 = previd.get("id")
                    previd.append(innr_alpha_ol)
                    p_tag["id"] = f'{prevnum_id1}{sec_alpha}'
                else:
                    innr_alpha_ol.append(p_tag)
                    p_tag["id"] = f'{prevnum_id1}{sec_alpha}'

                p_tag.string = re.sub(rf'^{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

                if re.search(r'^\w+\.\s?i\.', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\w+\.\s?i\.', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    roman_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^(?P<cid>\w+)\.\s?(?P<pid>i)\.', current_tag_text)
                    prev_id1 = f'{alpha_cur_tag1.get("id")}'
                    inner_li_tag[
                        "id"] = f'{alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'
                    roman_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, roman_ol)

            elif re.search(rf'^{cap_alpha}\.', current_tag_text):
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                cap_alpha1 = cap_alpha
                num_count = 1
                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    prev_id1 = p_tag.find_previous({"h4", "h3"}).get("id")

                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_id1}ol{ol_count}{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)

                if cap_alpha == 'Z':
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)


            elif re.search(r'^[IVX]+\.', current_tag_text):
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag
                ol_head = 1

                if re.search(r'^I\.', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    prev_id1 = p_tag.find_previous({"h4", "h3"}).get("id")
                else:
                    cap_roman_ol.append(p_tag)

                rom_head = re.search(r'^(?P<rom>[IVX]+)\.', current_tag_text)
                p_tag["id"] = f'{prev_id1}ol{ol_count}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^[IVX]+\.', '', current_tag_text)

            elif re.search(r'^[ivx]+\.', current_tag_text):
                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^i\.', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    alpha_cur_tag1.append(roman_ol)
                    prev_id1 = alpha_cur_tag1.get("id")

                else:

                    roman_ol.append(p_tag)

                rom_head = re.search(r'^(?P<rom>[ivx]+)\.', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^[ivx]+\.', '', current_tag_text)

            if re.search(r'^History|^Cross references:|^OFFICIAL COMMENT', current_tag_text) or p_tag.name in ['h3']:
                ol_head = 1
                ol_head1 = 1
                num_count = 1
                num_cur_tag = None
                new_alpha = None
                main_sec_alpha = 'a'
                sec_alpha = 'a'
                alpha_cur_tag = None
                cap_alpha = "A"
                num_count1 = 1
                cap_alpha_cur_tag = None
                cap_roman_cur_tag = None
                alpha_cur_tag1 = None
                sec_alpha1 = 'a'
        print("ol tag created")

    def create_analysis_nav_tag(self):
        super(NCParseHtml, self).create_case_note_analysis_nav_tag()
        print("Case Notes nav created")

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
            super(NCParseHtml, self).add_cite(tag)


ParseHtml_obj = NCParseHtml()
ParseHtml_obj.run_constitution()
ParseHtml_obj.run_titles()
