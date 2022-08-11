import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexND
from loguru import logger


class NDParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {
                'head1': r'^CONSTITUTION OF NORTH DAKOTA|CONSTITUTION OF THE UNITED STATES OF AMERICA',
                'ul': r'^PREAMBLE|^§ \d\.', 'head2': '^ARTICLE (I|1)',
                'head4': '^Source:', 'junk1': '^Text$',
                'head3': r'^Section \d\.|^§ \d\.', 'NTD': '^Notes to Decisions'}
        else:
            self.tag_type_dict: dict = {'head1': r'TITLE \d+', 'ul': r'^CHAPTER \d+(\.\d+)*-\d+',
                                        'head2': r'^CHAPTER \d+(\.\d+)*-\d+',
                                        'head4': r'^Source:',
                                        'head3': r'^\d+(\.\d+)*-\d+-\d+\.(\d+\.)*',
                                        'junk1': '^Annotations$', 'note_tag': '^Notes to Decisions'}

        self.h4_head: list = ['Revision of title. —', 'Cross references. —', 'Law reviews. —', 'Editor\'s notes. —',
                              'Official Comments.''History.', 'Effective dates. —', 'Notes to Decisions',
                              'DECISIONS UNDER PRIOR LAW', 'DECISIONS UNDER PRIOR PROVISIONS']

        self.junk_tag_class = ['Apple-converted-space', 'Apple-tab-span']

        self.watermark_text = """Release {0} of the Official Code of North Dakota Annotated released {1}. 
               Transformed and posted by Public.Resource.Org using cic-beautify-state-codes version v1.3 on {2}. 
               This document is not subject to copyright and is in the public domain.
               """

        self.regex_pattern_obj = CustomisedRegexND()
        if re.search(r'12\.html', self.input_file_name.strip()):
            self.h2_order: list = ['part', 'chapter', 'article', '', '']
        elif re.search(r'41\.html', self.input_file_name.strip()):
            self.h2_order: list = ['chapter', 'part', 'article', '', '']
        elif re.search(r'30\.1\.html', self.input_file_name.strip()):
            self.h2_order: list = ['article', 'chapter', 'part', '', '']
        else:
            self.h2_order: list = ['chapter', 'article', 'part', '', '']

    def replace_tags_titles(self):
        super(NDParseHtml, self).replace_tags_titles()
        note_to_decision_list: list = []
        cur_id_list: list = []
        note_to_decision_id: list = []
        h5count = 1
        count = 1

        for p_tag in self.soup.find_all():
            if p_tag.get("class") == [self.tag_type_dict["note_tag"]]:
                if p_tag.text.strip() in self.h4_head:
                    p_tag.name = "h4"
                    h4_text = re.sub(r'\W+', '', p_tag.text.strip()).lower()
                    curr_tag_id = f"{p_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"
                    if curr_tag_id in cur_id_list:
                        p_tag[
                            'id'] = f"{p_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}.{self.head4count}"
                        self.head4count += 1
                    else:
                        p_tag['id'] = f"{p_tag.find_previous({'h3', 'h2', 'h1'}).get('id')}-{h4_text}"
                        self.head4count = 1

                    cur_id_list.append(p_tag['id'])
                    header4_tag = p_tag
                    note_tag_head_id = None

            if p_tag.name == "h4":
                if re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR LAW', p_tag.text.strip(), re.I):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["head4"]] \
                                and not re.search(r'^\d+\.|^Analysis', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            note_to_decision_list.append(tag.text.strip())
                        elif tag.get("class") == [self.tag_type_dict["note_tag"]]:
                            break

            if p_tag.get("class") == [self.tag_type_dict["note_tag"]]:
                if p_tag.text.strip() in note_to_decision_list:
                    if re.search(r'^—\w+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        inner_case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_inner_id = f'{case_tag.get("id")}-{tag_text}'

                        if p_tag_inner_id in note_to_decision_id:
                            p_tag["id"] = f'{case_tag.get("id")}-{tag_text}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{case_tag.get("id")}-{tag_text}'
                            count = 1
                        note_to_decision_id.append(p_tag_inner_id)

                    elif re.search(r'^— —\w+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        inner_p_tag = p_tag

                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_inner1_id = f'{inner_case_tag.get("id")}-{tag_text}'

                        if p_tag_inner1_id in note_to_decision_id:
                            p_tag["id"] = f'{inner_case_tag.get("id")}-{tag_text}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{inner_case_tag.get("id")}-{tag_text}'
                            count = 1
                        note_to_decision_id.append(p_tag_inner1_id)

                    elif re.search(r'^— — —\w+', p_tag.text.strip()):
                        pass
                    elif re.search(r'^— — — —\w+', p_tag.text.strip()):
                        pass
                    else:
                        p_tag.name = "h5"
                        case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_id = f'{p_tag.find_previous("h3").get("id")}-notetodecision-{tag_text}'

                        if p_tag_id in note_to_decision_id:
                            p_tag["id"] = f'{p_tag_id}.{h5count:02}'
                            h5count += 1
                        else:
                            p_tag["id"] = f'{p_tag_id}'
                            h5count = 1

                        note_to_decision_id.append(p_tag_id)

        self.replace_h3_title()
        logger.info("Tags are replaced in the child class")

    def convert_paragraph_to_alphabetical_ol_tags(self):
        """
            For each tag which has to be converted to orderd list(<ol>)
            - create new <ol> tags with appropriate type (1, A, i, a ..)
            - get previous headers id to set unique id for each list item (<li>)
            - append each li to respective ol accordingly
        """
        inner_sec_alpha = 'a'
        ol_head = 1
        num_count = 1
        inner_num_count = 1
        ol_count = 1
        main_sec_alpha = 'a'
        sec_alpha = 'a'
        sec_alpha_cur_tag = None
        inr_sec_alpha_cur_tag = None
        num_cur_tag = None
        inr_num_cur_tag = None
        ol_head_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^{num_count}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                num_cur_tag = p_tag
                main_sec_alpha = 'a'
                inr_sec_alpha_cur_tag = None
                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    num_cur_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                    ol_count += 1
                else:
                    num_ol.append(p_tag)
                p_tag["id"] = f'{num_cur_id}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count = num_count + 1

                if re.search(rf'^\d+\.\s*a\.', current_tag_text):
                    p_tag.name = "li"
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\d+\.\s*a\.', '', current_tag_text)
                    sec_alpha_cur_tag = li_tag
                    sec_alpha_id = f'{num_cur_tag.get("id")}'
                    li_tag["id"] = f'{num_cur_tag.get("id")}a'
                    sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(sec_alpha_ol)
                    main_sec_alpha = "b"
                    inner_num_count = 1

            elif re.search(rf'^{main_sec_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                inner_num_count = 1
                inr_sec_alpha_cur_tag = None
                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_cur_tag:
                        num_cur_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_cur_tag.get('id')
                else:
                    sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{sec_alpha_id}{main_sec_alpha}'
                p_tag.string = re.sub(rf'^{main_sec_alpha}\.', '', current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                if re.search(rf'^\D+\.\s\(1\)', current_tag_text):
                    p_tag.name = "li"
                    inr_num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\D+\.\s\(1\)', '', current_tag_text)
                    inr_num_cur_tag = li_tag
                    inr_num_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    inr_num_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_num_ol)
                    inner_num_count = 2

            elif re.search(rf'^{sec_alpha}{sec_alpha}\.', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag
                inner_num_count = 1
                inr_sec_alpha_cur_tag = None
                sec_alpha_ol.append(p_tag)
                sec_alpha_id = num_cur_tag.get('id')
                p_tag["id"] = f'{sec_alpha_id}{sec_alpha}{sec_alpha}'
                p_tag.string = re.sub(rf'^{sec_alpha}{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

            elif re.search(rf'^\({inner_num_count}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_num_cur_tag = p_tag
                inner_sec_alpha = 'a'
                if re.search(r'^\(1\)', current_tag_text):
                    inr_num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inr_num_ol)
                    if inr_sec_alpha_cur_tag:
                        inr_sec_alpha_cur_tag.append(inr_num_ol)
                        inr_num_id = inr_sec_alpha_cur_tag.get('id')
                    elif sec_alpha_cur_tag:
                        sec_alpha_cur_tag.append(inr_num_ol)
                        inr_num_id = sec_alpha_cur_tag.get('id')
                    else:
                        inr_num_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inr_num_ol.append(p_tag)
                p_tag["id"] = f'{inr_num_id}{inner_num_count}'
                p_tag.string = re.sub(rf'^\({inner_num_count}\)', '', current_tag_text)
                inner_num_count = inner_num_count + 1

                if re.search(rf'^\(\d+\)\s*\(a\)', current_tag_text):
                    p_tag.name = "li"
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)\s*\(a\)', '', current_tag_text)
                    inr_sec_alpha_cur_tag = li_tag
                    inr_sec_alpha_id = f'{inr_num_cur_tag.get("id")}'
                    li_tag["id"] = f'{inr_num_cur_tag.get("id")}a'
                    inr_sec_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_sec_alpha_ol)
                    inner_sec_alpha = 'b'
                    ol_head = 1

            elif re.search(rf'^\({inner_sec_alpha}\)', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                inr_sec_alpha_cur_tag = p_tag
                ol_head = 1
                if re.search(r'^\(a\)', current_tag_text):
                    inr_sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(inr_sec_alpha_ol)
                    if inr_num_cur_tag:
                        inr_num_cur_tag.append(inr_sec_alpha_ol)
                        inr_sec_alpha_id = inr_num_cur_tag.get('id')
                    else:
                        inr_sec_alpha_id = f"{p_tag.find_previous({'h5', 'h4', 'h3', 'h2'}).get('id')}ol{ol_count}"
                else:
                    inr_sec_alpha_ol.append(p_tag)

                p_tag["id"] = f'{inr_sec_alpha_id}{inner_sec_alpha}'
                p_tag.string = re.sub(rf'^\({inner_sec_alpha}\)', '', current_tag_text)
                inner_sec_alpha = chr(ord(inner_sec_alpha) + 1)

                if re.search(rf'^\(\D\)\s*\[1\]', current_tag_text):
                    p_tag.name = "li"
                    inr_head_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\D\)\s*\[1\]', '', current_tag_text)
                    ol_head_cur_tag = li_tag
                    ol_head_id = f'{sec_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{sec_alpha_cur_tag.get("id")}1'
                    inr_head_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(inr_head_ol)
                    ol_head = 2

            elif re.search(rf'^\[{ol_head}\]', current_tag_text) and p_tag.name == "p":
                p_tag.name = "li"
                ol_head_cur_tag = p_tag
                if re.search(r'^\[1\]', current_tag_text):
                    inr_head_ol = self.soup.new_tag("ol")
                    p_tag.wrap(inr_head_ol)
                    inr_sec_alpha_cur_tag.append(inr_head_ol)
                    ol_head_id = inr_sec_alpha_cur_tag.get('id')
                else:
                    inr_head_ol.append(p_tag)

                p_tag["id"] = f'{ol_head_id}{ol_head}'
                p_tag.string = re.sub(rf'^\[{ol_head}\]', '', current_tag_text)
                ol_head = ol_head + 1

            if p_tag.name in ['h3', 'h4', 'h5']:
                inner_sec_alpha = 'a'
                ol_head = 1
                num_count = 1
                inner_num_count = 1
                ol_count = 1
                main_sec_alpha = 'a'
                sec_alpha_cur_tag = None
                inr_sec_alpha_cur_tag = None
                num_cur_tag = None
                inr_num_cur_tag = None

        logger.info("ol tags are created in child class")

    def create_analysis_nav_tag(self):
        if re.search('constitution', self.input_file_name):
            self.create_Notes_to_decision_analysis_nav_tag_con()
        else:
            super(NDParseHtml, self).create_Notes_to_decision_analysis_nav_tag()

        logger.info("Note to decision nav is created in child class")

    def replace_tags_constitution(self):
        super(NDParseHtml, self).replace_tags_constitution()

        note_to_decision_id = []
        note_to_decision_list = []
        h4_count = 1

        for p_tag in self.soup.find_all("p", class_=self.tag_type_dict["head2"]):
            if re.search('^(TRANSITION SCHEDULE|ARTICLES|DISTRICT COURTS|COUNTY COURTS|'
                         'JUSTICES OF THE PEACE|POLICE MAGISTRATES|MISCELLANEOUS|ARTICLES OF AMENDMENT)$',
                         p_tag.text.strip()):
                p_tag.name = "h2"
                p_tag_text = re.sub(r'\W+', '', p_tag.text.strip()).lower()
                p_tag["id"] = f"{p_tag.find_previous('h1').get('id')}-{p_tag_text}"
                p_tag["class"] = "oneh2"
            elif self.regex_pattern_obj.article_pattern_con.search(p_tag.text.strip()):
                p_tag.name = "h4"
                p_tag["id"] = f"{p_tag.find_previous('h2', class_='oneh2').get('id')}" \
                              f"a{self.regex_pattern_obj.article_pattern_con.search(p_tag.text.strip()).group('id').zfill(2)}"

        self.replace_h3_tags_con()

        for p_tag in self.soup.find_all("p"):
            if p_tag.get("class") == [self.tag_type_dict["NTD"]]:
                p_tag_text = re.sub(r'\W+','',p_tag.text.strip())
                if p_tag_text in note_to_decision_list:

                    if re.search(r'^—\w+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        inner_case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_inner_id = f'{case_tag.get("id")}-{tag_text}'

                        if p_tag_inner_id in note_to_decision_id:
                            p_tag["id"] = f'{case_tag.get("id")}-{tag_text}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{case_tag.get("id")}-{tag_text}'
                            count = 1
                        note_to_decision_id.append(p_tag_inner_id)

                    elif re.search(r'^— —\w+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        inner_p_tag = p_tag

                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()
                        p_tag_inner1_id = f'{inner_case_tag.get("id")}-{tag_text}'

                        if p_tag_inner1_id in note_to_decision_id:
                            p_tag["id"] = f'{inner_case_tag.get("id")}-{tag_text}.{count:02}'
                            count += 1
                        else:
                            p_tag["id"] = f'{inner_case_tag.get("id")}-{tag_text}'
                            count = 1
                        note_to_decision_id.append(p_tag_inner1_id)

                    elif re.search(r'^— — —\w+', p_tag.text.strip()):
                        pass
                    elif re.search(r'^— — — —\w+', p_tag.text.strip()):
                        pass

                    elif re.search(r'^[IVX]+\.', p_tag.text.strip()):
                        p_tag.name = "h5"
                        rom_tag = p_tag
                        rom_num = re.search(r'^(?P<id>[IVX]+)\.', p_tag.text.strip()).group("id")
                        rom_id = f'{p_tag.find_previous("h3").get("id")}-notetodecision-{rom_num}'
                        if rom_id in note_to_decision_id:
                            p_tag["id"] = f'{rom_id}.{h5count:02}'
                            h5count += 1
                        else:
                            p_tag["id"] = f'{rom_id}'
                            h5count = 1

                        note_to_decision_id.append(rom_id)

                    else:
                        p_tag.name = "h5"
                        case_tag = p_tag
                        tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip()).lower()

                        if rom_tag:
                            p_tag_id = f'{rom_tag.get("id")}-{tag_text}'
                        else:
                            p_tag_id = f'{p_tag.find_previous("h3").get("id")}-notetodecision-{tag_text}'

                        if p_tag_id in note_to_decision_id:
                            p_tag["id"] = f'{p_tag_id}.{h5count:02}'
                            h5count += 1
                        else:
                            p_tag["id"] = f'{p_tag_id}'
                            h5count = 1

                        note_to_decision_id.append(p_tag_id)
                else:
                    self.replace_h4_tag_titles(p_tag, h4_count)
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            if p_tag.get("class") == [self.tag_type_dict["NTD"]] or \
                    p_tag.get("class") == [self.tag_type_dict["head4"]]:
                if re.search(r'^Notes to Decisions|^DECISIONS UNDER PRIOR LAW|^Analysis', p_tag.text.strip(), re.I):
                    for tag in p_tag.find_next_siblings():
                        if tag.get("class") == [self.tag_type_dict["head4"]] \
                                and not re.search(r'^\d+\.|^Analysis', tag.text.strip()):
                            tag.name = "li"
                            tag["class"] = "note"
                            tag_text = re.sub(r'\W+','',tag.text.strip())
                            note_to_decision_list.append(tag_text)
                        elif tag.get("class") == [self.tag_type_dict["NTD"]]:
                            rom_tag = None
                            break


    def add_anchor_tags_con(self):
        super(NDParseHtml, self).add_anchor_tags_con()
        self.c_nav_count = 0
        for li in self.soup.find_all("li"):
            if not li.get("id"):
                if re.search('^(TRANSITION SCHEDULE|ARTICLES|DISTRICT COURTS|'
                             'COUNTY COURTS|JUSTICES OF THE PEACE|POLICE MAGISTRATES|'
                             'MISCELLANEOUS|ARTICLES OF AMENDMENT)$', li.text.strip()):
                    li_tag_text = re.sub(r'\W+', '', li.text.strip()).lower()
                    self.c_nav_count = int(
                        re.search(r'cnav(?P<ncount>\d+)', li.find_previous("li").get("id").strip()).group("ncount")) + 1
                    self.set_chapter_section_id(li, li_tag_text,
                                                sub_tag="-",
                                                prev_id=li.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

                elif self.regex_pattern_obj.article_pattern_con.search(li.text.strip()):
                    li_tag_num = self.regex_pattern_obj.article_pattern_con.search(li.text.strip()).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li, li_tag_num,
                                                sub_tag="a",
                                                prev_id=li.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
