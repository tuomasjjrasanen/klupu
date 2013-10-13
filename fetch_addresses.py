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

import sys
import time
import urllib.parse
import urllib.request
import urllib.response

from bs4 import BeautifulSoup

def find_result_trs(soup):
    # Query results are always marked with following h1:
    result_marker = soup.body("h1", text="Postinumerohaun tulos")[0]

    # Results are in the first table sibling.
    result_table = result_marker.parent.parent("table")[0]

    # The first row contains just headings.
    return result_table("tr")[1:]

def query(zipcode="", po_commune="", po_commune_radio=""):
    parameters = {
        "zipcode": zipcode,
        "po_commune": po_commune.encode("iso-8859-1"),
        "po_commune_radio": po_commune_radio,
        "streetname": "",
        }
    paramstr = urllib.parse.urlencode(parameters)
    url = "http://www.verkkoposti.com/e3/postinumeroluettelo?%s" % paramstr
    response = urllib.request.urlopen(url)
    return BeautifulSoup(response)

def _main():

    # Use set, because we are searching by zipcodes and the same
    # street might have several zipcodes. Let's just pick one of the
    # hits.
    streetnames = set()
    zipcode_soup = query(po_commune_radio="commune", po_commune=sys.argv[1])
    for tr in find_result_trs(zipcode_soup):
        zipcode = tr("td")[0].text.strip().split(" ")[0]
        streetname_soup = query(zipcode=zipcode)
        time.sleep(2)
        for tr in find_result_trs(streetname_soup):
            streetname = tr("td")[0].text.strip()
            streetnames.add(streetname)

    for streetname in sorted(streetnames):
        print(streetname)

if __name__ == "__main__":
    _main()
