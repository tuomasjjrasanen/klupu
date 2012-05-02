# -*- coding: utf-8 -*-
# klupu - scrape meeting minutes of governing bodies of city of Jyväskylä
# Copyright (C) 2012 Tuomas Jorma Juhani Räsänen <tuomasjjrasanen@tjjr.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import os.path
import re

import bs4

INFO_FILENAME = "htmtxt0.htm"

def iter_issue_filepaths(minutes_dirpath):
    pathname = os.path.join(minutes_dirpath, "htmtxt*.htm")
    for issue_filepath in glob.iglob(pathname):
        if os.path.basename(issue_filepath) != INFO_FILENAME:
            yield issue_filepath

def read_soup(filepath, encoding):
    with open(filepath, encoding=encoding, errors="replace") as f:
        return bs4.BeautifulSoup(f, from_encoding=encoding)

def clean_soup(soup):

    for tag in soup.find_all(text=lambda t: isinstance(t, bs4.Comment)):
        tag.extract()

    for tag in soup.find_all(text=lambda t: isinstance(t, bs4.Declaration)):
        tag.extract()

    for tag in soup("style"):
        tag.extract()

    for tag in soup("meta"):
        tag.extract()

    for tag in soup("span"):
        tag.replace_with_children()

    for tag in soup("font"):
        tag.replace_with_children()

    for tag in soup("st1:metricconverter"):
        tag.replace_with_children()

    for tag in soup("st1:personname"):
        tag.replace_with_children()

    for tag in soup.find_all():
        attrs = tag.attrs
        saved_attrs = set(["class", "href", "target"]) & set(attrs.keys())
        tag.attrs = {a: attrs[a] for a in saved_attrs}

    for tag in soup.find_all():
        if not tag.text.strip():
            tag.replace_with_children()

    for tag in soup.find_all(text=True):
        tag.replace_with(cleanws(tag.string))

    return soup

def cleanws(text):
    text = re.sub(r"[\r\n]", " ", text)
    text = re.sub(r"\xad+", " ", text)
    text = re.sub(r"\xa0+", " ", text)
    text = re.sub(r"[ ]+", " ", text)
    return text
