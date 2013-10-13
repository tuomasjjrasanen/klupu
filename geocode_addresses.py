#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# klupu - scrape meeting minutes of governing bodies of city of Jyväskylä
# Copyright (C) 2013 Tuomas Räsänen <tuomasjjrasanen@tjjr.fi>
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
import sys
import time
import urllib.parse
import urllib.request

def query_osm(street, city, country, email, *args):
    parameters = {
        "format": "json",
        "street": street,
        "city": city,
        "countrycodes": country,
        "email": email,
        }
    paramstr = urllib.parse.urlencode(parameters)
    url = "http://nominatim.openstreetmap.org/search?%s" % paramstr
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")

def query_google(street, city, country, *args):
    parameters = {
        "address": "%s %s" % (street, city),
        "sensor": "false",
        "components": "country:%s" % country,
        }
    paramstr = urllib.parse.urlencode(parameters)
    url =" http://maps.googleapis.com/maps/api/geocode/json?%s" % paramstr
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")

QUERY_FUNCTIONS = {
    "google": query_google,
    "osm": query_osm,
}

def _main():
    query_function = QUERY_FUNCTIONS[sys.argv[1]]
    output_rootdir = sys.argv[2]
    address_filename = sys.argv[3]
    email = ""
    if query_function is query_osm:
        email = sys.argv[4]
    with open(address_filename) as address_file:
        for address_line in address_file:
            address, city, country = [s.strip() for s in address_line.split(",")]
            output_dir = os.path.join(output_rootdir, country, city)
            os.makedirs(output_dir)
            output_filename = "%s.json" % address
            output_filepath = os.path.join(output_dir, output_filename)
            with open(output_filepath, "w") as output_file:
                output_file.write(query_function(address, city, country, email))
            time.sleep(2) # Be nice.

if __name__ == "__main__":
    _main()
