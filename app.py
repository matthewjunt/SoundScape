# app.py
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import json
import geohash
from geopy.geocoders import Nominatim
import numpy as np
from collections import Counter
from fuzzywuzzy import fuzz  
import spotify_data
import algorithm
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = 'secret_key'

API_KEY = 'XAWCGASB4r41URtFJpkPNGKAk3kUXQxU'
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read'

# Function to get popular events
def get_popular_events():
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': API_KEY,
        'size': 20,
        'classificationName': 'music',
        'sort': 'random',
        'countryCode': 'US',
    }

    response = requests.get(url, params=params)    
    
    if response.status_code == 200:
        data = response.json()
        
        # Filter events
        unique_events = []
        seen_event_names = set()
        for event in data['_embedded']['events']:
            event_name = event['name']
            if event_name not in seen_event_names:
                seen_event_names.add(event_name)
                unique_events.append(event)
        
        # Extract useful information from the events
        events = []
        for event in unique_events:
            venue = event['_embedded']['venues'][0]
            images = event.get('images', [])
            highest_res_image = max(images, key=lambda img: img.get('width', 0) * img.get('height', 0), default={})

            # Safely retrieve state information
            state = venue.get('state', {}).get('name', 'Unknown State')
            city = venue.get('city', {}).get('name', 'Unknown City')
            venue_name = venue.get('name', 'Unknown Venue')
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            date = event['dates']['start']['localDate']
            date_parts = date.split('-')
            month = months[int(date_parts[1]) - 1]
            day = int(date_parts[2])
            
            
            events.append({
                'name': event['name'],
                'id': event['id'],
                'image': highest_res_image.get('url', ''),
                'venue': venue_name,
                'date': f"{month} {day}",
                'city': city,
                'state': state
            })
        return events
    else:
        print("Error fetching events:", response.status_code)
        return []
    

@app.route('/search', methods=['GET', 'POST'])
def search():    
    
    location = request.form.get('location')
    radius = request.form.get('radius')
    search_type = request.form.get('search_type')
    date_range = request.form.get('date_range')
    genre = request.form.get('genre') if search_type == 'manual' else None
    
    # If location is empty, return an error message
    if not location:
        flash('Location is required!', 'error')
        return redirect(url_for('home'))
        
        
    if search_type == 'spotify':
        spotify = spotify_data.main(request.form.get('time_range'))
        
    # Parse date range
    if date_range:
        start_date, end_date = date_range.split(' to ')
        start_date = start_date.replace('/', '-')
        end_date = end_date.replace('/', '-')   
        start_date = f"{start_date}T00:00:00Z"
        end_date = f"{end_date}T23:59:59Z"
        
    # If location is a postal code, convert it to a city name    
    if location.isdigit():
        #get lat and long from postal code
        url = f"https://api.zippopotam.us/us/{location}"
        response = requests.get(url)
        data = response.json()
        location = data['places'][0]['place name']
    
    else:
        location = location
    
    # Use geopy to get the latitude and longitude of the location
    geolocator = Nominatim(user_agent="eventapp")
    location_data = geolocator.geocode(location)
    
    if not location_data:
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
        'classificationName': genre if genre else '',
        'segmentName': 'music',
        'size': 200,
        'sort': 'relevance,desc',
        'startDateTime': start_date if date_range else '',
        'endDateTime': end_date if date_range else '',
    }
    
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error: Unable to fetch data from Ticketmaster API. Status Code: {response.status_code}")
        return

    events_data = response.json()

    if '_embedded' not in events_data or 'events' not in events_data['_embedded']:
        print("No events found?")
        return render_template('search_results.html', events=[], location=location, genre=genre)

    # Extract event data
    events = events_data['_embedded']['events']

    event_list = []
      
    # Extract relevant information for each event
    for event in events:
        # Get date in the format "Month Day"
        date = event.get('dates', {}).get('start', {}).get('localDate', 'Unknown Date')
        months_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month = months_list[int(date.split('-')[1]) - 1]
        day = int(date.split('-')[2])
        date = f"{month} {day}"
        
        images = event.get('images', [])
        highest_res_image = max(images, key=lambda img: img.get('width', 0) * img.get('height', 0), default={})
        
        event_info = {
            'Name': event.get('name', 'Unknown Event'),
            'ID': event.get('id', 'Unknown ID'),
            'Image': highest_res_image.get('url', ''),
            'Venue': {
                'Name': event.get('_embedded', {}).get('venues', [{}])[0].get('name', 'Unknown Venue'),
                'Address': event.get('_embedded', {}).get('venues', [{}])[0].get('address', {}).get('line1', 'Unknown Address'),
                'City': event.get('_embedded', {}).get('venues', [{}])[0].get('city', {}).get('name', 'Unknown City'),
                'State': event.get('_embedded', {}).get('venues', [{}])[0].get('state', {}).get('name', 'Unknown State'),
                'Latitude': event.get('_embedded', {}).get('venues', [{}])[0].get('location', {}).get('latitude', 'Unknown Latitude'),
                'Longitude': event.get('_embedded', {}).get('venues', [{}])[0].get('location', {}).get('longitude', 'Unknown Longitude'),
                'Distance': event.get('_embedded', {}).get('venues', [{}])[0].get('distance', 'Unknown Distance'),
            },
            'Date': date,
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
    
    if search_type == 'spotify':
        spotify_dataset = get_spotify_data()

    if search_type == 'manual':
        ranked_events = []

        seen_event_names = set()  

        for event in event_list:
            event_name = event['Name']
            
            # Skip duplicates
            if event_name in seen_event_names:
                continue
            
            seen_event_names.add(event_name) 
            event_details = {
                'Name': event_name,
                'ID': event.get('ID', 'N/A'),
                'Image': event.get('Image', 'N/A'),
                'Artists': event['Headliners'] + event['Supporting Acts'],
                'Genres': event['Genres'] + event.get('Subgenres', []),
                'Date': event.get('Date'),
                'City': event['Venue']['City'],
                'State': event['Venue']['State'],
                'Address': event['Venue']['Address'],
                'Distance': event['Venue'].get('Distance', 'N/A'),
            }
            ranked_events.append(event_details)
        return render_template('search_results.html', events=ranked_events, spotify_data=[], location=location, genre=genre)
    
    # Run algorithm to rank events based on user preferences
    ranked_events = algorithm.main()
    
    
    return render_template('search_results.html', events=ranked_events, spotify_data=spotify_dataset, location=location, genre=genre)

@app.route("/")
def home():
    popular_events = get_popular_events()
    
    return render_template('index.html', events=popular_events)


# Route to get the event details by event ID
@app.route('/event/<event_id>')
def event_details(event_id):
    # Function to retrieve event details based on event_id
    event = get_event_by_id(event_id)
    if event:
        return render_template('event_details.html', event=event)
    else:
        return "Event not found", 404

def get_spotify_data():
    # Function to parse spotify data from json file into an object to send to front end for display
    with open('spotify_data.json', 'r') as f:
        data = json.load(f)
        artists_data = data['Top Artists']
        tracks_data = data['Top Tracks']
        top_genres = data['Top Genres']
        
        # Create a list of artists
        artists = []
        for artist in artists_data:
            artist_info = {
                'ArtistName': artist['Artist Name'],
                'Genres': artist.get('genres', []),
                'Image': artist['Image']
            }
            artists.append(artist_info)
            
        # Create a list of tracks
        tracks = []
        for track in tracks_data:
            track_info = {
                'TrackName': track['Track Name'],
                'Artists': track['Artists'],
                'Genres': track.get('genres', []),
                'Image': track['Image']
            }
            tracks.append(track_info)
        
        # Create a list of genres
        genres = []
        for genre in top_genres:
            genre_info = {
                'GenreName': genre
            }
            genres.append(genre_info)
            
        # Create a dictionary to store all the data
        spotify_data = {
            'Artists': artists,
            'Tracks': tracks,
            'Genres': genres,
        }
        
        return spotify_data
        

# Function to retrieve event details
def get_event_by_id(event_id):
    # Load event data from file
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        'apikey': API_KEY,
        'id': event_id,
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        event = data.get('_embedded', {}).get('events', [])[0]
        if event:            
            # Find the highest resolution image
            images = event.get('images', [])
            highest_res_image = max(images, key=lambda img: img.get('width', 0) * img.get('height', 0))
            # Get spotify artist link
            for performer in event['_embedded']['attractions']:
                if performer.get('name'):
                    artist = get_spotify_artist_link(performer['name'])
                    performer['spotify_link'] = artist
                    performer['spotify_id'] = artist.split('/')[-1]
                    
            event_info = {
                'name': event['name'],
                'id': event['id'],
                'image': highest_res_image['url'],
                'venue': event['_embedded']['venues'][0].get('name', 'Unknown Venue'),
                'date': event['dates']['start']['localDate'],
                'time': event['dates']['start']['localTime'],
                'genres': [classification['genre']['name'] for classification in event['classifications']],
                'headliners': [performer['name'] for performer in event['_embedded']['attractions'] if performer.get('name')],
                'supporting_acts': [performer['name'] for performer in event['_embedded']['attractions'][1:] if performer.get('name')],
                'tickets': event['url'],
                'spotify_link': performer.get('spotify_link'),
                'city': event['_embedded']['venues'][0]['city']['name'],
                'state': event['_embedded']['venues'][0]['state']['name'],
                'address': event['_embedded']['venues'][0]['address']['line1'],
                'spotify_id': performer.get('spotify_id')
                
            }

            return event_info
    else:
        return "Event not found", 404
    
def get_spotify_artist_link(artist_name):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=SCOPE))
    results = []
    results = sp.search(q=artist_name, limit=1)
    if results['tracks']['items']:
        artist_id = results['tracks']['items'][0]['artists'][0]['id']
        return f"https://open.spotify.com/artist/{artist_id}"
    return None
    
if __name__ == "__main__":
    app.run(debug=True, port=5001)