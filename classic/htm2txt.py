# klupu - scrape meeting minutes of governing bodies of city of Jyväskylä
# Copyright (C) 2013 Koodilehto Osk <http://koodilehto.fi>
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

import os.path
import re
import sys

from bs4 import BeautifulSoup

def _main():
    for filepath in sys.argv[1:]:

        with open(filepath) as f:
            soup = BeautifulSoup(f)

        text = re.sub(r"\s+", " ", soup.text)

        with open(os.path.splitext(filepath)[0] + ".txt", "w") as f:
            f.write(text)

if __name__ == "__main__":
    _main()
