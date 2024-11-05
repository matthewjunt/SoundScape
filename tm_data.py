import requests
import json
import geohash
from geopy.geocoders import Nominatim
import numpy as np
from collections import Counter
from fuzzywuzzy import fuzz  

# Ticketmaster API key
API_KEY = ''

def get_event_data(location, radius=100, size=200):

    # Use geopy to get the latitude and longitude of the location
    geolocator = Nominatim(user_agent="eventapp")
    location_data = geolocator.geocode(location)
    if location_data:
        print(f"Latitude: {location_data.latitude}, Longitude: {location_data.longitude}")
    else:
        print("Location not found.")
        return

    # Convert location to geohash
    geohash_code = geohash.encode(location_data.latitude, location_data.longitude, precision=9)
    #print("Geohash Code:", geohash_code)
    # Set up API request
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': API_KEY,
        'geoPoint': geohash_code,
        'radius': radius,
        'classificationName': "music",
        'segmentName': 'music',
        'size': size,
        'sort': 'relevance,desc',
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error: Unable to fetch data from Ticketmaster API. Status Code: {response.status_code}")
        return

    events_data = response.json()

    if '_embedded' not in events_data or 'events' not in events_data['_embedded']:
        print("No events found.")
        return

    # Extract event data
    events = events_data['_embedded']['events']

    event_list = []

    # Extract relevant information for each event
    for event in events:
        event_info = {
            'Event Name': event.get('name', 'Unknown Event'),
            'Venue': {
                'Name': event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'Unknown Venue'),
                'Address': event.get('_embedded', {}).get('venues', [{}])[0].get('address', {}).get('line1', 'Unknown Address'),
                'City': event.get('_embedded', {}).get('venues', [{}])[0].get('city', {}).get('name', 'Unknown City'),
                'State': event.get('_embedded', {}).get('venues', [{}])[0].get('state', {}).get('name', 'Unknown State'),
                'Latitude': event.get('_embedded', {}).get('venues', [{}])[0].get('location', {}).get('latitude', 'Unknown Latitude'),
                'Longitude': event.get('_embedded', {}).get('venues', [{}])[0].get('location', {}).get('longitude', 'Unknown Longitude'),
                'Distance': event.get('_embedded', {}).get('venues', [{}])[0].get('distance', 'Unknown Distance'),
            },
            'Date and Time': event.get('dates', {}).get('start', {}).get('localDate', 'Unknown Date'),
            'Time': event.get('dates', {}).get('start', {}).get('localTime', 'Unknown Time'),
            'Genres': [classification.get('genre', {}).get('name', 'Unknown Genre') for classification in event.get('classifications', [])],
            'Subgenres': [classification.get('subGenre', {}).get('name', 'Unknown Subgenre') for classification in event.get('classifications', [])],
            'Segments': [classification.get('segment', {}).get('name', 'Unknown Segment') for classification in event.get('classifications', [])],
            'Headliners': [performer['name'] for performer in event.get('_embedded', {}).get('attractions', []) if 'name' in performer],
            'Supporting Acts': [performer['name'] for performer in event.get('_embedded', {}).get('attractions', [])[1:] if 'name' in performer],
            
        }

        # Add the event info to the event list
        event_list.append(event_info)

    # Save the event data to a JSON file
    with open('ticketmaster_events_data.json', 'w') as f:
        json.dump({'events': event_list}, f, indent=4)

    print(f"Data for {len(event_list)} events saved to 'ticketmaster_events_data.json'.")


def main():
    location = input("Enter the city where you'd like to find events (e.g., Los Angeles, New York): ")
    get_event_data(location)

if __name__ == "__main__":
    main()
