import re


class RegexPatterns:
    """ BASE PATTERNS"""
    h1_pattern = re.compile(r'title (?P<id>\d+(\.\d+)*)', re.I)
    h2_chapter_pattern = re.compile(r'^chapter\s(?P<id>\d+([a-zA-Z])*)', re.I)
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+([a-zA-Z])*)', re.I)
    h2_part_pattern = re.compile(r'^part\s(?P<id>(\d+([a-zA-Z])*)|([IVX]+)*)', re.I)
    h2_subtitle_pattern = re.compile(r'^Subtitle\s*(?P<id>\d+)', re.I)
    section_pattern_con1 = re.compile(r'^Section (?P<id>\d+)')
    amend_pattern_con = re.compile(r'^AMENDMENT (?P<id>\d+)', re.I)
    amp_pattern = re.compile(r'&(?!amp;)')
    br_pattern = re.compile(r'<br/>')
    cite_pattern = None
    code_pattern = None
    h1_pattern_con = None
    h2_article_pattern_con = None
    section_pattern_con = None
    article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+(\w)?)')


class CustomisedRegexGa(RegexPatterns):
    """ Customised regex patterns for GA code"""

    section_pattern = re.compile(r'^(?P<id>\d+-\d+([a-z])?-\d+(\.\d+)?)', re.I)
    ul_pattern = re.compile(r'^(?P<id>\d+([A-Z])?)', re.I)
    rule_pattern = re.compile(r'^Rule (?P<id>\d+(-\d+-\.\d+)*(\s\(\d+\))*)\.', re.I)


class CustomisedRegexVA(RegexPatterns):
    """ Customised regex patterns for VA code"""

    h2_subtitle_pattern = re.compile(r'^subtitle\s(?P<id>[IVX]+([a-zA-Z])*)', re.I)
    h2_part_pattern = re.compile(r'^part\s(?P<id>([A-Z]))', re.I)
    h2_chapter_pattern = re.compile(r'^chapter\s(?P<id>\d+(\.\d+(:1\.)*?)*)', re.I)
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+((\.\d+)*?[a-zA-Z])*)', re.I)

    section_pattern = re.compile(
        r'^§+\s(?P<id>\d+(\.\d+)*[A-Z]*-\d+(\.\d+)*(:\d+)*(\.\d+)*(\.\d+)*)\.*\s*', re.I)

    cite_pattern = re.compile(
        r'(?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*(\.\s:\d+)*(?P<ol>(\([a-z]\))(\(\d+\))*)*)')
    code_pattern = re.compile(r'(\d+\sVa.\s\d+|S\.E\. \d+|Va\. App\. LEXIS \d+|Titles (\d+(\.\d+)*))')


class CustomisedRegexAK(RegexPatterns):
    """ Customised regex patterns for AK code"""

    section_pattern = re.compile(r'^Sec\.\s*?(?P<id>\d+\.\d+\.\d+)\.')
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)\.\d+\.\d+)(?P<ol>(\([a-z]\))(\(\d+\))*(\(\w+\))*)*)')
    code_pattern = re.compile(r'\d+ AAC \d+, art\. \d+\.|State v\. Yi, \d+ P\.\d+d \d+')

    h1_pattern_con = re.compile(r'The Constitution of the State')
    h2_article_pattern_con = re.compile(r'^Article (?P<id>[IVX]+)', re.I)
    section_pattern_con = re.compile(r'^Section (?P<id>\d+)\.')

    cite_tag_pattern = re.compile(r'AS\s\d+\.\d+\.\d+((\([a-z]\))(\(\d+\))*(\(\w+\))*)*|'
                                  r'\d+ AAC \d+, art\. \d+\.|State v\. Yi, \d+ P\.\d+d \d+')


class CustomisedRegexCO(RegexPatterns):
    """ Customised regex patterns for CO code"""

    h2_article_pattern = re.compile(r'^(article|Art\.)\s(?P<id>\d+(\.\d+)*)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*?)', re.I)
    h2_subpart_pattern = re.compile(r'^subpart\s(?P<id>\d+([a-zA-Z])*)', re.I)

    cite_pattern = re.compile(
        r'((?P<cite>(?P<title>\d+)(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)\s?(?P<ol>(\(\w\))(\(\w\))?(\(\w\))?)*)')
    code_pattern = re.compile(r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                              r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                              r"\d{4}\s*COA\s*\d+|"
                              r"L\.\s*\d+,\s*p\.\s*\d+|"
                              r"Colo\.+P\.\d\w\s\d+")

    h1_pattern_con = re.compile(r'^Declaration of Independence|'
                                r'^Constitution of the United States of America of 1787|'
                                r'^Constitution of the State of Colorado')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+)', re.I)
    section_pattern_con = re.compile(r'^§ (?P<id>\d+)\.')

    cite_tag_pattern = re.compile(r"\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*"
                                  r"Colo\.\s*\d+|Colo\.\s*Law\.\s*\d+|"
                                  r"\d+\s*Denv\.\s*L\.\s*Rev\.\s*\d+|"
                                  r"\d{4}\s*COA\s*\d+|"
                                  r"L\.\s*\d+,\s*p\.\s*\d+|"
                                  r"Colo.+P\.\d\w\s\d+")


class CustomisedRegexVT(RegexPatterns):
    """ Customised regex patterns for VT code"""
    h2_chapter_pattern = re.compile(r'^chapter\s*(?P<id>([IVX]+|\d+([A-Z])*))', re.I)
    h2_article_pattern = re.compile(r'^article\s*(?P<id>([IVX]+|\d+([a-zA-Z])*))', re.I)
    section_pattern = re.compile(
        r'^§*\s*(?P<id>\d+([a-z]{0,2})*([A-Z])*(\.\d+)*(\.*?\s*?-\d+([a-z])*)*(\.\d+)*)\.*\s*')
    h2_subchapter_pattern = re.compile(r'^Subchapter (?P<id>\d+([A-Z]+)?)', re.I)

    h1_pattern_con = re.compile(r'^Constitution of the United States|'
                                r'^CONSTITUTION OF THE STATE OF VERMONT', re.I)
    h2_chapter_pattern_con = re.compile(r'^chapter\s*(?P<id>[IVX]+)', re.I)
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+)\.*', re.I)
    section_pattern_con = re.compile(r'^(Article|§)\s*(?P<id>\d+(-[A-Z])*)\.')
    h2_amendment_pattern_con = re.compile(r'^AMENDMENT (?P<id>[IVX]+)\.*', re.I)

    cite_pattern = re.compile(r'\b((?P<cite>(?P<title>\d{1,2})-(?P<chap>\d(\w+)?)-(?P<sec>\d+(\.\d+)?))(\s?(\(('
                              r'?P<ol>\w+)\))+)?)')

    code_pattern = re.compile(r"\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*"
                              r"|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*"
                              r"|\d+,\sNo\.\s\d+")

    cite_tag_pattern = re.compile(r"\d+\sV\.S\.A\.\s§+\s\d+(-\d+)*([a-z]+)*(\([a-z]\))*(\(\d+\))*(\([A-Z]\))*"
                                  r"|\d+\sU\.S\.C\.\s§\s\d+\(*[a-z]\)*"
                                  r"|\d+,\sNo\.\s\d+")


class CustomisedRegexAR(RegexPatterns):
    """ Customised regex patterns for AR code"""

    section_pattern = re.compile(r'^(?P<id>(\d+-\d+([a-zA-Z])?-\d+(\.\d+)?)|\d\. Acts)')
    h2_subtitle_pattern = re.compile(r'^Subtitle (?P<id>\d+)\.')
    h2_chapters_pattern = re.compile(r'^Chapters (?P<id>\d+-\d+)')
    h2_subchapter_pattern = re.compile(r'^Subchapter (?P<id>\d+)')

    h1_pattern_con = re.compile(r'^Constitution\s+Of\s+The', re.I)
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+)', re.I)
    section_pattern_con = re.compile(r'^\[*§+\s*(?P<id>\d+)')
    amend_pattern_con = re.compile(r'^AMENDMENT (?P<id>\d+)', re.I)

    cite_pattern = re.compile(r'\b((?P<cite>(?P<title>\d{1,2})-(?P<chap>\d(\w+)?)-(?P<sec>\d+(\.\d+)?))(\s?(\(('
                              r'?P<ol>\w+)\))+)?)')
    code_pattern = re.compile(r"(\d+ Ga\.( App\.)? \d+"
                              r"|\d+ S\.E\.(2d)? \d+"
                              r"|\d+ U\.S\.C\. § \d+(\(\w\))?"
                              r"|\d+ S\. (Ct\.) \d+"
                              r"|\d+ L\. (Ed\.) \d+"
                              r"|\d+ L\.R\.(A\.)? \d+"
                              r"|\d+ Am\. St\.( R\.)? \d+"
                              r"|\d+ A\.L\.(R\.)? \d+)")

    cite_tag_pattern = re.compile(r"§+\s(\W+)?\d+-\w+-\d+(\.\d+)?"
                                  r"|\d+ Ga\.( App\.)? \d+"
                                  r"|\d+ S\.E\.(2d)? \d+"
                                  r"|\d+ U\.S\.C\. § \d+(\(\w\))?"
                                  r"|\d+ S\. (Ct\.) \d+"
                                  r"|\d+ L\. (Ed\.) \d+"
                                  r"|\d+ L\.R\.(A\.)? \d+"
                                  r"|\d+ Am\. St\.( R\.)? \d+"
                                  r"|\d+ A\.L\.(R\.)? \d+")


class CustomisedRegexND(RegexPatterns):
    """ Customised regex patterns for ND code"""

    h2_part_pattern = re.compile(r'^Part\s(?P<id>([IVX]+)*(\d+([a-zA-Z])*)*)')
    h2_chapter_pattern = re.compile(r'^CHAPTER\s(?P<id>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*)')
    h2_article_pattern = re.compile(r'^article\s(?P<id>(\d+([a-zA-Z])*)|[IVX]+)', re.I)

    cite_pattern = re.compile(
        r'((?P<cite>(?P<title>\d+(\.\d+)*)-\d+(\.\d+)*-\d+(\.\d+)*)(?P<ol>(\(\w\))(\(\w\))?(\(\w\))?)*)')
    code_pattern = re.compile(r'N\.D\. LEXIS \d+')

    cite_tag_pattern = re.compile(r"\d+(\.\d+)*-\d+(\.\d+)*-\d+(\.\d+)*"
                                  r"|Chapter\s(?P<chapid>\d+(\.\d+)*-\d+(\.\d+)*([A-Z])*)"
                                  r"|N\.D\. LEXIS \d+")

    h1_pattern_con = re.compile(r'^CONSTITUTION OF NORTH DAKOTA|CONSTITUTION OF THE UNITED STATES OF AMERICA')
    section_pattern_con = re.compile(r'^(Section(s)?|§) (?P<id>\d+(\.\d+)*)(\.| and| to)')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>[IVX]+|\d+)')
    article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+(\w)?)')


class CustomisedRegexID(RegexPatterns):
    """ Customised regex patterns for ID code"""

    h2_article_pattern = re.compile(r'^(article)\s(?P<id>\d+([a-zA-Z])*)', re.I)
    section_pattern = re.compile(r'^§?(\s?)(?P<id>\d+-\d+[a-zA-Z]?(-\d+)?)\.?', re.I)
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)\.\d+\.\d+)(?P<ol>(\([a-z]\))(\(\d+\))*)*)')
    code_pattern = re.compile(r'N\.D\. LEXIS \d+')


class CustomisedRegexWY(RegexPatterns):
    """ Customised regex patterns for WY code"""

    section_pattern = re.compile(r'^§*\s*(?P<id>\d+(\.\d+)*-\d+(\.[A-Z]+)*-\d+(\.\d+)*)', re.I)
    h2_division_pattern = re.compile(r'^Division (?P<id>\d+)\.')
    h2_article_pattern = re.compile(r'^article\s(?P<id>\d+(\.*[a-zA-Z])*)', re.I)
    h2_subpart_pattern = re.compile(r'^subpart\s(?P<id>\d+(\.*[a-zA-Z])*)', re.I)

    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)-\d+-\d+)(?P<ol>(\([a-z]\))(\([ivxl]+\))*(\(\w+\))*)*)')
    code_pattern = re.compile(r'\d+ Wyo\. LEXIS \d+')

    h1_pattern_con = re.compile(r'^THE CONSTITUTION OF THE UNITED STATES OF AMERICA|'
                                r'^Constitution of the State of Wyoming')
    h2_article_pattern_con = re.compile(r'^ARTICLE (?P<id>\d+)', re.I)
    section_pattern_con = re.compile(r'^(Section|§) (?P<id>\d+)')
    section_pattern_con1 = re.compile(r'^Section (?P<id>\d+)')

    cite_tag_pattern = re.compile(r"\d+-\d+-\d+((\([a-z]\))(\([ivxl]+\))*(\(\w+\))*)*|\d+ Wyo\. LEXIS \d+")


class CustomisedRegexTN(RegexPatterns):
    """ Customised regex patterns for TN code"""

    section_pattern = re.compile(r'^(?P<id>\d+-\d+([a-z])?-\d+(\.\d+)?)', re.I)
    cite_pattern = re.compile(r'\b(?P<cite>(?P<title>\d{1,2})-\d(\w+)?-\d+(\.\d+)?)(\s*(?P<ol>(\(\w+\))+))?')
    code_pattern = re.compile(r'(\d+ (Ga\.) \d+)|(\d+ Ga\.( App\.) \d+)'
                              r'(\d+ S\.E\.(2d)? \d+)|(\d+ U\.S\.(C\. §)? \d+(\(\w\))?)'
                              r'(\d+ S\. (Ct\.) \d+)|(\d+ L\. (Ed\.) \d+)|'
                              r'(\d+ L\.R\.(A\.)? \d+)|(\d+ Am\. St\.( R\.)? \d+)'
                              r'(\d+ A\.L\.R\.(2d)? \d+)')


class CustomisedRegexKY(RegexPatterns):
    h1_pattern = re.compile(r'title (?P<id>[IVXL]+)', re.I)
    section_pattern = re.compile(r'^(?P<id>\d+([A-Z]*?)\.\d+(-\d+)*?)\.', re.I)

    cite_pattern = re.compile(r'(?P<cite>(?P<title>\d+[a-zA-Z]*)\.\d+(\(\d+\))*(-\d+)*)(\s*(?P<ol>(\(\w+\))+))?')
    code_pattern = re.compile(r'((Ky\.\s*(L\. Rptr\.\s*)*\d+)|'
                              r'(Ky\.\s?(App\.)?\s?LEXIS\s?\d+)|'
                              r'(U\.S\.C\.\s*secs*\.\s*\d+(\([a-zA-Z]\))*(\(\d+\))*)|'
                              r'(OAG \d+-\d+))')

    cite_tag_pattern = re.compile(r"(KRS)*\s?\d+[a-zA-Z]*\.\d+(\(\d+\))*(-\d+)*|"
                                  r"(KRS Chapter \d+[a-zA-Z]*)|"
                                  r"(KRS Title \D+, Chapter \D+?,)|"
                                  r"KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                                  r"(KRS\s*\d+[a-zA-Z]*\.\d+\(\d+\)|"
                                  r"(U.S.C.\s*secs*\.\s*\d+)|"
                                  r"(Ky.\s?(App\.)?\s?LEXIS\s?\d+)|"
                                  r"(Ky.\s*(L. Rptr.\s*)*\d+)|"
                                  r"(OAG \d+-\d+))")


class CustomisedRegexRI(RegexPatterns):
    """ Customised regex patterns for RI code"""

    h1_pattern = re.compile(r'^Title (?P<id>\d+[A-Z]?(\.\d+)?)')
    h2_chapter_pattern = re.compile(r'^Chapter (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)')
    h2_article_pattern = re.compile(r'^Article (?P<id>(\d+|[IVXCL]+))')
    h2_part_pattern = re.compile(r'^Part (?P<id>(\d+|[IVXCL]+))')
    h2_subpart_pattern = re.compile(r'^Subpart (?P<id>[A-Z0-9])')
    amend_pattern_con = re.compile(r'^Amendment (?P<id>[IVXCL]+)')
    article_pattern_con = re.compile(r'^Article (?P<id>[IVXCL]+)')
    section_pattern = re.compile(r'(?P<id>^\d+[A-Z]?(\.\d+)?-\d+(-\d+)?([A-Z](-\d+)?)?(\.\d+(-\d+)?(\.\d+((\.\d+)?\.\d+)?)?(-\d+)?)?|^Chs\.\s*\d+\s*-\s*\d+\.)')
    ul_pattern = re.compile(r'^Chapters? (?P<id>\d+(\.\d+)?(\.\d+)?([A-Z])?)')
    section_pattern_1 = None
    section_pattern_con = re.compile(r'^§ (?P<id>\d+)\.')
    h1_pattern_con = re.compile(r'^Constitution of the State|^CONSTITUTION OF THE UNITED STATES')
    h2_article_pattern_con = re.compile(r'^Article (?P<id>[IVXCL]+)')
    code_pattern = re.compile(
                    r'((R\.I\. Const\.,? ((Decl\. Rights )?(art\.|article|Art\.|Article)( \d+| ?[IVXCL]+) ?((\. |, )?(Sec\.|§{1,2}|Section)\s+(\d+|[IVXCL]+))?)?)(?!(Amend|amend))|'
                    r'(\d+ R\.I\. \d+)|'
                    r'(\d+ R\.I\. LEXIS \d+)|'
                    r'(R\.I\. R\. Evid\. \d+)|'
                    r'(\d+- ?RICR-\d+-\d+-\d+(\.\d+[A-Z0-9()]+)?)|'
                    r'(R\.I\. Econ\. Dev\. Corp\. v\. Parking Co\.)|'
                    r'(R\.I\. Gen\. Laws)|'
                    r'(R\.I\. Airport Corp\.)|'
                    r'(R\.I\. Const\.,? (Amend|amend)\.,? (Art\. )?(\d+|[IVXCL]+)(, (Sec\.|§{1,2}) \d+)?)|'
                    r'(R\.I\. Super\. Ct\. R\. (Civ|Crim)\. P\. \d+(\. State v\. Long)?))')
    cite_tag_pattern = re.compile(
                    r'\d+[A-Z]?(\.\d+)?-\d+(-\d+)?([A-Z](-\d+)?)?(\.\d+(-\d+)?(\.\d+((\.\d+)?\.\d+)?)?(-\d+)?)?((\s?\([a-z0-9A-Z\n]+\))+)?|'
                    r'((R\.I\. Const\.,? ((Decl\. Rights )?(art\.|article|Art\.|Article)( \d+| ?[IVXCL]+) ?((\. |, )?(Sec\.|§{1,2}|Section)\s+(\d+|[IVXCL]+))?)?)(?!(Amend|amend))|'
                    r'(\d+ R\.I\. \d+)|'
                    r'(\d+ R\.I\. LEXIS \d+)|'
                    r'(R\.I\. R\. Evid\. \d+)|'
                    r'(\d+- ?RICR-\d+-\d+-\d+(\.\d+[A-Z0-9()]+)?)|'
                    r'(R\.I\. Econ\. Dev\. Corp\. v\. Parking Co\.)|'
                    r'(R\.I\. Gen\. Laws)|'
                    r'(R\.I\. Airport Corp\.)|'
                    r'(R\.I\. Const\.,? (Amend|amend)\.,? (Art\. )?(\d+|[IVXCL]+)(, (Sec\.|§{1,2}|Section) \d+)?)|'
                    r'(R\.I\. Super\. Ct\. R\. (Civ|Crim)\. P\. \d+(\. State v\. Long)?))')
    cons_cite_pattern = re.compile(r'(R\.I\. Const\.,? ((Decl\. Rights )?(art\.|article|Art\.|Article)( \d+| ?[IVXCL]+) ?((\. |, )?(Sec\.|§{1,2}|Section)\s+(\d+|[IVXCL]+))?)?)(?!(Amend|amend))')
    ri_cite_pattern = re.compile(r'((?P<title>R\.I\.) Const\.,? (art\.|article|Art\.|Article) ?(?P<article_num>[IVXCL]+) ?[.,]? (Sec\.|§{1,2}|Section)\s+(?P<sec_num>\d+))')
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+[A-Z]?(\.\d+)?)-(?P<chap>\d+)(-\d+)?([A-Z](-\d+)?)?(\.\d+(-\d+)?(\.\d+((\.\d+)?\.\d+)?)?(-\d+)?)?)(?P<ol>((\s?\([a-z0-9\sA-Z]+\))+)?))')


class CustomisedRegexMS(RegexPatterns):
    section_pattern = re.compile(
        r'§§? (?P<id>\d+-\d+-\d+)')
    ul_pattern = re.compile(r'^Chapter (?P<id>\d+)')
    section_pattern_1 = None
    h2_article_pattern = re.compile(r'^Article (?P<id>\d+)')
    h2_part_pattern = re.compile(r'^Part (?P<id>\d+)')
    h2_subpart_pattern = re.compile(r'^Subpart (?P<id>\d+)')
    h2_subarticle_pattern = re.compile(r'^Subarticle (?P<id>[A-Z])')
    cite_tag_pattern = re.compile(r'\d+-\d+-\d+(( ?\([a-z0-9A-Z]+\) ?)+)?|'
                                  r'((\d+ Miss\. (L\.J\. |(App\. )?LEXIS )?\d+)|'
                                  r'(Miss\. Code Ann\.)|'
                                  r'(Miss\. Const\. (art\.|article|Art\.|Article) \d+, (Sec\.|§{1,2}|Section) \d+)|'
                                  r'(Miss\. (Rule of |R\. )(Civil |Civ\. )(Proc\. |P\. )\d+(( ?\([a-z0-9\sA-Z]+\) ?)+)?)|'
                                  r'((Inc\. v\. )?Miss\. Dep\'t of Revenue( v. AT&T Corp\., \d+)?))')
    cite_pattern = re.compile(r'((?P<cite>(?P<title>\d+)-(?P<chap>\d+)-\d+)(?P<ol>(( ?\([a-z0-9\sA-Z]+\) ?)+)?))')
    cons_cite_pattern = None
    ri_cite_pattern = None
    code_pattern = re.compile(
        r'((\d+ Miss\. (L\.J\. |(App\. )?LEXIS )?\d+)|'
        r'(Miss\. Code Ann\.)|'
        r'( Miss\. Const\. (art\.|article|Art\.|Article) \d+, (Sec\.|§{1,2}|Section) \d+)|'
        r'(Miss\. (Rule of |R\. )(Civil |Civ\. )(Proc\. |P\. )\d+(( ?\([a-z0-9\sA-Z]+\) ?)+)?)|'
        r'((Inc\. v\. )?Miss\. Dep\'t of Revenue( v. AT&T Corp\., \d+)?))')