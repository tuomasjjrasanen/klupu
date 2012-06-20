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

import json
import os.path
import re
import sys

from bs4 import BeautifulSoup

def _main():
    cases = {}
    issue_filepaths = {}
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            nominative, case = line.split(",")
            cases[case] = nominative

    for filepath in sys.argv[3:]:
        with open(filepath) as f:
            soup = BeautifulSoup(f)
        text = re.sub(r"\s+", " ", soup.text)
        words = set(re.split(r"[^a-zA-ZåäöÅÄÖ]", text))
        for case in words & set(cases):
            nominative = cases[case]
            filepaths = issue_filepaths.setdefault(nominative, set())
            filepaths.add(filepath)

    objects = []
    data = {"objects": objects}
    locations = {}

    with open(sys.argv[2]) as f:
        for line in f:
            line = line.strip()
            nominative, lat, lng = line.split(",")
            if not nominative in locations:
                locations[nominative] = (float(lat), float(lng))

    for nominative, filepaths in issue_filepaths.items():
        if not nominative in locations:
            continue
        urls = []
        for filepath in filepaths:
            urls.append("http://www3.jkl.fi/" + os.path.splitext(filepath)[0] + ".htm")
        lat, lng = locations[nominative]
        obj = {"address": nominative, "issues": urls, "lat": lat, "lng": lng}
        objects.append(obj)

    json.dump(data, sys.stdout)

if __name__ == "__main__":
    _main()
