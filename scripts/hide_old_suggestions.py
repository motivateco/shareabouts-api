#!/usr/bin/env python3

"""
Usage:

    USERNAME='...' PASSWORD='...' python3 hide_old_suggestions.py

"""

import csv
import json
import os
import requests
import datetime
from request_utils import download_all_pages, request_with_retries
import sys


# USERNAME = os.environ['USERNAME']
# PASSWORD = os.environ['PASSWORD']

session = requests.Session()
# session.auth = (USERNAME, PASSWORD)
session.headers = {'content-type': 'application/json', 'x-shareabouts-silent': 'true', 'x-shareabouts-key': 'NmU4NTk2ZTZjOGFkM2U4OWUwNjBkZDBl'}

SUGGESTIONS_URL = 'http://shareabouts-api-production.us-east-1.elasticbeanstalk.com/api/v2/opstools/datasets/divvy/places'

# Download all the ideas
pages = download_all_pages(SUGGESTIONS_URL, session=session)
eighteen_months_ago = (datetime.datetime.now() - datetime.timedelta(days=int(365 * 1.5))).isoformat()

print(f'Hiding ideas submitted before {eighteen_months_ago}', file=sys.stderr)
for page in pages:
    for suggestion in page['features']:
        id = suggestion['id']
        location_type = suggestion['properties'].get('location_type', '(none)')
        suggested_at = suggestion['properties']['created_datetime']
        url = suggestion['properties']['url']
        is_visible = suggestion['properties']['visible']

        # Skip existing stations.
        if location_type == 'existing-station':
            continue

        # If there's an unrecognized type of suggestion, print and skip it.
        if location_type != 'new-suggestion':
            print(f'Unrecognized location type for id {id!r}: {location_type!r}', file=sys.stderr)
            continue

        # Update old stations to be invisible.
        if is_visible and suggested_at < eighteen_months_ago:
            print(f'Hiding suggestion with ID {id!r}', file=sys.stderr)
            request_with_retries('patch', url, session=session,
                data=json.dumps({'type': 'Feature', 'properties': {'visible': False}})
            )
