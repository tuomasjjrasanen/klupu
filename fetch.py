import errno
import os
import os.path
import re
import sys

from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.request import urlopen

import bs4

def iter_issue_urls(index_soup):
    for tr in index_soup("table")[0]("tr"):
        a = tr("a")[0]
        href = a["href"].strip()
        match = re.match(r"(.*)frmtxt(\d+)\.htm", href)
        if match and match.group(2) != "9999":
            yield "%shtmtxt%s.htm" % (match.groups())

def _main():
    base_url = sys.argv[1]
    soup = bs4.BeautifulSoup(urlopen(base_url), from_encoding="windows-1252")
    index_urls = [urljoin(base_url, h3("a")[0]["href"]) for h3 in soup("h3")]
    for index_url in index_urls:
        try:
            resp = urlopen(index_url)
        except HTTPError as err:
            print(err, err.url, file=sys.stderr)
            print("Skipping..", file=sys.stderr)
            continue
        index_soup = bs4.BeautifulSoup(resp, from_encoding="iso-8859-1")
        index_path = urlsplit(index_url).path
        index_filepath = os.path.normpath("." + index_path)
        try:
            os.makedirs(os.path.dirname(index_filepath))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        with open(index_filepath, "w") as f:
            print(index_soup, file=f)
        for issue_url in iter_issue_urls(index_soup):
            issue_url = urljoin(index_url, issue_url)
            try:
                resp = urlopen(issue_url)
            except HTTPError as err:
                print(err, err.url, file=sys.stderr)
                print("Skipping..", file=sys.stderr)
                continue
            issue_soup = bs4.BeautifulSoup(resp, from_encoding="windows-1252")
            issue_path = urlsplit(issue_url).path
            issue_filepath = os.path.normpath("." + issue_path)
            with open(issue_filepath, "w") as f:
                print(issue_soup, file=f)

if __name__ == "__main__":
    _main()
