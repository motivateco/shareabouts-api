#!/usr/bin/env python3

"""
Usage:

    USERNAME='...' PASSWORD='...' python3 hide_old_station  s.py

"""

import csv
import json
import requests
import datetime
from request_utils import download_all_pages, request_with_retries
import sys


session = requests.Session()
session.headers = {
    'content-type': 'application/json',
    'x-shareabouts-silent': 'True',
    'x-shareabouts-key': 'NmU4NTk2ZTZjOGFkM2U4OWUwNjBkZDBl'
}

STATIONS_URL = 'http://shareabouts-api-production.us-east-1.elasticbeanstalk.com/api/v2/opstools/datasets/divvy/places?include_invisible=true&location_type=existing-station'

# Read the stations in CSV format from stdin.
reader = csv.DictReader(sys.stdin)
updated_station_data = list(reader)
station_names = [station['Name'] for station in updated_station_data]
assert len(set(station_names)) == len(station_names), 'There are some duplicated staion names :('

# Organize the stations by name.
stations_by_name = {str(station['Name']): station for station in updated_station_data}

# Download all the ideas
pages = download_all_pages(STATIONS_URL, session=session)
seen_station_names = set()

# Gather all stations, and consider the older ones first.
stations = []
for page in pages:
    stations += page['features']
stations = list(sorted(stations, key=lambda s: s['properties']['created_datetime']))

for station in stations:
    id = station    ['id']
    name = station['properties'].get('name', None)
    url = station['properties']['url']
    is_visible = station['properties']['visible']

    # If station is a duplicate, hide it.
    if not name:
        print(f'Deleting station with ID {id!r} without a name')
        request_with_retries('delete', url + '?include_invisible=true', session=session)

    # If station is visible but we have already updated one with the same
    # name, hide this one.
    elif is_visible and name in seen_station_names:
        print(f'Hiding duplicate station with name {name!r} and ID {id!r}', file=sys.stderr)
        request_with_retries('patch', url, session=session,
            data=json.dumps({'type': 'Feature', 'properties': {'visible': False}})
        )

    # If this is the first time we've seen a station, update it.
    elif name in stations_by_name:
        print(f'Updating station with name {name!r} and ID {id!r}', file=sys.stderr)
        data = stations_by_name[name]
        request_with_retries('patch', url + '?include_invisible=true', session=session,
            data=json.dumps({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(data['Longitude']), float(data['Latitude'])]
                },
                'properties': {
                    'name': name,
                    'visible': True
                }
            })
        )
        seen_station_names.add(name)

    # If the station is visible but not in the stations to update, hide it.
    elif is_visible:
        print(f'Hiding nonexistent station with name {name!r} and ID {id!r}', file=sys.stderr)
        request_with_retries('patch', url, session=session,
            data=json.dumps({'type': 'Feature', 'properties': {'visible': False}})
        )

    else:
        # non-existent but already invisible
        pass

for name, data in stations_by_name.items():
    # If a station is in the update list but doesn't exist, create it.
    if name not in seen_station_names:
        print(f'Creating station with name {name!r}', file=sys.stderr)
        request_with_retries('post', STATIONS_URL, session=session,
            data=json.dumps({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [float(data['Longitude']), float(data['Latitude'])]
                },
                'properties': {
                    'name': data['Name'],
                    'location_type': 'existing-station',
                    'visible': True
                }
            })
        )
        seen_station_names.add(name)
