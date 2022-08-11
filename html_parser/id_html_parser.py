import re
from base_html_parser import ParseHtml
from regex_pattern import RegexPatterns, CustomisedRegexID


class IDParseHtml(ParseHtml, RegexPatterns):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):

        self.h2_subchapter_pattern = None
        self.h2_order = None
        self.tag_type_dict: dict = {'head1': r'^(Title|TITLE)\s*\d', 'ul': r'^Idaho Code Title \d',
                                    'head3': r'^§?\s?\d+-\d+\.|^§\s?\d+-\d+-\d+\.',
                                    'head4': '^STATUTORY NOTES',
                                    'junk1': 'Title \d', 'normalp': '^Editor\'s note',
                                    'article': r'^Article \d$|^Part \d$'}

        self.h4_head: list = ['Editor’s Notes —', 'Cross References —', 'NOTES TO DECISIONS', 'JUDICIAL DECISIONS',
                              'RESEARCH REFERENCES', 'ANNOTATION']

        self.watermark_text = """Release {0} of the Official Code of Idaho Annotated released {1}. 
                Transformed and posted by Public.Resource.Org using rtf-parser.py version 1.0 on {2}. 
                This document is not subject to copyright and is in the public domain.
                """
        self.regex_pattern_obj = CustomisedRegexID()

    def replace_tags_titles(self):

        for p_tag in self.soup.findAll("p", class_=self.tag_type_dict["head3"]):
            current_p_tag = p_tag.get_text()
            if re.search(r'^§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\.', current_p_tag):
                if head_text := re.search(r'^(?P<alpha>§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\..+)—', current_p_tag):
                    p_text = re.sub(r'^(§?\s?\d+-\d+[a-zA-Z]?(-\d+)?\..+)—', '', current_p_tag)
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = head_text.group('alpha')
                    new_p_tag["class"] = [self.tag_type_dict['head3']]
                    p_tag.insert_before(new_p_tag)
                    p_tag.string = p_text
                    p_tag["class"] = [self.tag_type_dict['ul']]

        sec_count = 1
        sec_head_id = []
        sub_sec_count = 1
        sub_sec_id = []
        cite_count = 1
        cite_id = []
        case_note_id = []
        case_note_count = 1
        self.snav_count = 1
        self.case_note_head = []

        for header_tag in self.soup.body.find_all():
            if header_tag.get("class") == [self.tag_type_dict['head1']]:
                if re.search(r'^(Title|TITLE)\s(?P<title>\d+)', header_tag.get_text()):
                    title_id = re.search(r"^Title\s(?P<title>\d+)", header_tag.get_text()).group("title")
                    header_tag.name = "h1"
                    header_tag["id"] = f't{title_id.zfill(2)}'
                    self.snav_count = 1
                    header_tag.wrap(self.soup.new_tag("nav"))
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif chap_head := re.search(r'Part\s?(?P<c_title>(\d+)?([IVX]+)?)', header_tag.get_text()):
                    header_tag.name = "h2"
                    if header_tag.find_previous("h2"):

                        prev_id = header_tag.find_previous("h2", class_='chapterh2').get("id")
                    else:
                        prev_id = header_tag.find_previous("h1").get("id")

                    header_tag["id"] = f'{prev_id}p{chap_head.group("c_title").zfill(2)}'
                    header_tag["class"] = "parth2"
                    sec_count = 1
                    self.snav_count = 1
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

                elif chap_head := re.search(r'(Chapter(s?)|CHAPTER(s?))\s(?P<c_title>\d+[a-zA-Z]?)',
                                            header_tag.get_text()):
                    header_tag.name = "h2"
                    header_tag[
                        "id"] = f'{header_tag.find_previous("h1").get("id")}c{chap_head.group("c_title").zfill(2)}'
                    sec_count = 1
                    header_tag["class"] = "chapterh2"
                    self.snav_count = 1
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})

            elif header_tag.get("class") == [self.tag_type_dict['head3']]:
                if sec_head := re.search(r'^§?(\s?)(?P<sec_id>\d+-\d+[a-zA-Z]?(-\d+)?)\.?', header_tag.get_text()):
                    header_tag.name = "h3"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                    if header_tag.find_previous("h2"):
                        header_tag_id = f'{header_tag.find_previous("h2").get("id")}s{sec_head.group("sec_id")}'
                    else:
                        header_tag_id = f'{header_tag.find_previous("h1").get("id")}s{sec_head.group("sec_id")}'

                    if header_tag_id in sec_head_id:
                        header_tag['id'] = f'{header_tag_id}.{sec_count}'
                        sec_count += 1
                    else:
                        header_tag['id'] = f'{header_tag_id}'
                    sec_head_id.append(header_tag_id)
                    case_note_count = 1

            elif header_tag.get("class") == [self.tag_type_dict['head4']]:
                self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
                if sec_head := re.search(r'^(ARTICLE|Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                    if re.search(r'^(ARTICLE)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                        prev_head_id = header_tag.find_previous(
                            lambda tag: tag.name in ["h2", "h3"] and tag.get("class") != "articleh3").get("id")
                        header_tag['id'] = f'{prev_head_id}a{sec_head.group("sec_id")}'

                    elif re.search(r'^(Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                        header_tag['id'] = f'{header_tag.find_previous("h4").get("id")}a{sec_head.group("sec_id")}'
                    header_tag.name = "h3"
                    header_tag["class"] = "articleh3"
                    case_note_count = 1

                elif header_tag.get_text().isupper():
                    header_tag.name = "h4"
                    header_tag_text = re.sub(r'[\s]*', '', header_tag.get_text())
                    if header_tag.find_previous("h3"):
                        casenote_id = f'{header_tag.find_previous("h3").get("id")}-{header_tag_text}'
                    else:
                        casenote_id = f'{header_tag.find_previous(["h2", "h1"]).get("id")}-{header_tag_text}'

                    if casenote_id in case_note_id:
                        header_tag["id"] = f'{casenote_id}.{case_note_count}'
                        case_note_count += 1
                    else:
                        header_tag["id"] = f'{casenote_id}'

                    case_note_id.append(casenote_id)
                    sub_sec_count = 1
                    cite_count = 1

                else:

                    if re.search(r'^History\.', header_tag.get_text()):
                        header_tag.name = "h5"
                        header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-history'

                    elif not re.search(r'^Part|^I\.C\.|^Chapter|^Sec\.|^This', header_tag.get_text()):
                        header_tag.name = "h5"
                        header_tag_text = re.sub(r'[\s.]*', '', header_tag.get_text()).lower()

                        subsec_head_id = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        if subsec_head_id in sub_sec_id:
                            header_tag[
                                "id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}{sub_sec_count}'
                            sub_sec_count += 1
                        else:
                            header_tag["id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        sub_sec_id.append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag.get_text().lower())

                if re.search(r'^CASE NOTES', header_tag.text.strip()):
                    for case_tag in header_tag.find_next_siblings():

                        if case_tag.get("class") == [self.tag_type_dict['ul']] and not case_tag.b:
                            case_tag.name = "li"
                            case_tag.wrap(self.ul_tag)
                        elif case_tag.get("class") == [self.tag_type_dict['ul']] and case_tag.b:
                            break


            if header_tag.get("class") == [self.tag_type_dict['ul']]:



                if re.search(r'^Chapter|^Section\.', header_tag.text.strip()):
                    for chap_tag in header_tag.find_next_siblings():
                        if chap_tag.get("class") == [self.tag_type_dict['ul']]:
                            chap_tag.name = "li"
                            chap_tag.wrap(self.ul_tag)
                        else:
                            break

                elif header_tag.b and not re.search(r'^Cited', header_tag.b.get_text()):
                    header_tag.name = "h5"

                    if re.search(r'^History\.', header_tag.get_text()):
                        header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-history'
                    else:

                        header_tag_text = re.sub(r'[\s.]*', '', header_tag.b.get_text()).lower()

                        subsec_head_id = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        if subsec_head_id in sub_sec_id:
                            header_tag[
                                "id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}{sub_sec_count}'
                            sub_sec_count += 1
                        else:
                            header_tag["id"] = f'{header_tag.find_previous(["h3", "h4"]).get("id")}-{header_tag_text}'
                        sub_sec_id.append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag_text)

                elif header_tag.get_text() == 'Chapter':
                    header_tag.find_previous("nav").append(header_tag)

                elif re.search(r'^Cited', header_tag.get_text()):
                    header_tag.name = "h4"
                    headertag_text = re.sub(r'[\s]*', '', header_tag.get_text()).lower()
                    if header_tag.find_previous("h3"):
                        cite_head_id = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}'
                    else:
                        cite_head_id = f'{header_tag.find_previous(["h2", "h1"]).get("id")}-{headertag_text}'

                    if cite_head_id in cite_id:
                        header_tag["id"] = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}.{cite_count}'
                        cite_count += 1
                    else:
                        header_tag["id"] = f'{header_tag.find_previous("h3").get("id")}-{headertag_text}'

                    sub_sec_count = 1
                    cite_id.append(cite_head_id)

                elif sec_head := re.search(r'^(ARTICLE|Article)(\s?)(?P<sec_id>[IVX]+)', header_tag.get_text()):
                    header_tag['id'] = f'{header_tag.find_previous("h4").get("id")}a{sec_head.group("sec_id")}'
                    header_tag.name = "h3"
                    header_tag["class"] = "articleh3"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})



            elif 'head' in self.tag_type_dict:
                if header_tag.get("class") == [self.tag_type_dict['head']]:
                    header_tag.name = "h5"

                    if re.search(r'^History\.', header_tag.get_text()):
                        header_tag["id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-history'
                    else:
                        header_tag_text = re.sub(r'[\s.]*', '', header_tag.get_text()).lower()
                        if header_tag.find_previous("h4"):
                            subsec_head_id = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}'
                            if subsec_head_id in sub_sec_id:
                                header_tag[
                                    "id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}{sub_sec_count}'
                                sub_sec_count += 1
                            else:
                                header_tag[
                                    "id"] = f'{header_tag.find_previous(["h4", "h3"]).get("id")}-{header_tag_text}'
                        else:
                            subsec_head_id = f'{header_tag.find_previous(["h3", "h2", "h1"]).get("id")}-{header_tag_text}'

                            if subsec_head_id in sub_sec_id:
                                header_tag[
                                    "id"] = f'{subsec_head_id}{sub_sec_count}'
                                sub_sec_count += 1
                            else:
                                header_tag["id"] = f'{subsec_head_id}'

                        sub_sec_id.append(subsec_head_id)
                        sub_sec_count = 1
                        self.case_note_head.append(header_tag_text)

            if len(header_tag.get_text(strip=True)) == 0:
                header_tag.extract()

        print('tags replaced')


    def add_anchor_tags(self):

        for list_item in self.soup.find_all("li"):
            if sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?)\s*[.—,]', list_item.get_text()):
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h2').get('id')}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count = 1
                list_item[
                    "id"] = f"{list_item.find_previous('h2').get('id')}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1

            elif sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?-(?P<p_id>\d{1})\d{2})\.',
                                       list_item.get_text()):
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link[
                    "href"] = f"#{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count = 1
                list_item[
                    "id"] = f"{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1
            elif sec_list := re.search(r'^(?P<chap_id>\d+-\d+[a-zA-Z]?[a-zA-Z]?-(?P<p_id>\d{2})\d{2})\.',
                                       list_item.get_text()):
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link[
                    "href"] = f"#{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}"
                nav_list.append(nav_link)
                list_item.contents = nav_list
                if list_item.find_previous().name == "ul":
                    self.snav_count = 1
                list_item[
                    "id"] = f"{list_item.find_previous('h2').get('id')}p{sec_list.group('p_id').zfill(2)}s{sec_list.group('chap_id')}-snav{self.snav_count:02}"
                self.snav_count += 1

            elif chap_list := re.search(r'^(Chapter\s?)*(?P<chap_id>\d+[a-zA-Z]?)\.?,?', list_item.get_text()):
                if not list_item.find_previous("h3"):
                    nav_list = []
                    nav_link = self.soup.new_tag('a')
                    nav_link.append(list_item.text)
                    nav_link[
                        "href"] = f"#{list_item.find_previous('h1').get('id')}c{chap_list.group('chap_id').zfill(2)}"
                    nav_list.append(nav_link)
                    list_item.contents = nav_list
                    list_item[
                        "id"] = f"{list_item.find_previous('h1').get('id')}c{chap_list.group('chap_id').zfill(2)}-cnav{self.snav_count:02}"
                    self.snav_count += 1

            else:
                list_item_text = re.sub(r'[\s.]*', '', list_item.get_text()).lower()
                nav_list = []
                nav_link = self.soup.new_tag('a')
                nav_link.append(list_item.text)
                nav_link["href"] = f"#{list_item.find_previous('h4').get('id')}-{list_item_text}"
                nav_list.append(nav_link)
                list_item.contents = nav_list

    def create_analysis_nav_tag(self):
        super(IDParseHtml, self).create_case_note_analysis_nav_tag()
        print("Annotation analysis nav created")


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
        alpha_ol = self.soup.new_tag("ol", Class="alpha")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        num_ol = self.soup.new_tag("ol")
        ol_count = 1
        ol_list = []
        innr_roman_ol = None
        cap_alpha_cur_tag = None
        new_alpha = None
        ol_head1 = 1
        main_sec_alpha1 = 'a'
        flag = 0
        cap_alpha_head = "A"
        num_count1 = 1

        for p_tag in self.soup.find_all(['p', 'h3', 'h4', 'h5']):
            if p_tag.b:
                p_tag.b.unwrap()
            if p_tag.i:
                p_tag.i.unwrap()

            current_tag_text = p_tag.text.strip()
            if p_tag.name == "h3":
                num_cur_tag = None

            if re.search(rf'^\({ol_head}\)|^\({ol_head1}\)', current_tag_text):
                p_tag.name = "li"
                num_cur_tag = p_tag
                cap_alpha = 'A'
                main_sec_alpha = "a"
                if re.search(r'^\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")

                    p_tag.wrap(num_ol)
                    prev_head_id = p_tag.find_previous(["h5", "h4", "h3"]).get("id")

                    if alpha_cur_tag:
                        alpha_cur_tag.append(num_ol)
                        prev_head_id = alpha_cur_tag.get("id")
                        prev_num_id = f'{prev_head_id}'
                        p_tag["id"] = f'{prev_head_id}{ol_head}'
                    else:
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
                ol_head += 1
                ol_head1 += 1

                if re.search(r'^\(\d+\)(\s)?\([a-z]\)', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)?\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)', current_tag_text)
                    prevnum_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(alpha_ol)
                    main_sec_alpha = "b"

                elif re.search(r'^\(\d+\)(\s)?\([A-Z]\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\(\d+\)(\s)?\(\w\)', '', current_tag_text)
                    li_tag.append(current_tag_text)
                    # alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>\d+)\)(\s)?\((?P<pid>\w)\)', current_tag_text)
                    prev_id = f'{prev_head_id}{cur_tag.group("cid")}'
                    li_tag["id"] = f'{prev_head_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(cap_alpha_ol)
                    cap_alpha = "B"



            # a
            elif re.search(rf'^\(\s*{main_sec_alpha}\s*\)|^{main_sec_alpha}\.|^\(\s*{main_sec_alpha1}\s*\)',
                           current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                roman_count = 1
                num_count = 1
                ol_head1 = 1

                if re.search(r'^\(a\)|^a\.', current_tag_text):
                    alpha_ol = self.soup.new_tag("ol", Class="alpha")
                    p_tag.wrap(alpha_ol)
                    if num_cur_tag:
                        prevnum_id = num_cur_tag.get("id")
                        num_cur_tag.append(alpha_ol)
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'
                        flag = 0
                    else:
                        flag = 1
                        prevnum_id = p_tag.find_previous(["h4", "h3"]).get("id")
                        p_tag["id"] = f'{p_tag.find_previous(["h4", "h3"]).get("id")}ol{ol_count}{main_sec_alpha1}'
                else:

                    alpha_ol.append(p_tag)

                    if flag:
                        p_tag["id"] = f'{p_tag.find_previous(["h4", "h3"]).get("id")}ol{ol_count}{main_sec_alpha1}'
                    else:
                        p_tag["id"] = f'{prevnum_id}{main_sec_alpha}'

                p_tag.string = re.sub(rf'^\(\s*{main_sec_alpha}\s*\)|^\(\s*{main_sec_alpha1}\s*\)', '',
                                      current_tag_text)
                main_sec_alpha = chr(ord(main_sec_alpha) + 1)
                main_sec_alpha1 = chr(ord(main_sec_alpha1) + 1)

                if re.search(r'^\(\w\)\s?\([ivx]+\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s?\([ivx]+\)', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                    inner_li_tag[
                        "id"] = f'{prev_head_id}ol{ol_count}{ol_head - 1}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    innr_roman_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, innr_roman_ol)
                    prev_alpha = p_tag

                if re.search(r'^\(\w\)\s?\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    inner_li_tag = self.soup.new_tag("li")
                    inner_li_tag.string = re.sub(r'^\(\w\)\s?\(1\)', '', current_tag_text)
                    inner_li_tag.append(current_tag_text)
                    alpha_cur_tag = inner_li_tag
                    cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>1)\)', current_tag_text)
                    prev_head_id = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    inner_li_tag[
                        "id"] = f'{prevnum_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    num_ol.append(inner_li_tag)
                    p_tag.string = ""
                    p_tag.insert(0, num_ol)
                    ol_head = 2
                    # prev_alpha = p_tag


            # i
            elif re.search(r'^\([ivx]+\)', current_tag_text):
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(i\)', current_tag_text):
                    innr_roman_ol = self.soup.new_tag("ol", type="i")

                    p_tag.wrap(innr_roman_ol)
                    p_tag.find_previous("li").append(innr_roman_ol)
                    prev_alpha = p_tag.find_previous("li")
                    p_tag["id"] = f'{prev_alpha.get("id")}i'

                else:
                    cur_tag = re.search(r'^\((?P<cid>[ivx]+)\)', current_tag_text).group("cid")
                    if innr_roman_ol:
                        innr_roman_ol.append(p_tag)
                        p_tag["id"] = f'{prev_alpha.get("id")}{cur_tag}'
                    else:
                        alpha_ol.append(p_tag)
                        prev_alpha_id = f'{prev_num_id}{cur_tag}'
                        p_tag["id"] = f'{prev_num_id}{cur_tag}'

                p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)', '', current_tag_text)
                # num_count = 1


            # 1
            elif re.search(rf'^{num_count}\.', current_tag_text) and p_tag.get('class') == [
                self.tag_type_dict['ul']] and p_tag.name != "li":
                p_tag.name = "li"
                cap_alpha = "A"
                num_tag = p_tag

                if re.search(r'^1\.', current_tag_text):
                    num_ol1 = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol1)
                    prev_id = p_tag.find_previous(["h5", "h4", "h3"]).get("id")

                    if alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)
                else:
                    num_ol1.append(p_tag)

                if alpha_cur_tag:
                    p_tag["id"] = f'{prev_id}{num_count}'
                else:
                    p_tag["id"] = f'{prev_id}ol{ol_count}{num_count}'
                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1


            elif re.search(rf'^{num_count}\.|^{num_count1}\.', current_tag_text) and p_tag.get('class') == [
                self.tag_type_dict['ul']] and p_tag.name != "li":
                p_tag.name = "li"
                num_tag = p_tag
                cap_alpha = "A"

                if re.search(r'^1\.', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    p_tag.wrap(num_ol)
                    prev_id = p_tag.find_previous(["h4", "h3"]).get("id")
                    if re.search(r'^ARTICLE [IVX]+', p_tag.find_previous("h3").get_text().strip()):
                        prev_id = cap_alpha_head_tag.get("id")
                        cap_alpha_head_tag.append(num_ol1)
                    elif alpha_cur_tag:
                        prev_id = alpha_cur_tag.get("id")
                        alpha_cur_tag.append(num_ol1)


                else:
                    num_ol.append(p_tag)

                if re.search(r'^ARTICLE [IVX]+', p_tag.find_previous("h3").get_text().strip()):
                    p_tag["id"] = f'{prev_id}{num_count1}'
                elif alpha_cur_tag:
                    p_tag["id"] = f'{prev_id}{num_count}'
                else:
                    p_tag["id"] = f'{prev_id}ol{ol_count}{num_count}'

                p_tag.string = re.sub(rf'^{num_count}\.', '', current_tag_text)
                num_count += 1

                p_tag.string = re.sub(rf'^{num_count1}\.', '', current_tag_text)
                num_count1 += 1


            # (A)
            elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                p_tag.name = "li"
                cap_alpha_cur_tag = p_tag
                cap_alpha1 = cap_alpha

                if re.search(r'^\(A\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(cap_alpha_ol)
                    prev_id = p_tag.find_previous("li").get("id")
                    p_tag.find_previous("li").append(cap_alpha_ol)

                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{prev_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                cap_alpha = chr(ord(cap_alpha) + 1)

            # A
            elif re.search(rf'^{cap_alpha_head}\.\s', current_tag_text):
                p_tag.name = "li"
                cap_alpha_head_tag = p_tag
                cap_alpha1 = cap_alpha
                num_count1 = 1

                if re.search(r'^A\.', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    print(p_tag)

                    p_tag.wrap(cap_alpha_ol)
                    prev_id = p_tag.find_previous("h3").get("id")
                    # p_tag.find_previous("li").append(cap_alpha_ol)

                else:
                    cap_alpha_ol.append(p_tag)
                p_tag["id"] = f'{prev_id}{cap_alpha_head}'
                p_tag.string = re.sub(rf'^{cap_alpha_head}\.', '', current_tag_text)
                cap_alpha_head = chr(ord(cap_alpha_head) + 1)




            elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
                curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
                p_tag.name = "li"
                if re.search(r'^\(i{2,3}\)', current_tag_text):
                    if p_tag.find_next_sibling():
                        if re.search(r'^\(j{2,3}\)', p_tag.find_next_sibling().get_text().strip()):
                            alpha_cur_tag = p_tag
                            alpha_ol.append(p_tag)
                            prev_alpha_id = f'{prev_num_id}{curr_id}'
                            p_tag["id"] = f'{prev_num_id}{curr_id}'
                            roman_count = 1
                            p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)
                        else:
                            innr_roman_ol.append(p_tag)
                            p_tag["id"] = f'{prev_alpha.get("id")}{curr_id}'
                    else:
                        alpha_cur_tag = p_tag
                        alpha_ol.append(p_tag)
                        prev_alpha_id = f'{prev_num_id}{curr_id}'
                        p_tag["id"] = f'{prev_num_id}{curr_id}'
                        roman_count = 1
                        p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)


                else:
                    alpha_cur_tag = p_tag
                    alpha_ol.append(p_tag)
                    prev_alpha_id = f'{prev_num_id}{curr_id}'
                    p_tag["id"] = f'{prev_num_id}{curr_id}'
                    roman_count = 1
                    p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)

            if re.search(r'^History|^Cross references:|^OFFICIAL COMMENT', current_tag_text) or p_tag.name in ['h3',
                                                                                                               'h4',
                                                                                                               'h5']:
                ol_head = 1
                ol_head1 = 1
                num_count = 1
                num_cur_tag = None
                new_alpha = None
                main_sec_alpha = 'a'
                main_sec_alpha1 = 'a'
                alpha_cur_tag = None
                cap_alpha_head = "A"
                num_count1 = 1

        print('ol tags added')

    # def create_analysis_nav_tag(self):
    #     super(IDParseHtml, self).create_annotation_analysis_nav_tag()
    #     print("Annotation analysis nav created")

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
            super(IDParseHtml, self).add_cite()
