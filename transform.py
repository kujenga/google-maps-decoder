#!/usr/bin/env python3

import argparse
import csv
import re
from dataclasses import dataclass
# https://github.com/googlemaps/google-maps-services-python
import googlemaps
from googlemaps import convert
# https://github.com/tkrajina/gpxpy
import gpxpy
import gpxpy.gpx
import gpxpy.gpxfield
from xml.etree.ElementTree import Element


urlRE = re.compile(
    r'https:\/\/www.google.com\/maps\/place\/' +
    r'(?P<name>[^\/]*?)' +
    r'\/' +
    r'data=(?P<data>.*)'
)

#  https://stackoverflow.com/questions/47017387/decoding-the-google-maps-embedded-parameters/47042514#47042514
dataRE = re.compile(r'(?P<start>.*?)(?P<ftid>0x\w+:0x\w+)')


@dataclass
class Place:
    name: str
    lat: float
    lng: float
    gmaps_place_id: str
    address: str


class Parser(object):
    def __init__(self, filepath, api_key, verbose=False):
        self.filepath = filepath
        self.gmaps = googlemaps.Client(key=api_key)
        self.verbose = verbose

    def parse_csv(self):
        places = []
        with open(self.filepath, newline='') as csvfile:
            csvreader = csv.DictReader(csvfile)
            for row in csvreader:
                place = self.parse_line(row)
                places.append(place)
        return places

    def parse_line(self, line):
        title = line['Title']
        note = line['Note']
        url = line['URL']
        m = urlRE.match(url)
        m = m.groupdict()
        _ = m['name']
        data = dataRE.match(m['data'])
        data = data.groupdict()
        _ = data['start']
        ftid = data['ftid']

        place_info = self.gmaps_place_info(ftid)

        if self.verbose:
            print(title, note, m, data)

        return Place(
            title,
            place_info['geometry']['location']['lat'],
            place_info['geometry']['location']['lng'],
            place_info['place_id'],
            place_info['formatted_address'],
        )

    def gmaps_place_info(self, ftid):
        # NOTE: We have to use a call with the underlying request API because
        # this call leverages an undocumented parameter of this API.
        # https://stackoverflow.com/questions/47017387/decoding-the-google-maps-embedded-parameters/47042514#47042514
        return self.gmaps._request("/maps/api/place/details/json", {
            'ftid': ftid,
            # Field definitions:
            #  https://developers.google.com/maps/documentation/places/web-service/details#Place
            'fields': convert.join_list(",", [
                'name',
                'website',
                'place_id',
                'geometry/location',
                'formatted_address',
            ]),
        })['result']

    def render_gpx(self, places, output_file):
        gpx = gpxpy.gpx.GPX()

        for place in places:
            wpt = gpxpy.gpx.GPXWaypoint(
                latitude=place.lat,
                longitude=place.lng,
                name=place.name,
            )
            addr = Element('address')
            addr.text = place.address
            wpt.extensions = [
                addr,
            ]
            gpx.waypoints.append(wpt)

        if output_file == '-':
            print(gpx.to_xml())
        else:
            with open(output_file, 'w') as writer:
                writer.write(gpx.to_xml())


def main():
    parser = argparse.ArgumentParser(
        description='decode google maps takeout data from "Saved" lists.'
    )
    parser.add_argument('csv', help='path to CSV file')
    # API keys can be generated from the instructions here:
    # https://developers.google.com/maps/documentation/places/web-service/get-api-key
    parser.add_argument('--key', required=True,
                        help='Google Maps Places API Key')
    parser.add_argument('--format', help='Format of output')
    parser.add_argument('--out', default='-', help='Output file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()

    p = Parser(args.csv, args.key, verbose=args.verbose)
    parsed = p.parse_csv()

    if args.format == 'gpx':
        p.render_gpx(parsed, args.out)
    else:
        raise Exception('unknown output format: {}'.format(args.format))


if __name__ == '__main__':
    main()
