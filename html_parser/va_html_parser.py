import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns
import roman


class VAParseHtml(ParseHtml, RegexPatterns):

    def __init__(self):
        super().__init__()

        self.tag_type_dict: dict = {'ul': r'^(Chapter|PART) \d+\.|^Chap.|^\d.|^§',
                                    'head1': r'^Title|^The Constitution of the United States of America',
                                    'head2': r'^Chapter \d+\.|^PART 1\.',
                                    'head3': r'^§\s\d+(\.\d+)*[A-Z]*\-\d+\.\s*|^§', 'junk1': '^Text|^Statute text',
                                    'article': '——————————',
                                    'head4': '^CASE NOTES', 'ol': r'^A\.\s',
                                    'head': r'^§§\s*\d+-\d+\s*through\s*\d+-\d+\.|'
                                            r'^§§+\s(?P<sec_id>\d+.\d+(-\d+)*)\.*\s*|^Part \d+\.'}

        self.h4_head: list = ['History.', 'Compiler’s Notes.', 'NOTES TO DECISIONS']

        self.watermark_text = """Release {0} of the Official Code of Virginia Annotated released {1}.
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """

    def replace_tags_titles(self):
        self.h2_order: list = ['subtitle', 'part', 'chapter', 'article','']

        super(VAParseHtml, self).replace_tags_titles()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_rom_id = None
        h5_alpha_id = None

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
        super(VAParseHtml, self).add_anchor_tags()
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
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        cap_alpha_cur_tag = None
        main_sec_alpha1 = 'a'
        sec_alpha_cur_tag = None
        num_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha1 = 'A'
        n_tag = None

        for p_tag in self.soup.body.find_all():
            current_tag_text = p_tag.text.strip()
            if p_tag.i:
                p_tag.i.unwrap()

            if re.search(rf'^{cap_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                ol_head = 1
                cap_alpha_cur_tag = p_tag

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    cap_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^{cap_alpha}\.', '', current_tag_text)
                if cap_alpha == "Z":
                    cap_alpha = "A"
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

                if re.search(rf'^[A-Z]+\.\s*\d+\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[A-Z]+\.\s*\d+\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    num_cur_tag = li_tag
                    cur_tag = re.search(r'^(?P<cid>[A-Z])+\.\s*(?P<pid>\d+)\.', current_tag_text)
                    num_id = f'{cap_alpha_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{cap_alpha_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    ol_head = 2

                    if re.search(r'[A-Z]+\.\s*\d+\.\s*[a-z]+\.', current_tag_text):
                        sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'[A-Z]+\.\s*\d+\.\s*[a-z]+\.', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)

                        cur_tag = re.search(r'(?P<cid>[A-Z])+\.\s*(?P<pid>\d+)\.\s*(?P<nid>[a-z]+)\.', current_tag_text)
                        sec_alpha_id1 = f'{num_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        sec_alpha_ol1.append(inner_li_tag)
                        num_cur_tag.string = ""
                        num_cur_tag.append(sec_alpha_ol1)
                        main_sec_alpha1 = 'b'

            elif re.search(rf'^{ol_head}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha1 = 'a'
                main_sec_alpha = "a"

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_id = f"{p_tag.find_previous({'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"
                    if cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(num_ol)
                        num_id = cap_alpha_cur_tag.get('id')
                    elif n_tag:
                        n_tag.append(num_ol)
                        num_id = n_tag.get('id')
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(num_ol)
                        num_id = sec_alpha_cur_tag.get('id')

                else:
                    num_ol.append(p_tag)
                p_tag["id"] = f'{num_id}{ol_head}'
                p_tag.string = re.sub(rf'^{ol_head}\.', '', current_tag_text)
                ol_head += 1

                if re.search(r'^\d+\.\s*[a-z]+\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'\d+\.\s*[a-z]+\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'(?P<pid>\d+)\.\s*(?P<nid>[a-z]+)\.', current_tag_text)
                    sec_alpha_id1 = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}{cur_tag.group("nid")}'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol1)
                    main_sec_alpha1 = 'b'

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        sec_alpha_id = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol)
                    elif num_cur_tag1:
                        sec_alpha_id = num_cur_tag1.get('id')
                        num_cur_tag1.append(sec_alpha_ol)
                    else:
                        sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

            elif re.search(rf'^{main_sec_alpha1}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol1)

                    if num_cur_tag:
                        sec_alpha_id1 = num_cur_tag.get('id')
                        num_cur_tag.append(sec_alpha_ol1)
                    else:
                        sec_alpha_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                else:
                    sec_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id1}{main_sec_alpha1}'
                p_tag.string = re.sub(rf'^{main_sec_alpha1}\.', '', current_tag_text)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

                if re.search(r'^[a-z]+\.\s1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'[a-z]+\.\s1\.', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'(?P<pid>[a-z]+)\.\s*1\.', current_tag_text)
                    num_cur_tag = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    sec_alpha_ol1.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(sec_alpha_ol1)
                    ol_head = 2

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                # main_sec_alpha = 'a'
                cap_alpha1 = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                        main_sec_alpha = 'a'

                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1


            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)

                    if num_cur_tag1:
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha_id1 = num_cur_tag1.get("id")
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                cap_alpha1 = chr(ord(cap_alpha1) + 1)

                if re.search(r'^\([A-Z]\)\s\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s\(i\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cur_tag = re.search(r'\((?P<pid>[A-Z])\)\s*\((?P<nid>i)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("nid")}'
                    roman_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(roman_ol)

            elif re.search(rf'^\(\d[a-z]\)', current_tag_text) and p_tag.name == "p":
                n_tag = p_tag
                n_id = re.search(rf'^\((?P<n_id>\d+[a-z])\)', current_tag_text).group("n_id")
                p_tag["id"] = f'{num_id1}-{n_id}'
                num_cur_tag1.append(p_tag)

            elif re.search(r'^\([ivx]+\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                roman_cur_tag = p_tag
                # ol_head = 1

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    if sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(roman_ol)
                        prev_id1 = sec_alpha_cur_tag.get("id")
                    elif cap_alpha_cur_tag1:
                        cap_alpha_cur_tag1.append(roman_ol)
                        prev_id1 = cap_alpha_cur_tag1.get('id')
                    elif cap_alpha_cur_tag:
                        cap_alpha_cur_tag.append(roman_ol)
                        prev_id1 = cap_alpha_cur_tag.get("id")

                    elif num_cur_tag1:
                        num_cur_tag1.append(roman_ol)
                        prev_id1 = num_cur_tag1.get("id")
                    else:
                        prev_id1 = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    print(p_tag)
                    roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[ivx]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([ivx]+\)', '', current_tag_text)

            if re.search(r'^CASE NOTES|^(ARTICLE|Article) [IVX]+\.', current_tag_text) or p_tag.name in ['h3', 'h4',
                                                                                                         'h5']:
                ol_head = 1
                cap_alpha = 'A'
                cap_alpha_cur_tag = None
                num_count = 1
                num_cur_tag = None
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                n_tag = None
                if re.search(r'^(ARTICLE|Article) [IVX]+\.', current_tag_text):
                    ol_count += 1

        print('ol tags added')

    def create_analysis_nav_tag(self):
        super(VAParseHtml, self).create_case_note_analysis_nav_tag()
        print("case note analysis nav created")

    def add_cite(self):
        file_name = 'gov.va.code.title.'
        cite_p_tags = []
        for tag in self.soup.findAll(
                lambda tag: re.search(
                    r"\d+(\.\d+)*-\d+(\.\d+)*\.*\s*(:\d+)*|\d+\sVa.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*)",
                    tag.get_text()) and tag.name == 'p'
                            and tag not in cite_p_tags):
            cite_p_tags.append(tag)
            super(VAParseHtml, self).add_cite(tag,file_name)


ParseHtml_obj = VAParseHtml()
ParseHtml_obj.run_constitution()
ParseHtml_obj.run_titles()
