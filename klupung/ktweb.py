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

import datetime
import errno
import glob
import os
import os.path
import re
import time

from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.request import urlopen

import bs4

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

def download_meetingdoc_dir(meetingdoc_url, download_interval=1):
    index_filepath, index_soup = _download_page(meetingdoc_url,
                                                encoding="iso-8859-1")
    last_download_time = time.time()

    meetingdoc_dir = os.path.dirname(index_filepath)
    _print_to_file(os.path.join(meetingdoc_dir, "origin_url"), meetingdoc_url)

    for tr in index_soup("table")[0]("tr"):
        a = tr("a")[0]
        href = a["href"].strip()
        match = re.match(r"(.*)frmtxt(\d+)\.htm", href)
        if not match or match.group(2) == "9999":
            continue
        agendaitem_url = urljoin(meetingdoc_url,
                                 "%shtmtxt%s.htm" % (match.groups()))
        pause = max(last_download_time - time.time() + download_interval, 0)
        time.sleep(pause)
        _download_page(agendaitem_url, encoding="windows-1252")

    return meetingdoc_dir

def query_meetingdoc_urls(url):
    response = urlopen(url)
    dirty_soup = bs4.BeautifulSoup(response, from_encoding="windows-1252")
    clean_soup = _cleanup_soup(dirty_soup)

    retval = []
    for h3 in clean_soup("h3"):
        rel_url = h3("a")[0]["href"]
        abs_url = urljoin(url, rel_url)
        retval.append(abs_url)

    return retval

_RE_PERSON = re.compile(r"([A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*(?: [A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*)+)")
_RE_DNRO = re.compile(r"Dnro (\d+[ ]?/\d+)")
_RE_TIME = re.compile(r"(?:[a-zA-Z]+ )?(\d\d?)\.(\d\d?)\.(\d{4})[ ]?,? (?:kello|klo)\s?(\d\d?)\.(\d\d)\s*[–-]\s*(\d\d?)\.(\d\d)")

def _parse_agendaitem_resolution(agendaitem_soup):
    resolution = None
    for p in agendaitem_soup.html.body("p"):
        match = re.match(r"^\s*Päätös\s+(.*)", p.text, re.DOTALL)
        if match:
            resolution = re.sub("\s+", " ", match.group(1))
    return resolution

def _parse_agendaitem_preparers(agendaitem_soup):
    preparers = []
    for text in [re.sub(r"\s+", " ", p.text).strip() for p in agendaitem_soup("p")]:
        if text.startswith("Asian valmisteli"):
            preparers.extend(_RE_PERSON.findall(text))
            break
    return preparers

def _parse_agendaitem_dnro(agendaitem_soup):
    ps = agendaitem_soup.html.body("p")
    dnros = []
    for text in [re.sub(r"\s+", " ", p.text) for p in ps]:
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

def _parse_agendaitem_subject(agendaitem_soup):
    indexed_subject = agendaitem_soup.html.body("p", {"class": "Asiaotsikko"})[0].text
    match = re.match(r"^(\d+)\s+", indexed_subject)
    index = int(match.group(1))
    subject = re.sub(r"\s+", " ", indexed_subject[match.end():])
    return index, subject

def _parse_agendaitem(agendaitem_filepath):
    agendaitem_soup = _make_soup(agendaitem_filepath)

    index, subject = _parse_agendaitem_subject(agendaitem_soup)
    dnro = _parse_agendaitem_dnro(agendaitem_soup)
    preparers = _parse_agendaitem_preparers(agendaitem_soup)
    resolution = _parse_agendaitem_resolution(agendaitem_soup)

    return {
        "index": index,
        "dnro": dnro,
        "preparers": preparers,
        "subject": subject,
        "resolution": resolution,
    }

def _parse_agendaitems(meetingdoc_dirpath):
    retval = []

    agendaitem_filepath_pattern = os.path.join(meetingdoc_dirpath, "htmtxt*.htm")
    for agendaitem_filepath in glob.iglob(agendaitem_filepath_pattern):
        if os.path.basename(agendaitem_filepath) == "htmtxt0.htm":
            continue
        agendaitem = _parse_agendaitem(agendaitem_filepath)
        retval.append(agendaitem)

    return retval

def _parse_meeting_info(meetingdoc_dirpath):
    cover_page_filepath = os.path.join(meetingdoc_dirpath, "htmtxt0.htm")
    cover_page_soup = _make_soup(cover_page_filepath)

    # Find the marker element. Datetimes and such are nearby...
    markertag = cover_page_soup(text=re.compile("KOKOUSTIEDOT"))[0]

    # Filters p-elements which might contain the actual payload
    # (datetimes and place). Looks a bit scary but seems to work
    # really well in practice.
    ps = markertag.parent.parent.parent.parent("td")[1]("p")

    # Accept only non-empty strings.
    texts = [re.sub(r"[\xad\s]+", " ", p.text) for p in ps if p.text.strip()]

    meeting_datetimes = []
    for i, text in enumerate(texts):
        timespecs = _RE_TIME.findall(text)
        if not timespecs:
            break
        for timespec in timespecs:
            (day, month, year,
             start_hour, start_minute,
             end_hour, end_minute) = [int(v) for v in timespec]

            # Someone uses stupid format to denote that the meeting
            # lasted past midnight.
            end_hour %= 24

            start = datetime.datetime(year, month, day, start_hour, start_minute)
            end = datetime.datetime(year, month, day, end_hour, end_minute)
            if start > end:
                end += datetime.timedelta(1)

            meeting_datetimes.append((start, end))

    # The place of the meeting is easy, it always follows the last
    # datetime field.
    meeting_place = texts[i]

    return {
        "meeting_datetimes": meeting_datetimes,
        "meeting_place": meeting_place,
    }

def parse_meetingdoc(meetingdoc_dirpath):
    origin_url_filepath = os.path.join(meetingdoc_dirpath, "origin_url")
    if os.path.exists(origin_url_filepath):
        with open(origin_url_filepath) as f:
            origin_url = f.readline().strip()
    else:
        origin_url = ""

    policymaker_dirpath = os.path.join(meetingdoc_dirpath, "..", "..")
    policymaker_absdirpath = os.path.abspath(policymaker_dirpath)
    policymaker_abbreviation = os.path.basename(policymaker_absdirpath)

    meetingdoc = {
        "policymaker_abbreviation": policymaker_abbreviation,
        "origin_url": origin_url,
    }

    meetingdoc.update(_parse_meeting_info(meetingdoc_dirpath))

    meetingdoc["agendaitems"] = _parse_agendaitems(meetingdoc_dirpath)

    return meetingdoc
