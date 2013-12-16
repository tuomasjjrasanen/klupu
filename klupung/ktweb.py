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

import errno
import os
import os.path
import re
import sys
import time

import urllib2
import urlparse

import bs4

def _iter_agendaitem_urls(meetingdoc_index_soup, meetingdoc_index_url):
    for tr in meetingdoc_index_soup("table")[0]("tr"):
        a = tr("a")[0]
        href = a["href"].strip()
        match = re.match(r"(.*)frmtxt(\d+)\.htm", href)
        if match and match.group(2) != "9999":
            yield urlparse.urljoin(meetingdoc_index_url,
                                   "%shtmtxt%s.htm" % (match.groups()))

def _iter_meetingdoc_index_urls(base_soup, base_url):
    for h3 in base_soup("h3"):
        yield urlparse.urljoin(base_url, h3("a")[0]["href"])

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

class HTMLDownloader(object):

    def __init__(self):
        self.force_download = False
        self.min_http_request_interval = 1.0
        self.__last_download_time = 0

    def __download_page(self, url, encoding):
        filepath = os.path.normpath("." + urlparse.urlsplit(url).path)
        if os.path.exists(filepath) and not self.force_download:
            print('%s already exists in %s, downloading skipped'
                  % (url, filepath), file=sys.stderr)
            with open(filepath) as f:
                return bs4.BeautifulSoup(f)

        # Ensure downloads are not made more often than once per
        # self.min_http_request_interval seconds.
        if (self.__last_download_time + self.min_http_request_interval
            - time.time()) > 0:
            time.sleep(waittime)

        try:
            response = urllib2.urlopen(url)
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

    def download(self, base_url):
        base_soup = self.__download_page(base_url, "windows-1252")
        for index_url in _iter_meetingdoc_index_urls(base_soup, base_url):

            try:
                index_soup = self.__download_page(index_url, "iso-8859-1")
            except urllib2.HTTPError as err:
                print("failed to download meetingdoc index", err, err.url,
                      "skipped", file=sys.stderr)
                continue

            for agendaitem_url in _iter_agendaitem_urls(index_soup, index_url):

                try:
                    self.__download_page(agendaitem_url, "windows-1252")
                except urllib2.HTTPError as err:
                    print("failed to download agendaitem", err, err.url,
                          "skipped", file=sys.stderr)
                    continue
