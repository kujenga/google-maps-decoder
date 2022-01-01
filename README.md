# google-maps-decoder
Decoding utility for google maps data exports, currently focused on turning the
basic CSV file exports from lists of saved places into GPX files and other
formats that can be used elsewhere. It uses the [Google Places API][placesAPI]
to transform the exports into more portable information.

## Usage

First, get a Google Maps API key following the instructions here:
https://developers.google.com/maps/documentation/places/web-service/get-api-key

```
./transform.py --key=$MAPS_API_KEY --format=gpx list.csv
```
