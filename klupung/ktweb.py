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
import tempfile
import time
import traceback

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
    dirpath = os.path.dirname(filepath)
    try:
        os.makedirs(dirpath)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    # Write the contents to a temporary file first, because the
    # existence of the real filepath can be used as an indicator to not
    # re-download and re-write the file again but just read its current
    # value. Writing to a temporary file and then renaming it to its
    # final name guarantees that the contents of the final path is
    # always complete.
    tmp_file = tempfile.NamedTemporaryFile(dir=dirpath, delete=False)
    try:
        print(printable, file=tmp_file)
        tmp_file.close()
    except:
        # Something went wrong when writing to the file. Signal
        # interrupted, fs failed, anything.
        try:
            tmp_file.close()
        finally:
            os.remove(tmp_file.name)
        raise
    else:
        try:
            # File written, now let's move it to its final path.
            os.rename(tmp_file.name, filepath)
        except:
            os.remove(tmp_file.name)
            raise

_last_download_time = None

def _download_clean_soup(url, encoding="utf-8", min_interval=1):
    global _last_download_time

    if _last_download_time is not None:
        pause = max(_last_download_time - time.time() + min_interval, 0)
        time.sleep(pause)

    response = urlopen(url)
    _last_download_time = time.time()

    dirty_soup = bs4.BeautifulSoup(response, from_encoding=encoding)
    clean_soup = _cleanup_soup(dirty_soup)
    return clean_soup

_DOWNLOAD_PAGE_ERROR_POLICIES = set(("raise", "ignore", "log"))
_DOWNLOAD_PAGE_ERROR_POLICIES_STR = ' or '.join([repr(s) for s in _DOWNLOAD_PAGE_ERROR_POLICIES])
def _download_page(url, encoding="utf-8", force=False, min_interval=1,
                   download_dir=os.path.curdir, error_policy="raise"):
    if error_policy not in _DOWNLOAD_PAGE_ERROR_POLICIES:
        raise ValueError("error_policy has invalid value (%r), expected %s" %
                         (error_policy, _DOWNLOAD_PAGE_ERROR_POLICIES_STR))
    filepath = os.path.normpath(download_dir + urlsplit(url).path)
    if force or not os.path.exists(filepath):
        try:
            clean_soup = _download_clean_soup(url,
                                              encoding=encoding,
                                              min_interval=min_interval)
        except Exception, e:
            if error_policy == "raise":
                raise
            if error_policy == "ignore":
                return None, None
            if error_policy == "log":
                with open("%s.log" % filepath, "a") as error_log:
                    traceback.print_exc(file=error_log)
                return None, None
        _print_to_file(filepath, clean_soup)
        return filepath, clean_soup
    return filepath, None

def download_meeting_document(meeting_document_url, min_interval=1, force=False, download_dir=os.path.curdir):
    index_filepath, index_soup = _download_page(meeting_document_url,
                                                encoding="iso-8859-1",
                                                force=True, # Refresh indices always.
                                                min_interval=min_interval,
                                                download_dir=download_dir,
                                                error_policy="log")
    if index_filepath is index_soup is None:
        return None

    meeting_document_dir = os.path.dirname(index_filepath)
    _print_to_file(os.path.join(meeting_document_dir, "origin_url"), meeting_document_url)

    cover_page_url = urljoin(meeting_document_url, _COVER_PAGE_FILENAME)
    _download_page(cover_page_url,
                   encoding="windows-1252",
                   force=True,
                   min_interval=min_interval,
                   download_dir=download_dir,
                   error_policy="log")

    for tr in index_soup("table")[0]("tr"):
        try:
            agenda_item_number = int(tr("td")[0].text)
        except ValueError:
            continue
        agenda_item_url = urljoin(meeting_document_url,
                                  "htmtxt%d.htm" % agenda_item_number)
        _download_page(agenda_item_url, encoding="windows-1252", force=force,
                       min_interval=min_interval,
                       download_dir=download_dir, error_policy="log")

    return meeting_document_dir

def query_meeting_document_urls(url):
    clean_soup = _download_clean_soup(url, encoding="windows-1252")

    retval = []
    for h3 in clean_soup("h3"):
        if h3.text.strip().lower().startswith(u"pöytäkirja"):
            rel_url = h3("a")[0]["href"]
            abs_url = urljoin(url, rel_url)
            retval.append(abs_url)

    return retval

def download_policymaker(policymaker_url, min_interval=1, force=False, download_dir=os.path.curdir):
    meeting_document_urls = query_meeting_document_urls(policymaker_url)
    for meeting_document_url in meeting_document_urls:
        meeting_document_dir = download_meeting_document(meeting_document_url,
                                                         min_interval=min_interval,
                                                         force=force,
                                                         download_dir=download_dir)
        yield meeting_document_dir

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

def _parse_agenda_item_introducers(agenda_item_soup):
    introducers = []
    for text in [_trimws(p.text) for p in agenda_item_soup("p")]:
        if text.startswith("Asian esitteli"):
            introducers.extend(_RE_PERSON.findall(text))
            break
    return introducers

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
    number_found = False
    for p in agenda_item_soup.html.body("p"):
        text = _trimws(p.text)
        if not number_found:
            match = re.match(r"%d$|%d " % (number, number), text)
            if match:
                # The paragraph starts with the given agenda item
                # number, the subject is nearby.
                number_found = True

                # In most cases, the subject follows the number within
                # the same paragraph.
                subject_candidate = text[match.end():].strip()
                if subject_candidate:
                    return subject_candidate
        else:
            # In some rare cases, the subject is the next non-whitespace
            # paragraph.
            subject_candidate = text.strip()
            if subject_candidate:
                return subject_candidate
    return None

def _parse_agenda_item_geometries(agenda_item_soup, geodata):
    # Return example
    # [ { "type": "Point", "category": "address", "name": "Siltakatu 12" },
    #   { "type": "Polygon", "category": "plan_unit", "name": "As Oy Siltakatu" },
    #   { "type": "LineString", "category": "plan", "name": "Siltakatu" },
    # ]
    #
    return []

def _parse_agenda_item(agenda_item_filepath, geodata):
    agenda_item_soup = _make_soup(agenda_item_filepath)

    agenda_item_filename = os.path.basename(agenda_item_filepath)
    number = int(re.match(r"htmtxt([0-9]+)\.htm", agenda_item_filename).group(1))

    subject = _parse_agenda_item_subject(agenda_item_soup, number)
    dnro = _parse_agenda_item_dnro(agenda_item_soup)
    preparers = _parse_agenda_item_preparers(agenda_item_soup)
    introducers = _parse_agenda_item_introducers(agenda_item_soup)
    resolution = _parse_agenda_item_resolution(agenda_item_soup)
    geometries = _parse_agenda_item_geometries(agenda_item_soup, geodata)

    return {
        "number": number,
        "dnro": dnro,
        "preparers": preparers,
        "introducers": introducers,
        "subject": subject,
        "resolution": resolution,
        "geometries": geometries,
        }

def _parse_agenda_items(meeting_document_dirpath, geodata):
    retval = []

    agenda_item_filepath_pattern = os.path.join(meeting_document_dirpath, "htmtxt*.htm")
    for agenda_item_filepath in glob.iglob(agenda_item_filepath_pattern):
        if os.path.basename(agenda_item_filepath) == _COVER_PAGE_FILENAME:
            continue
        agenda_item = _parse_agenda_item(agenda_item_filepath, geodata)
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
    publish_datetime_marker_re = re.compile(ur"PÖYTÄKIRJA\s+YLEISESTI")
    publish_datetime_markers = cover_page_soup(text=publish_datetime_marker_re)
    if publish_datetime_markers:
        publish_datetime_marker = publish_datetime_markers[0]
        tds = publish_datetime_marker.parent.parent.parent.parent("td")
        texts = tds[1](text=re.compile(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}"))
        if texts:
            date_text = re.search(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{4}", texts[0]).group()
            publish_datetime = datetime.datetime.strptime(date_text, "%d.%m.%Y")

    return {
        "start_datetime": start_datetime,
        "publish_datetime": publish_datetime,
        }

def _parse_meeting_document_type(meeting_document_dirpath):
    index_filepath = os.path.join(meeting_document_dirpath, "index.htm")
    index_soup = _make_soup(index_filepath)
    title = index_soup("title")[0].text.strip()
    if title.lower().startswith(u"pöytäkirja"):
        return "minutes"
    if title.lower().startswith(u"esityslista"):
        return "agenda"
    return None

def parse_meeting_document(meeting_document_dirpath, geodata=None):
    meeting_document_type = _parse_meeting_document_type(meeting_document_dirpath)

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
        "type": meeting_document_type,
        }

    meeting_document.update(_parse_cover_page(meeting_document_dirpath))

    meeting_document["agenda_items"] = _parse_agenda_items(meeting_document_dirpath, geodata)

    return meeting_document
