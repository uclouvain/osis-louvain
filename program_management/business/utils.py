##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import html

LINE_BREAK_SPACE_CHARACTERS = [chr(13), chr(13), chr(9), chr(13), chr(13), chr(13), chr(13), chr(13), chr(13)]
TAG_TO_BE_REPLACE_BY_EMPTY_LINE = ['<br>',  '<tr',  '<td', '</p>', 'span>', 'li>', '</h', 'div>', '<br />']
TAGS_NOT_TREATED = ['<script', '<noscript', '<style', '<!--']
TAGS_TO_TREAT = ['</style', '</script>', '</noscript>', '-->']


def html2text(html_text):
    html_text_to_convert = _get_inner_html(html.unescape(html_text))

    tag_ok = True
    starting_ending_character_of_html_tag = True
    html_converted = ""
    for character_idx in range(len(html_text_to_convert)):
        character_to_convert = html_text_to_convert[character_idx]
        html_converted = _remove_tags(character_idx, html_converted, html_text_to_convert)
        tag_ok = _check_tag_ok(character_idx, html_text_to_convert, tag_ok)

        if character_to_convert == '<':
            starting_ending_character_of_html_tag = False
        if tag_ok and starting_ending_character_of_html_tag and (ord(character_to_convert) != 10):
            html_converted = html_converted + character_to_convert

        if character_to_convert == '>':
            starting_ending_character_of_html_tag = True

        if tag_ok and starting_ending_character_of_html_tag:
            html_converted = html_converted.replace(chr(32) + chr(13), chr(13))
            html_converted = html_converted.replace(chr(9) + chr(13), chr(13))
            html_converted = html_converted.replace(chr(13) + chr(32), chr(13))
            html_converted = html_converted.replace(chr(13) + chr(9), chr(13))
            html_converted = html_converted.replace(chr(13) + chr(13), chr(13))
    html_converted = html_converted.replace(chr(13), '\n')
    return html_converted.strip()


def _check_tag_ok(starting_idx, html_text_to_convert, tag_ok):

    for tag in TAGS_NOT_TREATED:
        if html_text_to_convert[starting_idx:starting_idx + len(tag)].lower() == tag:
            return False

    for tag in TAGS_TO_TREAT:
        if html_text_to_convert[starting_idx:starting_idx + len(tag)].lower() == tag:
            return True
    return tag_ok


def _remove_tags(character_idx, html_converted, html_text_to_convert):
    for idx, html_tag in enumerate(TAG_TO_BE_REPLACE_BY_EMPTY_LINE):
        if html_text_to_convert[character_idx:character_idx + len(html_tag)].lower() == html_tag:
            html_converted = html_converted + LINE_BREAK_SPACE_CHARACTERS[idx]
    return html_converted


def _get_inner_html(html_text_to_convert):
    idx_starting_body_tag = html_text_to_convert.lower().find("<body")
    if idx_starting_body_tag > 0:
        html_text_to_convert = html_text_to_convert[idx_starting_body_tag:]
    idx_ending_body_tag = html_text_to_convert.lower().find("</body>")
    if idx_ending_body_tag > 0:
        html_text_to_convert = html_text_to_convert[:idx_ending_body_tag]
    return html_text_to_convert
