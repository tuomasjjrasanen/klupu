#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
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

import errno
import os.path
import sys

import klupu

def _main():
    dest_dirpath = sys.argv[1]
    for minutes_dirpath in sys.argv[2:]:
        minutes_dirpath = os.path.normpath(minutes_dirpath)

        minutes_dirname = os.path.basename(minutes_dirpath)
        clean_minutes_dirpath = os.path.join(dest_dirpath, minutes_dirname)
        try:
            os.mkdir(clean_minutes_dirpath)
        except OSError as err:
            if err.errno != errno.EEXIST:
                raise err

        index_filename = "index.htm"
        index_filepath = os.path.join(minutes_dirpath, index_filename)
        index_soup = klupu.read_soup(index_filepath, "iso-8859-15")
        clean_index_soup = klupu.clean_soup(index_soup)
        clean_index_filepath = os.path.join(clean_minutes_dirpath, index_filename)
        with open(clean_index_filepath, "w") as f:
            f.write(clean_index_soup.prettify(formatter="html"))

        for issue_filepath in klupu.iter_issue_filepaths(minutes_dirpath):
            issue_filename = os.path.basename(issue_filepath)
            issue_soup = klupu.read_soup(issue_filepath, "windows-1252")
            clean_issue_soup = klupu.clean_soup(issue_soup)
            clean_issue_filepath = os.path.join(clean_minutes_dirpath, issue_filename)
            with open(clean_issue_filepath, "w") as f:
                f.write(clean_issue_soup.prettify(formatter="html"))

        info_filename = klupu.INFO_FILENAME
        info_filepath = os.path.join(minutes_dirpath, info_filename)
        info_soup = klupu.read_soup(info_filepath, "windows-1252")
        clean_info_soup = klupu.clean_soup(info_soup)
        with open(os.path.join(clean_minutes_dirpath, info_filename), "w") as f:
            f.write(clean_info_soup.prettify(formatter="html"))

if __name__ == "__main__":
    _main()
