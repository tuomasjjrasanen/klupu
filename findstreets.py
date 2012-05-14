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

import re
import sys

def _main():
    counts = {}
    cases = {}
    with open(sys.argv[1]) as f:
        for line in f:
            line = line.strip()
            nominative, case = line.split(",")
            counts[nominative] = 0
            cases[case] = nominative

    for filepath in sys.argv[3:]:
        with open(filepath) as f:
            text = f.read()
        words = set(re.split(r"[^a-zA-ZåäöÅÄÖ]", text))
        for case in words & set(cases):
            nominative = cases[case]
            counts[nominative] += 1

    with open(sys.argv[2], "w") as f:
        for nominative, count in counts.items():
            if count:
                print(nominative, count, sep=",", file=f)

if __name__ == "__main__":
    _main()
