# -*- coding: utf-8 -*-
# KlupuNG
# Copyright (C) 2013 Koodilehto Osk <http://koodilehto.fi>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime
import errno
import glob
import os
import os.path
import re
import time

from codecs import open

from urllib2 import urlopen
from urlparse import urljoin, urlsplit

import bs4

_COVER_PAGE_FILENAME = "htmtxt0.htm"

def is_meeting_document_dir(dirpath):
    for dirpath, dirnames, filenames in os.walk(dirpath):
        if not _COVER_PAGE_FILENAME in filenames:
            return False
        break
    return True

def _make_soup(filepath, encoding="utf-8"):
    with open(filepath, encoding=encoding, errors="replace") as f:
        return bs4.BeautifulSoup(f, from_encoding=encoding)

def _cleanup_soup(soup):
    for tag in soup.find_all(text=lambda t: isinstance(t, bs4.Comment)):
        tag.extract()

    for tag in soup.find_all(text=lambda t: isinstance(t, bs4.Declaration)):
        tag.extract()

    for tag in soup("style"):
        tag.extract()

    for tag in soup("meta"):
        tag.extract()

    for tag in soup.find_all():
        attrs = tag.attrs
        saved_attrs = set(["class", "href", "target"]) & set(attrs.keys())
        tag.attrs = {a: attrs[a] for a in saved_attrs}

    for tag in soup.find_all(text=True):
        tag.replace_with(re.sub(r"\r", "", tag.string))

    return soup

def _print_to_file(filepath, printable):
    # Make the target directory with all the leading components, do not
    # care whether the the directory exists or not.
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    with open(filepath, "w") as f:
        print(printable, file=f)

def _download_page(url, encoding="utf-8"):
    response = urlopen(url)
    dirty_soup = bs4.BeautifulSoup(response, from_encoding=encoding)
    clean_soup = _cleanup_soup(dirty_soup)

    filepath = os.path.normpath("." + urlsplit(url).path)

    _print_to_file(filepath, clean_soup)

    return filepath, clean_soup

def download_meeting_document(meeting_document_url, download_interval=1):
    index_filepath, index_soup = _download_page(meeting_document_url,
                                                encoding="iso-8859-1")
    last_download_time = time.time()

    meeting_document_dir = os.path.dirname(index_filepath)
    _print_to_file(os.path.join(meeting_document_dir, "origin_url"), meeting_document_url)

    for tr in index_soup("table")[0]("tr"):
        a = tr("a")[0]
        href = a["href"].strip()
        match = re.match(r"(.*)frmtxt(\d+)\.htm", href)
        if not match or match.group(2) == "9999":
            continue
        agenda_item_url = urljoin(meeting_document_url,
                                  "%shtmtxt%s.htm" % (match.groups()))
        pause = max(last_download_time - time.time() + download_interval, 0)
        time.sleep(pause)
        _download_page(agenda_item_url, encoding="windows-1252")

    return meeting_document_dir

def query_meeting_document_urls(url):
    response = urlopen(url)
    dirty_soup = bs4.BeautifulSoup(response, from_encoding="windows-1252")
    clean_soup = _cleanup_soup(dirty_soup)

    retval = []
    for h3 in clean_soup("h3"):
        rel_url = h3("a")[0]["href"]
        abs_url = urljoin(url, rel_url)
        retval.append(abs_url)

    return retval

_RE_PERSON = re.compile(ur"([A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*(?: [A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*)+)")
_RE_DNRO = re.compile(r"Dnro (\d+[\s\xa0\xad]?/\d+)")
_RE_WS = re.compile(r"[\s\xa0\xad]+")

def _trimws(text):
    return _RE_WS.sub(" ", text).strip()

def _parse_agenda_item_resolution(agenda_item_soup):
    resolution = None
    for p in agenda_item_soup.html.body("p"):
        match = re.match(ur"^[\s\xa0\xad]*Päätös[\s\xa0\xad]+(.*)", p.text, re.DOTALL)
        if match:
            resolution = _trimws(match.group(1))
    return resolution

def _parse_agenda_item_preparers(agenda_item_soup):
    preparers = []
    for text in [_trimws(p.text) for p in agenda_item_soup("p")]:
        if text.startswith("Asian valmisteli"):
            preparers.extend(_RE_PERSON.findall(text))
            break
    return preparers

def _parse_agenda_item_dnro(agenda_item_soup):
    ps = agenda_item_soup.html.body("p")
    dnros = []
    for text in [_trimws(p.text) for p in ps]:
        dnro_match = _RE_DNRO.match(text)
        if dnro_match:
            dnros.append(dnro_match.group(1))

    try:
        dnro = dnros[0]
    except IndexError:
        # Some of the agenda items in each meeting are "standard"
        # agenda items, e.g. opening of the meeting, determination
        # of quorum, which do not have Dnro.
        dnro = None

    if dnro == "0/00":
        dnro = None

    return dnro

def _parse_agenda_item_subject(agenda_item_soup, number):
    for p in agenda_item_soup.html.body("p"):
        text = _trimws(p.text)
        match = re.match(r"%d " % number, text)
        if match:
            return text[match.end():]
    return None

def _parse_agenda_item(agenda_item_filepath):
    agenda_item_soup = _make_soup(agenda_item_filepath)

    agenda_item_filename = os.path.basename(agenda_item_filepath)
    number = int(re.match(r"htmtxt([0-9]+)\.htm", agenda_item_filename).group(1))

    subject = _parse_agenda_item_subject(agenda_item_soup, number)
    dnro = _parse_agenda_item_dnro(agenda_item_soup)
    preparers = _parse_agenda_item_preparers(agenda_item_soup)
    resolution = _parse_agenda_item_resolution(agenda_item_soup)

    return {
        "number": number,
        "dnro": dnro,
        "preparers": preparers,
        "subject": subject,
        "resolution": resolution,
        }

def _parse_agenda_items(meeting_document_dirpath):
    retval = []

    agenda_item_filepath_pattern = os.path.join(meeting_document_dirpath, "htmtxt*.htm")
    for agenda_item_filepath in glob.iglob(agenda_item_filepath_pattern):
        if os.path.basename(agenda_item_filepath) == _COVER_PAGE_FILENAME:
            continue
        agenda_item = _parse_agenda_item(agenda_item_filepath)
        retval.append(agenda_item)

    return retval

def _parse_start_datetime(text):
    pattern = r"(?P<weekday>[a-zA-Z]+)?" \
        r"[ ]*" \
        r"(?P<day>[0-9]{1,2})\.(?P<month>[0-9]{1,2})\.(?P<year>[0-9]{4})" \
        r"[, ]+(?:kello|klo)[ ]*" \
        r"(?P<hour>[0-9]{1,2})\.(?P<minute>[0-9]{2})" \
        r".*"

    match = re.match(pattern, text)
    if not match:
        return None

    day = int(match.group("day"))
    month = int(match.group("month"))
    year = int(match.group("year"))
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))

    return datetime.datetime(year, month, day, hour, minute)

def _parse_cover_page(meeting_document_dirpath):
    cover_page_filepath = os.path.join(meeting_document_dirpath, _COVER_PAGE_FILENAME)
    cover_page_soup = _make_soup(cover_page_filepath)

    # Find the meeting info marker. Datetimes and such are nearby...
    meeting_info_markertag = cover_page_soup(text=re.compile("KOKOUSTIEDOT"))[0]

    meeting_info_texts = []

    # Filters p-elements which might contain the actual payload
    # (datetimes and place). Looks a bit scary but seems to work
    # really well in practice.
    for p in meeting_info_markertag.parent.parent.parent.parent("td")[1]("p"):
        meeting_info_text = _trimws(p.text)
        if meeting_info_text:
            # Accept only non-empty strings.
            meeting_info_texts.append(meeting_info_text)

    start_datetime = None
    for meeting_info_text in meeting_info_texts:
        start_datetime = _parse_start_datetime(meeting_info_text)
        if start_datetime is not None:
            # Assume the very first match is the starting time.
            break

    if start_datetime is None:
        # Fallback to bullet-proof method: get the start time from the
        # directory path. However, it is not as accurate because it is
        # often just a template value.
        year = int(os.path.basename(os.path.dirname(meeting_document_dirpath)))
        dirname = os.path.basename(meeting_document_dirpath)
        day = int(dirname[:2])
        month = int(dirname[2:4])
        hour = int(dirname[4:6])
        minute = int(dirname[6:8])
        start_datetime = datetime.datetime(year, month, day, hour, minute)

    publish_datetime = None
    publish_datetime_marker_re = re.compile(ur"PÖYTÄKIRJA YLEISESTI")
    publish_datetime_markers = cover_page_soup(text=publish_datetime_marker_re)
    if publish_datetime_markers:
        publish_datetime_marker = publish_datetime_markers[0]
        tds = publish_datetime_marker.parent.parent.parent.parent("td")
        texts = tds[1](text=re.compile(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}"))
        if texts:
            publish_datetime = datetime.datetime.strptime(texts[0], "%d.%m.%Y")

    return {
        "start_datetime": start_datetime,
        "publish_datetime": publish_datetime,
        }

def parse_meeting_document(meeting_document_dirpath):
    origin_url_filepath = os.path.join(meeting_document_dirpath, "origin_url")
    if os.path.exists(origin_url_filepath):
        with open(origin_url_filepath) as f:
            origin_url = f.readline().strip()
    else:
        origin_url = ""

    policymaker_dirpath = os.path.join(meeting_document_dirpath, "..", "..")
    policymaker_absdirpath = os.path.abspath(policymaker_dirpath)
    policymaker_abbreviation = os.path.basename(policymaker_absdirpath)

    origin_id = "/".join(meeting_document_dirpath.split(os.path.sep)[-3:])

    meeting_document = {
        "policymaker_abbreviation": policymaker_abbreviation,
        "origin_url": origin_url,
        "origin_id": origin_id,
        }

    meeting_document.update(_parse_cover_page(meeting_document_dirpath))

    meeting_document["agenda_items"] = _parse_agenda_items(meeting_document_dirpath)

    return meeting_document
