import errno
import os
import os.path
import sys
from urllib.parse import urljoin
from urllib.parse import urlsplit
from urllib.request import urlopen

import bs4

import klupu

def _main():
    base_url = sys.argv[1]
    soup = bs4.BeautifulSoup(urlopen(base_url), from_encoding="windows-1252")
    index_urls = [urljoin(base_url, h3("a")[0]["href"]) for h3 in soup("h3")]
    for index_url in index_urls:
        index_soup = bs4.BeautifulSoup(urlopen(index_url),
                                       from_encoding="iso-8859-1")
        clean_index_soup = klupu.clean_soup(index_soup)
        index_path = urlsplit(index_url).path
        index_filepath = os.path.normpath("." + index_path)
        try:
            os.makedirs(os.path.dirname(index_filepath))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e
        with open(index_filepath, "w") as f:
            f.write(clean_index_soup.prettify())
        for issue_url in klupu.iter_issue_urls(clean_index_soup):
            issue_url = urljoin(index_url, issue_url)
            issue_soup = bs4.BeautifulSoup(urlopen(issue_url),
                                           from_encoding="windows-1252")
            clean_issue_soup = klupu.clean_soup(issue_soup)
            issue_path = urlsplit(issue_url).path
            issue_filepath = os.path.normpath("." + issue_path)
            with open(issue_filepath, "w") as f:
                f.write(clean_issue_soup.prettify())

if __name__ == "__main__":
    _main()
