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
import logging
import logging.handlers
import os
import os.path
import re
import sys
import time

from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.request import urlopen

import bs4

def _make_soup(filepath, encoding="utf-8"):
    with open(filepath, encoding=encoding, errors="replace") as f:
        return bs4.BeautifulSoup(f, from_encoding=encoding)

def _iter_issue_page_filepaths(meetingdoc_dirpath):
    issue_page_filepath_pattern = os.path.join(meetingdoc_dirpath, "htmtxt*.htm")
    for issue_page_filepath in glob.iglob(issue_page_filepath_pattern):
        if os.path.basename(issue_page_filepath) != "htmtxt0.htm":
            yield issue_page_filepath

def _iter_issue_page_urls(meetingdoc_index_soup, meetingdoc_index_url):
    for tr in meetingdoc_index_soup("table")[0]("tr"):
        a = tr("a")[0]
        href = a["href"].strip()
        match = re.match(r"(.*)frmtxt(\d+)\.htm", href)
        if match and match.group(2) != "9999":
            yield urljoin(meetingdoc_index_url,
                          "%shtmtxt%s.htm" % (match.groups()))

def _iter_meetingdoc_index_urls(base_soup, base_url):
    for h3 in base_soup("h3"):
        yield urljoin(base_url, h3("a")[0]["href"])

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

class Error(Exception):
    pass

class HTMLDownloadError(Error):
    pass

class HTMLDownloader(object):

    def __init__(self, base_url, download_dir=".", **kwargs):
        self.__base_url = base_url.rstrip("/")
        self.__base_path = urlsplit(self.__base_url).path
        self.__download_dir = os.path.abspath(download_dir)

        try:
            self.logger = kwargs["logger"]
        except KeyError:
            self.logger = logging.getLogger("klupung.ktweb.HTMLDownloader")
            self.logger.setLevel(logging.INFO)

            logfilepath = os.path.join(self.__download_dir, "download.log")
            loghandler = logging.handlers.WatchedFileHandler(logfilepath)
            logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            loghandler.setFormatter(logging.Formatter(logformat))
            self.logger.addHandler(loghandler)

        self.force_download = False
        self.min_http_request_interval = 1.0
        self.__last_download_time = 0

    def __download_page(self, url, encoding):
        urlpath = urlsplit(url).path
        base, sep, path = urlpath.partition(self.__base_path)
        if base or not sep:
            raise HTMLDownloadError("download URL has different base path than"
                                    " the base URL", url, self.__base_url)
        filepath = os.path.normpath(self.__download_dir + path)
        if os.path.exists(filepath) and not self.force_download:
            self.logger.warning('page %s already exists at %s'
                                ', downloading skipped', url, filepath)
            with open(filepath) as f:
                return bs4.BeautifulSoup(f)

        # Ensure downloads are not made more often than once per
        # self.min_http_request_interval seconds.
        if (self.__last_download_time + self.min_http_request_interval
            - time.time()) > 0:
            time.sleep(waittime)

        try:
            response = urlopen(url)
        finally:
            self.__last_download_time = time.time()

        # Make the target directory with all the leading components, do
        # not care whether the the directory exists or not.
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        soup = bs4.BeautifulSoup(response, from_encoding=encoding)

        # Clean the soup to save diskspace.
        clean_soup = _cleanup_soup(soup)
        with open(filepath, "w") as f:
            print(clean_soup, file=f)

        return clean_soup

    def download(self, policymaker_id):
        url = "%s/%s.htm" % (self.__base_url, policymaker_id)
        self.logger.info("starting to download meeting documents of"
                         " %s from %s to %s", policymaker_id,
                         self.__base_url, self.__download_dir)
        base_soup = self.__download_page(url, "windows-1252")
        for index_url in _iter_meetingdoc_index_urls(base_soup, url):

            # Try to download individual pages, but do not interrupt the
            # whole download process if something goes wrong with a
            # single page. Just log it so the user can come back to it
            # afterwards if necessary.
            try:
                index_soup = self.__download_page(index_url, "iso-8859-1")
                for ai_url in _iter_issue_page_urls(index_soup, index_url):
                    try:
                        self.__download_page(ai_url, "windows-1252")
                    except Exception:
                        self.logger.exception("failed to download issue page %s",
                                              ai_url)
                        continue
            except Exception:
                self.logger.exception("failed to download meeting document"
                                      " index %s", index_url)
                continue

        self.logger.info("finished downloading meeting documents of %s from %s",
                         policymaker_id, self.__base_url)

class HTMLParseError(Error):
    pass

class HTMLParser(object):

    RE_TIME = re.compile(r"(?:[a-zA-Z]+ )?(\d\d?)\.(\d\d?)\.(\d{4})[ ]?,? (?:kello|klo)\s?(\d\d?)\.(\d\d)\s*[–-]\s*(\d\d?)\.(\d\d)")

    def __parse_cover_page_datetimes(self, text):
        retval = []

        for values in HTMLParser.RE_TIME.findall(text):
            (day, month, year,
             start_hour, start_minute,
             end_hour, end_minute) = [int(v) for v in values]

            # Someone uses stupid format to denote that the meeting lasted
            # past midnight.
            end_hour %= 24

            start = datetime.datetime(year, month, day, start_hour, start_minute)
            end = datetime.datetime(year, month, day, end_hour, end_minute)
            if start > end:
                end += datetime.timedelta(1)

            retval.append((start, end))

        return retval

    def __init__(self, *args, **kwargs):

        try:
            self.logger = kwargs["logger"]
        except KeyError:
            self.logger = logging.getLogger("klupung.ktweb.HTMLParser")
            self.logger.setLevel(logging.INFO)

            loghandler = logging.handlers.WatchedFileHandler("parse.log")
            logformat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            loghandler.setFormatter(logging.Formatter(logformat))
            self.logger.addHandler(loghandler)

    def __parse_issue_page(self, filepath):
        soup = _make_soup(filepath)

        return {
        }

    def parse_issue_pages(self, meetingdoc_dirpath):
        retval = []

        for issue_page_filepath in _iter_issue_page_filepaths(meetingdoc_dirpath):
            issue_page = self.__parse_issue_page(issue_page_filepath)
            retval.append(issue_page)

        return retval

    def parse_cover_page(self, meetingdoc_dirpath):
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

        # There must be at least two text elements: datetime and place.
        if len(texts) != 2:
            raise HTMLParseError("cover page has unknown structure for "
                                 "datetime and place information",
                                 cover_page_filepath)

        # The place of the meeting is easy, it's always the last element.
        place = texts[-1]

        # There can be several datetimes within one paragraph.
        datetimes = self.__parse_cover_page_datetimes(texts[0])

        return {
            "datetimes": datetimes,
            "place": place,
        }

    def parse_index_page(self, meetingdoc_dirpath):
        index_filepath = os.path.join(meetingdoc_dirpath, "index.htm")
        index_soup = _make_soup(index_filepath)

        magical_selfurl = index_soup.html.body("a", target="_self")[0]["href"]
        policymaker = os.path.splitext(os.path.basename(magical_selfurl))[0]

        return {
            "policymaker": policymaker,
        }

    def parse_meetingdoc(self, meetingdoc_dirpath):
        index_page = self.parse_index_page(meetingdoc_dirpath)
        cover_page = self.parse_cover_page(meetingdoc_dirpath)
        issue_pages = self.parse_issue_pages(meetingdoc_dirpath)

        return {
            "index_page": index_page,
            "cover_page": cover_page,
            "issue_pages": issue_pages,
        }
