from django.conf import settings
from django.core.files import uploadedfile
from rest_framework import exceptions
from usermgmt.countries import COUNTRY_CHOICES
from usermgmt.utils import GENDER_CHOICES, EDU_CHOICES
import chardet, docx, pathlib, re
from nltk import tokenize

NAME_ID_SPLITTER = '__'


def create_headers(speakers):
    """
    Creates all necessary stm headers for the given userlist
    """
    genders = {s.gender for s in speakers}
    gender_dict = dict(GENDER_CHOICES)
    g_header = ';; CATEGORY "0" "SEX" ""\n'
    for gender in genders:
        g_header += f';; LABEL "{gender}" "{gender_dict[gender]}" ""\n'

    edus = {s.education for s in speakers}
    edu_dict = dict(EDU_CHOICES)
    e_header = ';; CATEGORY "1" "EDUCATION" ""\n'
    for edu in edus:
        e_header += f';; LABEL "{edu}" "{edu_dict[edu]}" ""\n'

    p_header = ';; CATEGORY "2" "PERMISSION" ""\n'
    p_header += ';; LABEL "SR" "SPEECH RECOGNITION" ""\n'
    p_header += ';; LABEL "TTS" "TEXT TO SPEECH" ""\n'
    p_header += ';; LABEL "SRTTS" "BOTH" ""\n'

    countries = {s.country for s in speakers}
    country_dict = dict(COUNTRY_CHOICES)
    c_header = ';; CATEGORY "3" "COUNTRY" ""\n'
    for country in countries:
        c_header += f';; LABEL "{country}" "{country_dict[country]}" ""\n'

    accents = {s.accent for s in speakers}
    a_header = ';; CATEGORY "4" "ACCENT" ""\n'
    for accent in accents:
        a_header += f';; LABEL "{accent}" "{accent}" ""\n'

    return g_header + e_header + p_header + c_header + a_header


def folder_relative_path(folder):
    dirs = []
    user = str(folder.owner.username)
    while folder != None:  # go through the folders
        dirs.append(str(folder.name))
        folder = folder.parent
    dirs.append(user)
    dirs.reverse()
    media_path = '/'.join(dirs)
    return media_path


#Deprecated, since absolute paths aren't used anymore
def folder_path(folder):
    media_path = folder_relative_path(folder)
    path = settings.MEDIA_ROOT/media_path
    return path


def split_str(str_, max_len=None):

    if max_len is None:
        return [str_]
    
    if len(str_) <= max_len:
        return [str_]

    strings = re.split('([,;:.?!])', str_)

    if strings[0].strip() == '':
        strings[2] = strings[1] + strings[2]
        del strings[0:2]
    for i in range(2, len(strings), 2):
        if strings[i].strip() == '':
            strings[i-2] = strings[i-2] + strings[i-1]
            del strings[i-1:i+1]

    if len(strings) <= 1: # fallback if no punctuation in the text, split in the middle
        strings = re.split('([ ])', str_)

    limit = 0
    len_start, len_end = 0, len(str_)
    # split string near the middle
    for i in range(0, len(strings), 2):
        word_len = len( strings[i].strip() )
        if abs(len_end - len_start) < abs(len_end - len_start - 2*word_len):
            limit = i
            break
        len_end -= word_len
        len_start += word_len
    return split_str(''.join(strings[:limit]).strip(), max_len=max_len) \
        + split_str(''.join(strings[limit:]).strip(), max_len=max_len)


def parse_file(textfile, separator='\n\n', tknz=False, lang='english'):

    textfile.seek(0)
    filepath = pathlib.PurePath(textfile.name)
    # Check suffix to identify filetype, unknown/no suffix is assumed plain text
    if filepath.suffix in ['.doc', '.docx']:
        doc = docx.Document(textfile)
        content = map(lambda par: par.text, doc.paragraphs)
        if tknz:
            content_str = '\n'.join(content)
    #elif filepath.suffix in [<filetype>]:
    #   handle file type
    else:
        content_bytes: bytes = textfile.read()
        enc = chardet.detect(content_bytes)['encoding']
        content_str = content_bytes.decode(enc)

        content_str = content_str.replace('\r\n', '\n')
        # Normalize newline characters
        content_str = content_str.replace('\r', '\n')

        if not tknz:
            content = re.split(separator, content_str)

    if tknz:
        content = tokenize.sent_tokenize(content_str, language=lang.lower())

    # If there is any [\n]+ remaining (which would get in the way later),
    # replace it by a single \n (to not get in the way later).
    content = map(lambda x: re.sub('\n+', '\n', x), content)

    return content


def split_lines(lines, max_lines=None, max_chars=250):

    # Run char split before line split
    split_content = []
    for line in list(lines):
        split_content += split_str(line, max_chars)

    if max_lines is None:
        return [split_content]

    text_split = []
    num_texts = len(split_content) // max_lines + 1
    len_text = len(split_content) // num_texts + 1

    for i in range(0, len(split_content), len_text):
        lim =  min(i+len_text, len(split_content))
        text_split.append(split_content[i:lim])

    return text_split


def make_file(content: str, filename: str):
    return uploadedfile.SimpleUploadedFile(
        f'{filename}.txt', '\n\n'.join(content).encode('utf-8-sig')
    )
