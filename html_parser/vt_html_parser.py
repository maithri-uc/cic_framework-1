import importlib
import re
from base_html_parser import ParseHtml
import roman
from regex_pattern import CustomisedRegexVT


class VTParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)
        self.h2_pattern_text = None

    def pre_process(self):

        if re.search('constitution', self.input_file_name):

            self.tag_type_dict: dict = {'ul': r'^Chapter I|^PREAMBLE',
                                        'head1': '^Constitution of the United States|'
                                                 'CONSTITUTION OF THE STATE OF VERMONT',
                                        'head2': '^CHAPTER I|^PREAMBLE', 'head3': r'^§ 1\.|^Section \d+\.',
                                        'junk1': '^Annotations',
                                        'article': '——————————', 'head4': '^ANNOTATIONS', 'ol': r'^\(A\)', }
            if re.search(r'us\.html$', self.input_file_name):
                self.h2_order: list = ['chapter', '', '', '', '']
            else:
                self.h2_order: list = ['article', 'amendment', '', '', '']

            self.h2_pattern_text: list = ['PREAMBLE', 'DELEGATION AND DISTRIBUTION OF POWERS',
                                          'LEGISLATIVE DEPARTMENT', 'EXECUTIVE DEPARTMENT',
                                          'JUDICIARY DEPARTMENT', 'QUALIFICATIONS OF FREEMEN AND FREEWOMEN',
                                          'ELECTIONS; OFFICERS; TERMS OF OFFICE', 'OATH OF ALLEGIANCE; OATH OF OFFICE',
                                          'IMPEACHMENT', 'MILITIA', 'GENERAL PROVISIONS',
                                          'AMENDMENT OF THE CONSTITUTION',
                                          'TEMPORARY PROVISIONS']

        else:
            if int(self.release_number) >= int('84'):
                self.tag_type_dict: dict = {'ul': r'^(Chapter|Article)\s*\d+\.', 'head2': r'^(CHAPTER|Article) \d+\.',
                                            'head1': r'^TITLE|^The Constitution of the United States of America',
                                            'head3': r'^§ \d+((-|—)\d+)*\.', 'junk1': '^Annotations',
                                            'article': '——————————',
                                            'ol': r'^\(A\)', 'head4': '^History'}
            else:
                self.tag_type_dict: dict = {'ul': r'^\d+\.', 'head2': r'^CHAPTER \d+\.',
                                            'head1': r'^TITLE|^The Constitution of the United States of America',
                                            'head3': r'^§ \d+(-\d+)*\.', 'junk1': '^Annotations',
                                            'article': '——————————',
                                            'ol': r'^\(A\)', 'head4': '^History', 'analysishead': r'^\d+\.',
                                            'part': r'^PART \d'}

            file_no = re.search(r'gov\.vt\.vsa\.title\.(?P<fno>\w+)\.html', self.input_file_name).group("fno")

            if file_no in ['18', '05', '03', '10', '09', '08', '06', '13', '14', '16', '20', '16A',
                           '24', '24A', '33', '30', '29']:
                self.h2_order: list = ["part", "chapter", 'subchapter', '', '']

            elif file_no in ['09A', '11C']:
                self.h2_order: list = ["article", "part", '', '', '']

            elif file_no in ['32']:
                self.h2_order: list = ["subtitle", 'chapter', 'subchapter ','', '', '']

            elif file_no in ['27A']:
                self.h2_order: list = ["part", "article", '', '', '']

            else:
                self.h2_order: list = ["chapter", 'subchapter', 'article', 'part', '']

            self.h2_text: list = ['Regulations Chapter 1. Game', 'Title Five Tables',
                                  'Table 2 Derivation of Sections',
                                  'Aeronautics and Surface Transportation Generally',
                                  'Table 2 Derivation of Sections']

        self.h2_pattern_text = [r'^(?P<tag>Part)\s*(?P<id>\d+)']

        self.h4_head: list = ['History', 'Compiler’s Notes.', 'CROSS REFERENCES', 'ANNOTATIONS', 'Notes to Opinions']

        self.watermark_text = """Release {0} of the Official Code of Vermont Annotated released {1}.
                Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                This document is not subject to copyright and is in the public domain.
                """

        self.regex_pattern_obj = CustomisedRegexVT()

    def replace_tags_titles(self):

        super(VTParseHtml, self).replace_tags_titles()

        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_alpha_id = None
        h5_rom_id = None
        cap_roman_tag = None
        annotation_text_list: list = []
        annotation_id_list: list = []
        h5_count = 1

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^CASE NOTES$|^Analysis$|^ANNOTATIONS$', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_roman_tag = None
                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()):
                    header_tag.name = "h5"
                    cap_roman_tag = header_tag
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecisison-{h5_rom_text}'
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
                else:
                    annotation_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    if annotation_text in annotation_text_list and re.search(r'^ANNOTATIONS$', header_tag.find_previous(
                            "h4").text.strip()):
                        header_tag.name = "h5"
                        if cap_roman_tag:
                            annotation_id = f'{cap_roman_tag.get("id")}-{annotation_text}'
                        else:
                            annotation_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{annotation_text}'

                        if annotation_id in annotation_id_list:
                            header_tag["id"] = f'{annotation_id}.{h5_count}'
                            h5_count += 1
                        else:
                            header_tag["id"] = f'{annotation_id}'
                            h5_count = 1

                        annotation_id_list.append(annotation_id)

            if re.search(r'^Analysis|^ANNOTATIONS', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]]:
                        break
                    else:
                        tag["class"] = "casenote"
                        annotation_text_list.append(re.sub(r'[\W\s]+', '', tag.text.strip()).lower())

    def add_anchor_tags(self):
        super(VTParseHtml, self).add_anchor_tags()
        for li_tag in self.soup.find_all("li"):
            if not li_tag.get("id") and re.search(r'^Part \d+\.', li_tag.text.strip()):
                chap_num = re.search(r'^Part (?P<id>\d+)\.', li_tag.text.strip()).group("id")
                self.c_nav_count += 1
                self.set_chapter_section_id(li_tag, chap_num,
                                            sub_tag="p",
                                            prev_id=li_tag.find_previous("h1").get("id"),
                                            cnav=f'cnav{self.c_nav_count:02}')

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        main_sec_alpha = 'a'
        num_count = 1
        num_ol = self.soup.new_tag("ol")
        roman_ol = self.soup.new_tag("ol", type="i")
        sec_alpha_ol = self.soup.new_tag("ol", type="a")
        num_ol1 = self.soup.new_tag("ol")
        ol_count = 1
        sec_alpha_cur_tag = None
        num_cur_tag1 = None
        cap_alpha_cur_tag1 = None
        cap_alpha1 = 'A'
        sec_alpha_id = None
        cap_alpha2 = 'A'
        small_roman = "i"
        num_tag = None
        previous_li_tag = None
        cap_roman_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):

            current_tag_text = p_tag.text.strip()

            if p_tag.i:
                p_tag.i.unwrap()

            if re.search(rf'^\({small_roman}\)', current_tag_text) and cap_alpha_cur_tag1:
                p_tag.name = "li"
                roman_cur_tag = p_tag

                if re.search(r'^\(i\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    p_tag.wrap(roman_ol)
                    prev_class = p_tag.find_previous({'h4', 'h3'}).get("class")

                    if prev_class == ['subsection']:
                        if sec_alpha_cur_tag:
                            sec_alpha_cur_tag.append(roman_ol)
                            prev_id1 = sec_alpha_cur_tag.get('id')
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                            main_sec_alpha = 'j'
                        elif num_tag:
                            num_tag.append(roman_ol)
                            prev_id1 = num_tag.get('id')
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                        else:
                            prev_id1 = f"{p_tag.find_previous('h4', class_='subsection').get('id')}ol{ol_count}"

                            prev_id1 = f'{prev_id1}'
                            p_tag["id"] = f'{prev_id1}i'
                            p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                    else:

                        prev_li = p_tag.find_previous("li")
                        prev_li.append(roman_ol)
                        prev_id1 = prev_li.get("id")
                        p_tag["id"] = f'{prev_li.get("id")}i'
                        p_tag.string = re.sub(r'^\(i\)', '', current_tag_text)
                else:
                    roman_ol.append(p_tag)
                    rom_head = re.search(r'^\((?P<rom>[ivx]+)\)', current_tag_text).group("rom")
                    p_tag["id"] = f'{prev_id1}{rom_head}'
                    p_tag.string = re.sub(r'^\([ivx]+\)', '', current_tag_text)

                small_roman = roman.toRoman(roman.fromRoman(small_roman.upper()) + 1).lower()

                if re.search(rf'^\([ivx]+\)\s*\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([ivx]+\)\s*\(I\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_roman_cur_tag = li_tag
                    cur_tag1 = re.search(r'^\((?P<cid>[ivx]+)\)\s*\((?P<pid>I)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag1.group("cid")}{cur_tag1.group("pid")}'
                    cap_roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_roman_ol)
                previous_li_tag = p_tag

            elif re.search(r'^\d{0,2}\.\d+(\.\d+)*', current_tag_text) and p_tag.name == 'p':
                p_tag.name = "li"
                num_tag = p_tag
                main_sec_alpha = 'a'

                if re.search(r'^\d\.1\s', current_tag_text):

                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                else:
                    num_ol.append(p_tag)
                # prev_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2', 'h1'}).get('id')}ol{ol_count}"

                num_id = re.search(r'^(?P<n_id>\d{0,2}\.\d+(\.\d+)*)', current_tag_text).group("n_id")
                # p_tag["id"] = f'{prev_num_id}{num_id}'
                p_tag.string = re.sub(r'^\d{0,2}\.\d+\.*(\d+)*', '', p_tag.text.strip())
                previous_li_tag = p_tag

            elif re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                num_count = 1
                cap_alpha_cur_tag1 = None

                if re.search(r'^\(a\)', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"

                    if num_tag:
                        sec_alpha_id = num_tag.get('id')
                        num_tag.append(sec_alpha_ol)

                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\([a-z]\)\s*\(\d+\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([a-z]\)\s*\(\d+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    num_cur_tag1 = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s*\((?P<pid>\d+)\)', current_tag_text)
                    num_id1 = f'{sec_alpha_id}{cur_tag.group("cid")}'
                    sec_alpha_id = f'{sec_alpha_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{num_id1}{cur_tag.group("pid")}'
                    num_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(num_ol1)
                    num_count = 2
                    cap_alpha1 = 'A'

                    if re.search(r'^\([a-z]\)\s*\(\d+\)\s?\(A\)', current_tag_text):
                        cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\([a-z]\)\s*\(\d+\)\s?\(A\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cap_alpha_cur_tag1 = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>[a-z])\)\s?\((?P<pid>\d+)\)\s\(?(?P<nid>A)\)',
                                            current_tag_text)

                        cap_alpha_id1 = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag["id"] = f'{num_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_alpha_ol1.append(inner_li_tag)
                        num_cur_tag1.string = ""
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha1 = 'B'
                previous_li_tag = p_tag

            elif re.search(rf'^\({num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag1 = p_tag
                cap_alpha1 = 'A'
                cap_alpha2 = 'A'

                if re.search(r'^\(1\)', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)

                    if sec_alpha_cur_tag:
                        num_id1 = sec_alpha_cur_tag.get('id')
                        sec_alpha_cur_tag.append(num_ol1)
                    else:
                        num_id1 = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"

                else:
                    num_ol1.append(p_tag)

                p_tag["id"] = f'{num_id1}{num_count}'
                p_tag.string = re.sub(rf'^\({num_count}\)', '', current_tag_text)
                num_count += 1

                if re.search(rf'^\(\d+\)\s*\([A-Z]\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type='A')
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\([A-Z]\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_alpha_cur_tag1 = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
                    if sec_alpha_cur_tag:
                        cap_alpha_id1 = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    else:
                        cap_alpha_id1 = f'{p_tag.find_previous({"h5", "h4", "h3", "h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}'

                        li_tag[
                            "id"] = f'{p_tag.find_previous({"h5", "h4", "h3", "h2"}).get("id")}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'

                    cap_alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol1)
                    cap_alpha1 = 'B'

                    if re.search(r'^\(\d+\)\s?\([A-Z]\)\s?\(i\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\d+\)\s?\([A-Z]\)\s?\(i\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s?\((?P<pid>[A-Z])\)\s\(?(?P<nid>i)\)',
                                            current_tag_text)
                        prev_id1 = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag[
                            "id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        roman_ol.append(inner_li_tag)
                        cap_alpha_cur_tag1.string = ""
                        cap_alpha_cur_tag1.append(roman_ol)
                        small_roman = "ii"
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha2}{cap_alpha2}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha_ol1.append(p_tag)
                p_tag_id = re.search(rf'^\((?P<p_id>{cap_alpha2}{cap_alpha2})\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_alpha_id1}{p_tag_id}'
                p_tag.string = re.sub(rf'^\({cap_alpha2}{cap_alpha2}\)', '', current_tag_text)
                cap_alpha2 = chr(ord(cap_alpha2) + 1)
                previous_li_tag = p_tag

            elif re.search(r'^\([IVX]+\)', current_tag_text) and p_tag.name == "p" \
                    and cap_alpha1 not in ['I', 'V', 'X']:
                p_tag.name = "li"
                cap_roman_cur_tag = p_tag

                if re.search(r'^\(I\)', current_tag_text):
                    cap_roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(cap_roman_ol)
                    roman_cur_tag.append(cap_roman_ol)
                    prev_id1 = roman_cur_tag.get('id')

                else:
                    cap_roman_ol.append(p_tag)

                rom_head = re.search(r'^\((?P<rom>[IVX]+)\)', current_tag_text)
                p_tag["id"] = f'{prev_id1}{rom_head.group("rom")}'
                p_tag.string = re.sub(r'^\([IVX]+\)', '', current_tag_text)

                if re.search(rf'^\([IVX]+\)\s*\(aa\)', current_tag_text):
                    alpha_ol1 = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([IVX]+\)\s*\(aa\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    cap_roman_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[IVX]+)\)\s*\((?P<pid>aa)\)', current_tag_text)

                    li_tag["id"] = f'{cap_roman_cur_tag.get("id")}{cur_tag.group("pid")}'
                    alpha_ol1.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(alpha_ol1)
                previous_li_tag = p_tag

            elif re.search(rf'^\({cap_alpha1}\)', current_tag_text) and p_tag.name == "p":
                cap_alpha2 = 'A'
                p_tag.name = "li"
                cap_alpha_cur_tag1 = p_tag
                small_roman = "i"

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol1 = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol1)
                    if num_cur_tag1:
                        num_cur_tag1.append(cap_alpha_ol1)
                        cap_alpha_id1 = num_cur_tag1.get("id")
                    else:
                        cap_alpha_id1 = f"{p_tag.find_previous(['h5', 'h4', 'h3', 'h2']).get('id')}ol{ol_count}"

                else:
                    cap_alpha_ol1.append(p_tag)

                p_tag["id"] = f'{cap_alpha_id1}{cap_alpha1}'
                p_tag.string = re.sub(rf'^\({cap_alpha1}\)', '', current_tag_text)
                if cap_alpha1 == 'Z':
                    cap_alpha1 = 'A'

                else:
                    cap_alpha1 = chr(ord(cap_alpha1) + 1)

                if re.search(rf'^\([A-Z]\)\s*\([ivx]+\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="i")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([A-Z]\)\s*\([ivx]+\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    roman_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[A-Z])\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                    prev_id1 = f'{cap_alpha_cur_tag1.get("id")}'
                    li_tag["id"] = f'{cap_alpha_cur_tag1.get("id")}{cur_tag.group("pid")}'
                    roman_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(roman_ol)
                    small_roman = "ii"

                    if re.search(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', current_tag_text):
                        cap_roman_ol = self.soup.new_tag("ol", type="I")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\([A-Z]\)\s*\([ivx]+\)\s*\([IVX]+\)', '', current_tag_text)
                        inner_li_tag.append(current_tag_text)
                        cap_roman_cur_tag = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>[A-Z])\)\s?\((?P<pid>[ivx]+)\)\s\(?(?P<nid>I)\)',
                                            current_tag_text)
                        prev_id1 = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}'

                        inner_li_tag["id"] = f'{roman_cur_tag.get("id")}{cur_tag.group("pid")}{cur_tag.group("nid")}'
                        cap_roman_ol.append(inner_li_tag)
                        roman_cur_tag.string = ""
                        roman_cur_tag.append(cap_roman_ol)
                previous_li_tag = p_tag

            elif re.search(r'^\([a-z][a-z]\)', current_tag_text) and cap_roman_cur_tag:
                p_tag.name = "li"
                if re.search(r'^\(aa\)', current_tag_text):
                    alpha_ol1 = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(alpha_ol1)
                    cap_roman_cur_tag.append(alpha_ol1)

                elif alpha_ol1:

                    alpha_ol1.append(p_tag)

                p_tag_id = re.search(r'^\((?P<p_id>[a-z][a-z])\)', current_tag_text).group('p_id')
                p_tag["id"] = f'{cap_roman_cur_tag.get("id")}{p_tag_id}'
                p_tag.string = re.sub(r'^\([a-z][a-z]\)', '', current_tag_text)
                previous_li_tag = p_tag

            elif p_tag.get("class") == [self.tag_type_dict["ol"]] \
                    and not re.search(r'^HISTORY:|^History', current_tag_text) and previous_li_tag:
                if previous_li_tag:
                    previous_li_tag.append(p_tag)

            if re.search(r'^CASE NOTES|^HISTORY:', current_tag_text) or p_tag.name in ['h3', 'h4', 'h5']:
                num_count = 1
                main_sec_alpha = 'a'
                num_cur_tag1 = None
                sec_alpha_cur_tag = None
                cap_alpha1 = "A"
                cap_alpha2 = "A"
                sec_alpha_id = None
                num_tag = None
                small_roman = "i"
                alpha_ol1 = None
                cap_alpha_cur_tag1 = None
                cap_roman_cur_tag = None
                previous_li_tag = None

        print('ol tags added')

    def create_analysis_nav_tag(self):
        super(VTParseHtml, self).create_case_note_analysis_nav_tag()
        print("Case Notes nav created")

    def replace_tags_constitution(self):
        super(VTParseHtml, self).replace_tags_constitution()
        cap_roman = "I"
        cap_alpha = None
        cap_num = None
        h5_alpha_id = None
        h5_rom_id = None
        cap_roman_tag = None
        annotation_text_list: list = []
        annotation_id_list: list = []
        h5_count = 1

        for header_tag in self.soup.find_all():
            if header_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^CASE NOTES$|^Analysis$|^ANNOTATIONS$', header_tag.text.strip()):
                    cap_roman = "I"
                    cap_roman_tag = None
                elif re.search(rf'^{cap_roman}\.', header_tag.text.strip()) and \
                        re.search(r'^ANNOTATIONS$', header_tag.find_previous("h4").text.strip()):
                    header_tag.name = "h5"
                    cap_roman_tag = header_tag
                    h5_rom_text = re.search(r'^(?P<h5_id>[IVX]+)\.', header_tag.text.strip()).group("h5_id")
                    h5_rom_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecisison-{h5_rom_text}'
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
                else:
                    annotation_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    if annotation_text in annotation_text_list and re.search(r'^ANNOTATIONS$', header_tag.find_previous(
                            "h4").text.strip()):
                        header_tag.name = "h5"
                        if cap_roman_tag:
                            annotation_id = f'{cap_roman_tag.get("id")}-{annotation_text}'
                        else:
                            annotation_id = f'{header_tag.find_previous({"h3", "h2", "h1"}).get("id")}-notetodecision-{annotation_text}'

                        if annotation_id in annotation_id_list:
                            header_tag["id"] = f'{annotation_id}.{h5_count}'
                            h5_count += 1
                        else:
                            header_tag["id"] = f'{annotation_id}'
                            h5_count = 1

                        annotation_id_list.append(annotation_id)

            if re.search(r'^Analysis|^ANNOTATIONS', header_tag.text.strip()):
                for tag in header_tag.find_next_siblings():
                    if tag.get('class') == [self.tag_type_dict["head4"]]:
                        break
                    else:
                        tag["class"] = "casenote"
                        annotation_text_list.append(re.sub(r'[\W\s]+', '', tag.text.strip()).lower())
