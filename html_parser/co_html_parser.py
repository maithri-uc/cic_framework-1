import re
from base_html_parser import ParseHtml
from regex_pattern import CustomisedRegexCO
import roman
from loguru import logger


class COParseHtml(ParseHtml):

    def __init__(self, state_key, path, release_number, input_file_name):
        super().__init__(state_key, path, release_number, input_file_name)

    def pre_process(self):
        if re.search('constitution', self.input_file_name):
            self.tag_type_dict: dict = {'ul': '^Article I.', 'head2': '^Article I.',
                                        'head1': '^Declaration of Independence',
                                        'head3': r'^§ 1.', 'junk1': '^Statute text', 'ol_p': r'^§',
                                        'head4': '^ANNOTATIONS|^ANNOTATION', 'art_head': '^ARTICLE',
                                        'amd': '^AMENDMENTS', 'Analysis': r'^I\.', 'section': '^Section 1.'}
        else:
            self.tag_type_dict: dict = {'ul': '^Art.', 'head2': '^ARTICLE|^Article|^Part',
                                        'head1': '^(TITLE|Title)|^(CONSTITUTION OF KENTUCKY)',
                                        'head3': r'^\d+(\.\d+)*-\d+-\d+\.',
                                        'part_head': r'^PART\s\d+',
                                        'junk1': '^Annotations', 'ol_p': r'^(\(1\))',
                                        'head4': '^ANNOTATION', 'nd_nav': r'^1\.',
                                        'Analysis': r'^I\.', 'editor': '^Editor\'s note', 'h4_article': 'Article I'}

        self.h4_head: list = ['Editor’s Notes —', 'Cross References —', 'NOTES TO DECISIONS', 'JUDICIAL DECISIONS',
                              'RESEARCH REFERENCES', 'ANNOTATION','OFFICIAL COMMENT']

        self.watermark_text = """Release {0} of the Official Code of Colorado Annotated released {1}.
                       Transformed and posted by Public.Resource.Org using cic-beautify-state-codes.py version 1.4 on {2}.
                       This document is not subject to copyright and is in the public domain.
                       """
        self.h2_order: list = ['article', 'part', 'subpart', '']

        self.regex_pattern_obj = CustomisedRegexCO()

    def replace_tags_titles(self):
        super(COParseHtml, self).replace_tags_titles()
        num_p_tag = None
        for p_tag in self.soup.find_all("p"):
            if p_tag.get("class") == [self.tag_type_dict["head2"]]:
                p_tag.name = "h2"
            if p_tag.get("class") == [self.tag_type_dict["head4"]]:
                if num_p_tag and re.search(r'^\d+\.\s—\w+', p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag_text = re.sub(r'[\W\s]+', '', p_tag.text.strip())
                    p_tag["id"] = f'{num_p_tag}{p_tag_text}'
                elif re.search(r'^\d+\. ', p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag_num = re.search(r'^(?P<id>\d+)\. ', p_tag.text.strip()).group("id")
                    num_p_tag = f'{p_tag.find_previous("h3").get("id")}-judicialdecision-{p_tag_num}'
                    p_tag["id"] = num_p_tag
                else:
                    if re.search(r'^[IVX]+\.', p_tag.text.strip()):
                        p_tag.name = "h5"
                        chap_num = re.search(r'^(?P<id>[IVX]+)\.', p_tag.text.strip()).group("id")
                        p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-annotation-{chap_num}'

                    elif re.search(r'^[A-HJ-UW-Z]\.\s"?[A-Z][a-z]+', p_tag.text.strip()):
                        p_tag.name = "h5"
                        prev_id = p_tag.find_previous(lambda tag: tag.name in ['h5'] and re.search(r'^[IVX]+\.',
                                                                                                   tag.text.strip())).get(
                            "id")
                        chap_num = re.search(r'^(?P<id>[A-Z])\.', p_tag.text.strip()).group("id")
                        p_tag["id"] = f'{prev_id}-{chap_num}'

                    elif re.search(r'^[1-9]\.', p_tag.text.strip()):
                        p_tag.name = "h5"
                        if p_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())):

                            prev_id = p_tag.find_previous(
                                lambda tag: tag.name in ['h5'] and re.search(r'^[A-HJ-UW-Z]\.',
                                                                             tag.text.strip())).get("id")
                            chap_num = re.search(r'^(?P<id>[0-9])\.', p_tag.text.strip()).group("id")
                            p_tag["id"] = f'{prev_id}-{chap_num}'
                        else:
                            p_tag["class"] = [self.tag_type_dict['ol_p']]

            elif p_tag.get("class") == [self.tag_type_dict["part_head"]]:
                if self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()):
                    p_tag["class"] = "navhead"
                    p_tag[
                        "id"] = f'{p_tag.find_previous("h2").get("id")}p{self.regex_pattern_obj.h2_part_pattern.search(p_tag.text.strip()).group("id").zfill(2)}'

                if re.search(r'^——————————$', p_tag.text.strip()):
                    p_tag.decompose()

            elif p_tag.get("class") == [self.tag_type_dict["h4_article"]]:
                if re.search(r'^(ARTICLE|Article) [IVX]+', p_tag.text.strip()):
                    p_tag.name = "h4"
                    p_tag["id"] = f'{p_tag.find_previous("h3").get("id")}-' \
                                  f'a{re.search(r"^(ARTICLE|Article) (?P<aid>[IVX]+)", p_tag.text.strip()).group("aid")}'

    def add_anchor_tags(self):
        super(COParseHtml, self).add_anchor_tags()

        h2_article_pattern = re.compile(r'^(article|Art\.)\s(?P<id>\d+(\.\d+)*)', re.I)

        for li_tag in self.soup.findAll():
            if li_tag.name == "li" and not li_tag.get("id"):
                if h2_article_pattern.search(li_tag.text.strip()):
                    chap_num = h2_article_pattern.search(li_tag.text.strip()).group("id")
                    sub_tag = "a"
                    prev_id = li_tag.find_previous("h1").get("id")
                    self.c_nav_count += 1
                    cnav = f'cnav{self.c_nav_count:02}'
                    self.set_chapter_section_id(li_tag, chap_num, sub_tag, prev_id, cnav)

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
        if not re.search('constitution', self.input_file_name):
            for tag in self.soup.find_all("p", class_=[self.tag_type_dict['editor']]):
                if re.search(r'^Editor\'s note: \(\d+\)', tag.text.strip()):
                    new_h4_tag = self.soup.new_tag("h4")
                    new_h4_tag.string = tag.find_next("b").text
                    h4_text = re.sub(r'[\W\s]+', '', tag.find_next("b").text.strip()).lower()
                    new_h4_tag['id'] = f'{tag.find_previous({"h3", "h2", "h1"}).get("id")}-{h4_text}'
                    tag.insert_before(new_h4_tag)
                    tag.find_next("b").decompose()

        for p_tag in self.soup.find_all("p", class_=[self.tag_type_dict['ol_p']]):
            current_p_tag = p_tag.text.strip()
            if re.search(r'^\[.+\]\s*\(\d+(\.\d+)*\)', current_p_tag):
                alpha_text = re.sub(r'^\[.+\]\s*', '', current_p_tag)
                num_text = re.sub(r'\(1\).+', '', current_p_tag)
                new_p_tag = self.soup.new_tag("p")
                new_p_tag.string = alpha_text
                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                p_tag.insert_after(new_p_tag)
                p_tag.string = num_text

            if re.search(r'^\(\d+(\.\d+)*\)', current_p_tag):
                if p_tag.find_next().name == "b":
                    if re.search(r'^\[ Editor\'s note:', p_tag.find_next().text.strip()):
                        continue
                    else:
                        alpha_text = re.sub(r'^[^.]+\.', '', current_p_tag)
                        num_text = re.sub(r'\(a\).+', '', current_p_tag)
                        if re.search(r'^\s*\([a-z]\)', alpha_text):
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                        elif re.search(r'^.+\s(?P<alpha>\(a\)+)', current_p_tag):
                            alpha_text = re.search(r'^.+\s(?P<alpha>\(a\).+)', current_p_tag).group("alpha")
                            num_text = re.sub(r'\(a\).+', '', current_p_tag)
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

            if re.search(r'^\(\d+\)\s*\([a-z]+\)\s*.+\s*\([a-z]\)', current_p_tag):
                alpha = re.search(
                    r'^(?P<num_text>\(\d+\)\s*\((?P<alpha1>[a-z]+)\)\s*.+\s*)(?P<alpha_text>\((?P<alpha2>[a-z])\).+)',
                    current_p_tag)
                if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                          p_tag.find_next_sibling().text.strip()).group("alpha3")
                    if ord(alpha.group("alpha2")) == (ord(alpha.group("alpha1"))) + 1:
                        if ord(nxt_alpha) == (ord(alpha.group("alpha2"))) + 1:
                            alpha_text = alpha.group("alpha_text")
                            num_text = alpha.group("num_text")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

            if re.search(r'^\(\d+\)\s*(to|and)\s*\(\d+\)\s*', current_p_tag):
                nxt_tag = p_tag.find_next_sibling(
                    lambda tag: tag.name in ['p'] and re.search(r'^[^\s]', tag.text.strip()))
                alpha = re.search(
                    r'^(?P<text1>\((?P<num1>\d+)\))\s*(to|and)\s*(?P<text2>\((?P<num2>\d+)\)\s*(?P<rpt_text>.+))',
                    current_p_tag)
                if re.search(r'^\(\d+\)', nxt_tag.text.strip()):
                    nxt_alpha = re.search(r'^\((?P<num3>\d+)\)', nxt_tag.text.strip()).group(
                        "num3")
                    if int(nxt_alpha) != int(alpha.group("num1")) + 1:
                        if int(alpha.group("num2")) == int(alpha.group("num1")) + 1:
                            if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                alpha_text = alpha.group("text2")
                                num_text = alpha.group("text1")
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = alpha_text
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag.string = num_text
                        else:
                            if int(nxt_alpha) == int(alpha.group("num2")) + 1:
                                alpha_text = alpha.group("text2")
                                num_text = alpha.group("text1") + alpha.group("rpt_text")
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = alpha_text
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag.string = num_text
                                range_from = int(alpha.group("num1"))
                                range_to = int(alpha.group("num2"))
                                count = range_from + 1
                                for new_p_tag in range(range_from + 1, range_to):
                                    new_p_tag = self.soup.new_tag("p")
                                    new_p_tag.string = f'({count}){alpha.group("rpt_text")}'
                                    new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                    p_tag.insert_after(new_p_tag)
                                    p_tag = new_p_tag
                                    count += 1

            if re.search(r'^\([a-zA-Z]\)\s*(to|and)\s*\([a-zA-Z]\)\s*(Repealed.|\()', current_p_tag):
                alpha = re.search(
                    r'^(?P<text1>\((?P<num1>[a-zA-Z])\))\s*(to|and)\s*(?P<text2>\((?P<num2>[a-zA-Z])\)\s*(?P<rpt_text>Repealed.|\(.+))',
                    current_p_tag)
                if re.match(r'^\([a-zA-Z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<num3>[a-zA-Z])\)',
                                          p_tag.find_next_sibling().text.strip()).group(
                        "num3")
                    if ord(alpha.group("num2")) == ord(alpha.group("num1")) + 1:
                        if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

                    else:
                        if ord(nxt_alpha) == ord(alpha.group("num2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1") + alpha.group("rpt_text")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text
                            range_from = ord(alpha.group("num1"))
                            range_to = ord(alpha.group("num2"))
                            count = range_from + 1
                            for new_p_tag in range(range_from + 1, range_to):
                                new_p_tag = self.soup.new_tag("p")
                                new_p_tag.string = f'({chr(count)}){alpha.group("rpt_text")}'
                                new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                                p_tag.insert_after(new_p_tag)
                                p_tag = new_p_tag
                                count += 1

                else:
                    alpha_text = alpha.group("text2")
                    num_text = alpha.group("text1")
                    new_p_tag = self.soup.new_tag("p")
                    new_p_tag.string = alpha_text
                    new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                    p_tag.insert_after(new_p_tag)
                    p_tag.string = num_text
                    range_from = ord(alpha.group("num1"))
                    range_to = ord(alpha.group("num2"))
                    count = range_from + 1
                    for new_p_tag in range(range_from + 1, range_to):
                        new_p_tag = self.soup.new_tag("p")
                        new_p_tag.string = f'({chr(count)})'
                        new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                        p_tag.insert_after(new_p_tag)
                        p_tag = new_p_tag
                        count += 1

            if re.search(r'^\([a-z]\).+\([a-z]\)\s*', current_p_tag):
                alpha = re.search(r'^(?P<text1>\((?P<alpha1>[a-z])\).+)(?P<text2>\((?P<alpha2>[a-z])\)\s*.+)',
                                  current_p_tag)
                if re.match(r'^\([a-z]\)', p_tag.find_next_sibling().text.strip()):
                    nxt_alpha = re.search(r'^\((?P<alpha3>[a-z])\)',
                                          p_tag.find_next_sibling().text.strip()).group(
                        "alpha3")
                    if ord(alpha.group("alpha2")) == ord(alpha.group("alpha1")) + 1:
                        if ord(nxt_alpha) == ord(alpha.group("alpha2")) + 1:
                            alpha_text = alpha.group("text2")
                            num_text = alpha.group("text1")
                            new_p_tag = self.soup.new_tag("p")
                            new_p_tag.string = alpha_text
                            new_p_tag["class"] = [self.tag_type_dict['ol_p']]
                            p_tag.insert_after(new_p_tag)
                            p_tag.string = num_text

        main_sec_alpha = 'a'
        sec_alpha = 'a'
        cap_alpha = 'A'
        inr_cap_alpha = 'A'
        cap_roman = 'I'
        small_roman = 'i'

        ol_head = 1
        num_count = 1
        roman_count = 1
        ol_count = 1

        alpha_ol = self.soup.new_tag("ol", type="a")
        cap_alpha_ol = self.soup.new_tag("ol", type="A")
        roman_ol = self.soup.new_tag("ol", type="I")
        num_ol = self.soup.new_tag("ol")

        ol_list = []
        dup_id_list = []
        innr_roman_ol = None
        sec_alpha_cur_tag = None
        num_tag = None
        inr_cap_alpha_cur_tag = None
        alpha_cur_tag = None
        prev_alpha_id = None
        prev_head_id = None
        article_alpha_tag = None
        previous_li_tag = None
        num_cur_tag = None

        for p_tag in self.soup.body.find_all(['h3', 'h4', 'h5', 'p']):
            if p_tag.b:
                p_tag.b.unwrap()
            current_tag_text = p_tag.text.strip()

            if re.search(rf'^\({ol_head}\)|^\[.+\]\s*\({ol_head}\)|^\(\d+\.\d+\)', current_tag_text):
                previous_li_tag = p_tag
                if re.search(rf'^\({ol_head}\)|^\[.+\]\s*\({ol_head}\) ', current_tag_text):
                    p_tag.name = "li"
                    num_cur_tag = p_tag

                    if re.search(r'^\(1\)|^\[.+\]\s*\(1\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        p_tag.wrap(num_ol)

                        if article_alpha_tag:
                            alpha_cur_tag.append(num_ol)
                            prev_head_id = alpha_cur_tag.get("id")

                        else:
                            prev_head_id = p_tag.find_previous(["h4", "h3", "h2", "h1"]).get("id")
                            main_sec_alpha = 'a'

                    else:
                        num_ol.append(p_tag)

                    if inr_cap_alpha_cur_tag:
                        p_tag["id"] = f'{inr_cap_alpha_cur_tag.get("id")}{ol_head}'
                    elif article_alpha_tag:
                        p_tag["id"] = f'{alpha_cur_tag.get("id")}{ol_head}'
                    else:
                        prev_num_id = f'{prev_head_id}ol{ol_count}{ol_head}'
                        p_tag["id"] = f'{prev_head_id}ol{ol_count}{ol_head}'
                        main_sec_alpha = 'a'

                    p_tag.string = re.sub(rf'^\({ol_head}\)', '', current_tag_text)
                    ol_head += 1

                    if re.search(r'^\(\d+\)\s\(a\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s\(a\)', '', current_tag_text)

                        alpha_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>a)\)', current_tag_text)
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(alpha_ol)
                        main_sec_alpha = "b"

                        if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="I")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            rom_cur_tag = li_tag
                            cur_tag = re.search(r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[IVX]+)\)',
                                                current_tag_text)
                            prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            roman_ol.append(inner_li_tag)
                            alpha_cur_tag.string = ""
                            alpha_cur_tag.insert(0, roman_ol)
                            cap_roman = "II"

                            if re.search(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                                cap_alpha_ol = self.soup.new_tag("ol", type="A")
                                inner_li_tag = self.soup.new_tag("li")
                                inner_li_tag.string = re.sub(r'^\(\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '',
                                                             current_tag_text)
                                # inner_li_tag.append(current_tag_text)
                                li_tag["class"] = self.tag_type_dict['ol_p']
                                cur_tag = re.search(
                                    r'^\((?P<id1>\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                    current_tag_text)
                                prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                                inner_li_tag[
                                    "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'
                                cap_alpha_ol.append(inner_li_tag)
                                rom_cur_tag.string = ""
                                rom_cur_tag.append(cap_alpha_ol)
                                cap_alpha = "B"

                    if re.search(r'^\(\d+\)\s\(i\)', current_tag_text):
                        innr_roman_ol = self.soup.new_tag("ol", type="i")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\d+\)\s\(i\)', '', current_tag_text)
                        prev_alpha = p_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+)\)\s\((?P<pid>i)\)', current_tag_text)
                        prev_num_id = f'{prev_head_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        innr_roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(innr_roman_ol)
                elif re.search(r'^\(\d+\.\d+\)', current_tag_text):
                    cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\)', current_tag_text).group("cid")
                    tag_id = f'{prev_num_id}-{cur_tag}'
                    if tag_id in dup_id_list:
                        p_tag["id"] = f'{prev_num_id}-{cur_tag}.1'
                    else:
                        p_tag["id"] = f'{prev_num_id}-{cur_tag}'

                    dup_id_list.append(tag_id)

                    if not re.search(r'^\(\d+\.\d+\)', p_tag.find_next().text.strip()):
                        prev_num_id = f'{prev_num_id}-{cur_tag}'
                        p_tag.name = "div"
                    p_tag.find_previous("li").append(p_tag)
                    main_sec_alpha = "a"
                    num_cur_tag = p_tag

                    if re.search(r'^\(\d+\.\d+\)\s\(\w\)|^\(\d+\.\d+\)\s*\[.+\]\s*\(\w\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        li_tag = self.soup.new_tag("li")
                        li_tag.append(current_tag_text)
                        alpha_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\d+\.\d+)\).+\((?P<pid>\w)\)', current_tag_text)
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        if prev_alpha_id in dup_id_list:
                            li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}.1'
                        else:
                            li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        alpha_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(alpha_ol)
                        main_sec_alpha = "b"
                        cap_roman = "I"
                        dup_id_list.append(prev_alpha_id)
                        if re.search(r'^\(\d+\.\d+\)\s*\(\w\)\s*\([I,V,X]+\)\s*', current_tag_text):
                            roman_ol = self.soup.new_tag("ol", type="I")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            rom_cur_tag = li_tag
                            cur_tag = re.search(r'^\((?P<id1>\d+\.\d+)\)\s*\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)',
                                                current_tag_text)
                            prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("id1")}{cur_tag.group("cid")}{cur_tag.group("id2")}'
                            roman_ol.append(inner_li_tag)
                            p_tag.insert(1, roman_ol)
                            roman_ol.find_previous().string.replace_with(roman_ol)
                            cap_roman = "II"

            elif re.search(rf'^\({main_sec_alpha}\)|^\(\w+\.\d+\)', current_tag_text):
                previous_li_tag = p_tag
                if re.search(rf'^\({main_sec_alpha}\)', current_tag_text):
                    p_tag.name = "li"
                    alpha_cur_tag = p_tag
                    if re.search(r'^\(a\)', current_tag_text):
                        alpha_ol = self.soup.new_tag("ol", type="a")
                        p_tag.wrap(alpha_ol)

                        if p_tag.find_previous("h4") and re.search(r'^(ARTICLE|Article) [IVX]+',
                                                                   p_tag.find_previous("h4").text.strip()):
                            if num_tag:
                                num_tag.append(alpha_ol)
                                prev_alpha_id = f'{num_tag.get("id")}'
                            else:
                                prev_alpha_id = f'{p_tag.find_previous("h4").get("id")}ol{ol_count}'
                                article_alpha_tag = p_tag
                        elif num_cur_tag:
                            article_alpha_tag = None
                            num_cur_tag.append(alpha_ol)
                            prev_alpha_id = f'{prev_num_id}'
                        else:
                            article_alpha_tag = p_tag
                            prev_alpha_id = f'{p_tag.find_previous(["h4", "h3", "h2", "h1"]).get("id")}ol{ol_count}'

                    else:
                        alpha_ol.append(p_tag)

                    if p_tag.find_previous("h4") and re.search(r'^(ARTICLE|Article) [IVX]+',
                                                               p_tag.find_previous("h4").text.strip()):
                        ol_head = 1

                    p_tag["id"] = f'{prev_alpha_id}{main_sec_alpha}'
                    p_tag.string = re.sub(rf'^\({main_sec_alpha}\)', '', current_tag_text)
                    main_sec_alpha = chr(ord(main_sec_alpha) + 1)

                    if re.search(r'^\(\w\)(\s*\[.+\])*\s*\([I,V,X]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)', '', current_tag_text)

                        li_tag["class"] = self.tag_type_dict['ol_p']
                        rom_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w+)\)(\s*\[.+\])*\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                        prev_alpha_id = f'{prev_num_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(roman_ol)
                        cap_roman = "II"

                        if re.search(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.string = re.sub(r'^\(\w\)\s*\([I,V,X]+\)\s*\(\w\)', '', current_tag_text)
                            inner_li_tag.append(current_tag_text)
                            li_tag["class"] = self.tag_type_dict['ol_p']
                            cur_tag = re.search(
                                r'^\((?P<cid>\w)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                current_tag_text)
                            prev_id = rom_cur_tag.get("id")
                            inner_li_tag[
                                "id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("id3")}'
                            cap_alpha_ol.append(inner_li_tag)
                            p_tag.insert(1, cap_alpha_ol)
                            rom_cur_tag.string = ""
                            rom_cur_tag.string.replace_with(cap_alpha_ol)
                            cap_alpha = "B"

                    if re.search(r'^\(\w\)\s*\(\d+\)', current_tag_text):
                        num_ol = self.soup.new_tag("ol")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\)\s*\(\d+\)', '', current_tag_text)

                        li_tag["class"] = self.tag_type_dict['ol_p']
                        new_num = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w+)\)\s*\((?P<pid>\d+)\)', current_tag_text)
                        prev_rom_id = f'{prev_num_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                        num_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(num_ol)
                        ol_head = 2
                        cap_alpha = "A"
                        new_num = None

                    if re.search(r'^\(\w\)\s*\([ivx]+\)', current_tag_text):
                        innr_roman_ol = self.soup.new_tag("ol", type="i")
                        inner_li_tag = self.soup.new_tag("li")
                        inner_li_tag.string = re.sub(r'^\(\w\)\s*\([ivx]+\)', '', current_tag_text)

                        inner_li_tag["class"] = self.tag_type_dict['ol_p']
                        prev_alpha = inner_li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w)\)\s*\((?P<pid>[ivx]+)\)', current_tag_text)
                        prev_rom_id = f'{alpha_cur_tag.get("id")}'
                        inner_li_tag["id"] = f'{alpha_cur_tag.get("id")}{cur_tag.group("pid")}'
                        innr_roman_ol.append(inner_li_tag)
                        p_tag.contents = []
                        p_tag.append(innr_roman_ol)
                elif re.search(r'^\(\w+\.\d+\)', current_tag_text):
                    p_tag.name = "li"
                    roman_count = 1
                    cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)', current_tag_text).group("cid")
                    p_tag.string = re.sub(r'^\(\w+\.\d+\)', '', current_tag_text)
                    p_tag_id = f'{prev_alpha_id}-{cur_tag}'
                    if p_tag_id in dup_id_list:
                        p_tag["id"] = f'{prev_alpha_id}-{cur_tag}.1'
                    else:
                        p_tag["id"] = f'{prev_alpha_id}-{cur_tag}'

                    dup_id_list.append(p_tag_id)
                    prev_alpha_id = f'{prev_alpha_id}'

                    if not re.search(r'^\(\w+\.\d+\)', p_tag.find_next().text.strip()) and re.search(r'^\([A-Z]\)',
                                                                                                     p_tag.find_next().text.strip()):
                        prev_alpha_id = f'{prev_alpha_id}-{cur_tag}'

                    alpha_ol.append(p_tag)
                    alpha_cur_tag = p_tag

                    if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)', current_tag_text):
                        roman_ol = self.soup.new_tag("ol", type="I")
                        li_tag = self.soup.new_tag("li")
                        li_tag.string = re.sub(r'^\(\w\.\d+\)\s*\([I,V,X]+\)', '', current_tag_text)

                        li_tag["class"] = self.tag_type_dict['ol_p']
                        rom_cur_tag = li_tag
                        cur_tag = re.search(r'^\((?P<cid>\w+\.\d+)\)\s*\((?P<pid>[I,V,X]+)\)', current_tag_text)
                        prev_rom_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        prev_alpha_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                        roman_ol.append(li_tag)
                        p_tag.contents = []
                        p_tag.append(roman_ol)
                        cap_roman = "II"

                        if re.search(r'^\(\w\.\d+\)\s*\([I,V,X]+\)\s*\(\w\)', current_tag_text):
                            cap_alpha_ol = self.soup.new_tag("ol", type="A")
                            inner_li_tag = self.soup.new_tag("li")
                            inner_li_tag.append(current_tag_text)
                            inner_li_tag["class"] = self.tag_type_dict['ol_p']
                            cur_tag = re.search(
                                r'^\((?P<cid>\w\.\d+)\)\s*\((?P<id2>[I,V,X]+)\)\s*\((?P<id3>\w)\)',
                                current_tag_text)
                            prev_id = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}'

                            inner_li_tag[
                                "id"] = f'{prev_head_id}ol{ol_count}{cur_tag.group("cid")}{cur_tag.group("id2")}{cur_tag.group("id3")}'

                            cap_alpha_ol.append(inner_li_tag)
                            p_tag.insert(1, cap_alpha_ol)
                            cap_alpha_ol.find_previous().string.replace_with(cap_alpha_ol)
                            cap_alpha = "B"

            elif re.search(rf'^\({cap_roman}\)', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                rom_cur_tag = p_tag
                cap_alpha = "A"
                if re.search(r'^\(I\)', current_tag_text):
                    roman_ol = self.soup.new_tag("ol", type="I")
                    p_tag.wrap(roman_ol)
                    if alpha_cur_tag:
                        alpha_cur_tag.append(roman_ol)
                        p_tag["id"] = f'{prev_alpha_id}I'
                    else:
                        p_tag["id"] = f'{p_tag.find_previous("li").get("id")}I'
                        p_tag.find_previous("li").append(roman_ol)
                else:
                    roman_ol.append(p_tag)
                    prev_rom_id = f'{prev_alpha_id}{cap_roman}'
                    p_tag["id"] = f'{prev_alpha_id}{cap_roman}'

                p_tag.string = re.sub(rf'^\({cap_roman}\)', '', current_tag_text)
                cap_roman = roman.toRoman(roman.fromRoman(cap_roman.upper()) + 1)

                if re.search(r'^\([I,V,X]+\)\s*\([A-Z]\)', current_tag_text):
                    cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^\([I,V,X]+\)\s*\(A\)', '', current_tag_text)
                    cap_alpha_cur_tag = li_tag
                    cur_tag = re.search(r'^\((?P<cid>[I,V,X]+)\)\s*\((?P<pid>[A-Z])\)', current_tag_text)
                    prev_id = f'{rom_cur_tag.get("id")}'
                    li_tag["id"] = f'{rom_cur_tag.get("id")}{cur_tag.group("pid")}'

                    if not re.search(r'^\(I\)', current_tag_text):
                        prev_tag_id = p_tag.find_previous("li").get("id")
                        cur_tag_id = re.search(r'^[^IVX]+', prev_tag_id).group()
                        prev_rom_id = f'{cur_tag_id}{cur_tag.group("cid")}'
                        li_tag["id"] = f'{cur_tag_id}{cur_tag.group("cid")}{cur_tag.group("pid")}'
                    cap_alpha_ol.append(li_tag)
                    p_tag.string = ""
                    p_tag.append(cap_alpha_ol)
                    roman_count += 1
                    cap_alpha = "B"

            elif re.search(rf'^\({cap_alpha}\)', current_tag_text):
                previous_li_tag = p_tag
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

                if cap_alpha in ['I', 'V', 'X', 'L']:
                    p_tag["id"] = f'{prev_id}{ord(cap_alpha)}'
                else:
                    p_tag["id"] = f'{prev_id}{cap_alpha}'

                # p_tag["id"] = f'{prev_id}{cap_alpha}'
                p_tag.string = re.sub(rf'^\({cap_alpha}\)', '', current_tag_text)
                if cap_alpha == 'Z':
                    cap_alpha = 'A'
                else:
                    cap_alpha = chr(ord(cap_alpha) + 1)

            elif re.search(r'^\([ivx]+\)', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                rom_cur_tag = p_tag
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
                        alpha_cur_tag = p_tag
                        p_tag["id"] = f'{prev_num_id}{cur_tag}'
                p_tag.string = re.sub(r'^\((?P<cid>[ivx]+)\)', '', current_tag_text)

            elif re.search(rf'^{sec_alpha}\.', current_tag_text):
                previous_li_tag = p_tag
                p_tag.name = "li"
                sec_alpha_cur_tag = p_tag

                if re.search(r'^a\.', current_tag_text):
                    sec_alpha_ol = self.soup.new_tag("ol", type="a")
                    p_tag.wrap(sec_alpha_ol)
                    if num_tag:
                        num_tag.append(sec_alpha_ol)
                        sec_alpha_id = num_tag.get("id")

                    else:
                        sec_alpha_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count}{sec_alpha}'
                        num_count = 1

                else:
                    sec_alpha_ol.append(p_tag)
                    if not num_tag:
                        num_count = 1

                p_tag["id"] = f'{sec_alpha_id}{sec_alpha}'
                p_tag.string = re.sub(rf'^{sec_alpha}\.', '', current_tag_text)
                sec_alpha = chr(ord(sec_alpha) + 1)

            elif re.search(rf'^{inr_cap_alpha}\.', current_tag_text) and p_tag.name == "p":
                previous_li_tag = p_tag
                p_tag.name = "li"
                inr_cap_alpha_cur_tag = p_tag
                num_count = 1
                ol_head = 1

                if re.search(r'^A\.', current_tag_text):
                    inr_cap_alpha_ol = self.soup.new_tag("ol", type="A")
                    p_tag.wrap(inr_cap_alpha_ol)
                    prev_id = f'{p_tag.find_previous({"h4", "h3", "h2"}).get("id")}ol{ol_count + 1}'

                else:
                    inr_cap_alpha_ol.append(p_tag)

                p_tag["id"] = f'{prev_id}{inr_cap_alpha}'
                p_tag.string = re.sub(rf'^{inr_cap_alpha}\.', '', current_tag_text)
                inr_cap_alpha = chr(ord(inr_cap_alpha) + 1)

                if re.search(r'^[A-Z]\.\s\(1\)', current_tag_text):
                    num_ol = self.soup.new_tag("ol")
                    li_tag = self.soup.new_tag("li")
                    li_tag.string = re.sub(r'^[A-Z]\.\s\(1\)', '', current_tag_text)
                    li_tag["class"] = self.tag_type_dict['ol_p']
                    inner_alpha_id = f'{inr_cap_alpha_cur_tag.get("id")}'
                    li_tag["id"] = f'{inr_cap_alpha_cur_tag.get("id")}1'
                    num_ol.append(li_tag)
                    p_tag.contents = []
                    p_tag.append(num_ol)
                    ol_head = 2

            elif re.search(r'^\([a-z]{2,3}\)', current_tag_text) and p_tag.name != "li":
                previous_li_tag = p_tag
                curr_id = re.search(r'^\((?P<cur_id>[a-z]+)\)', current_tag_text).group("cur_id")
                p_tag.name = "li"
                alpha_cur_tag = p_tag
                alpha_ol.append(p_tag)
                prev_alpha_id = f'{prev_num_id}{curr_id}'
                p_tag["id"] = f'{prev_num_id}{curr_id}'
                roman_count = 1
                p_tag.string = re.sub(r'^\([a-z]{2,3}\)', '', current_tag_text)

            elif p_tag.get("class") == [self.tag_type_dict['ol_p']]:
                if previous_li_tag:
                    previous_li_tag.append(p_tag)

            if re.search(r'^Source|^Cross references:|^OFFICIAL COMMENT|^(ARTICLE|Article) [IVX]+',
                         current_tag_text, re.I) or p_tag.name in ['h3']:
                main_sec_alpha = 'a'
                sec_alpha = 'a'
                cap_alpha = 'A'
                inr_cap_alpha = 'A'
                cap_roman = 'I'
                ol_head = 1
                roman_count = 1
                ol_count = 1
                innr_roman_ol = None
                num_tag = None
                inr_cap_alpha_cur_tag = None
                alpha_cur_tag = None
                prev_alpha_id = None
                article_alpha_tag = None
                previous_li_tag = None
                num_cur_tag = None

        logger.info("ol tags added")

    def create_analysis_nav_tag(self):
        super(COParseHtml, self).create_annotation_analysis_nav_tag()
        logger.info("Annotation analysis nav created")

    def wrap_inside_main_tag(self):

        """wrap inside main tag"""

        main_tag = self.soup.new_tag('main')
        chap_nav = self.soup.find('nav')

        h2_tag = self.soup.find("h2")
        tag_to_wrap = h2_tag.find_previous_sibling()

        for tag in tag_to_wrap.find_next_siblings():
            tag.wrap(main_tag)

        for nav_tag in chap_nav.find_next_siblings():
            if nav_tag.name != "main":
                nav_tag.wrap(chap_nav)

    def replace_tags_constitution(self):
        for p_tag in self.soup.find_all(class_=self.tag_type_dict['head3']):
            current_p_tag = p_tag.text.strip()
            next_sibling = p_tag.find_next_sibling()
            if re.search('^§', current_p_tag):
                if p_tag.b and re.search('^§', p_tag.b.text.strip()):
                    new_h3_tag = self.soup.new_tag("p")
                    new_h3_tag["class"] = self.tag_type_dict['head3']
                    h3_text = p_tag.b.text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()
                else:
                    new_h3_tag = self.soup.new_tag("p")
                    new_h3_tag["class"] = self.tag_type_dict['head3']
                    h3_text = "§ " + p_tag.find_next("b").text
                    new_h3_tag.string = h3_text
                    p_tag.insert_before(new_h3_tag)
                    if not re.search(r'^Constitution of the State of Colorado', p_tag.find_next("b").text.strip()):
                        p_tag.find_next("b").decompose()
                    if re.search(r'^§', p_tag.text.strip()):
                        p_tag.string = re.sub(r'^§', '', p_tag.text.strip())

        super(COParseHtml, self).replace_tags_constitution()
        for header_tag in self.soup.find_all("p"):
            if header_tag.get("class") == [self.tag_type_dict["head2"]] or \
                    header_tag.get("class") == [self.tag_type_dict["amd"]]:
                if re.search(r'^PREAMBLE|^AMENDMENTS|^Schedule', header_tag.text.strip(), re.I):
                    header_tag.name = "h2"
                    tag_text = re.sub(r'[\W\s]+', '', header_tag.text.strip()).lower()
                    header_tag["id"] = f"{header_tag.find_previous('h1').get('id')}-{tag_text}"
                    header_tag["class"] = "gen"
            elif header_tag.get("class") == [self.tag_type_dict["art_head"]]:
                if self.regex_pattern_obj.h2_article_pattern_con.search(header_tag.text.strip()):
                    header_tag.name = "h3"
                    chap_no = self.regex_pattern_obj.h2_article_pattern_con.search(header_tag.text.strip()).group('id')
                    header_tag["id"] = f'{header_tag.find_previous("h2").get("id")}-am{chap_no.zfill(2)}'
                    header_tag["class"] = "amend"
                    self.ul_tag = self.soup.new_tag("ul", **{"class": "leaders"})
            elif header_tag.get("class") == [self.tag_type_dict["section"]]:
                if re.search(r'^Section \d+(\w)*\.', header_tag.text.strip()):
                    chap_num = re.search(r'^Section (?P<id>\d+(\w)*)\.', header_tag.text.strip()).group("id")
                    header_tag.name = "h3"
                    header_tag["id"] = f"{header_tag.find_previous('h2').get('id')}-sec{chap_num.zfill(2)}"
                    header_tag["class"] = "sec"

    def add_anchor_tags_con(self):
        super(COParseHtml, self).add_anchor_tags_con()
        for li in self.soup.find_all("li"):
            if not li.get("id"):
                if re.search(r'^[IVX]+', li.text.strip()):
                    chap_num = re.search(r'^(?P<id>[IVX]+) ', li.text.strip()).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li, chap_num,
                                                sub_tag="-ar",
                                                prev_id=li.find_previous("h1").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')

                elif re.search(r'^Section \d+(\w)*\.', li.text.strip()):
                    chap_num = re.search(r'^Section (?P<id>\d+(\w)*)\.', li.text.strip()).group("id")
                    self.c_nav_count += 1
                    self.set_chapter_section_id(li, chap_num.zfill(2),
                                                sub_tag="-sec",
                                                prev_id=li.find_previous("h2").get("id"),
                                                cnav=f'cnav{self.c_nav_count:02}')
