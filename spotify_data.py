import os
import json
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import numpy as np
from collections import Counter

# Spotify API credentials 
CLIENT_ID = 'f5f05bb707634304ba73ffe617c9db74'
CLIENT_SECRET = 'e079e909e4394145bf75ab21317e2911'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-top-read'

# Function to get user's top tracks
def get_top_tracks(sp):
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term')
    tracks_data = []
    
    for track in top_tracks['items']:
        track_info = {
            'Track Name': track['name'],
            'Artists': [artist['name'] for artist in track['artists']],
            'Genres': []
        }
        
        # Fetch genre for each artist
        for artist in track['artists']:
            if artist.get('id'):
                try:
                    artist_info = sp.artist(artist['id'])
                    track_info['Genres'].extend(artist_info.get('genres', []))
                except Exception as e:
                    print(f"Error fetching genre for artist {artist['name']}: {e}")
        
        tracks_data.append(track_info)
    
    return tracks_data

# Function to get user's top artists
def get_top_artists(sp):
    top_artists = sp.current_user_top_artists(limit=50, time_range='long_term')
    artists_data = []
    
    for artist in top_artists['items']:
        artist_info = {
            'Artist Name': artist['name'],
            'Genres': artist.get('genres', [])
        }
        artists_data.append(artist_info)
    
    return artists_data

# Function to calculate genre vector
def calculate_genre_vector(tracks_data, artists_data):
    all_genres = []
    
    # Collect genres from top tracks
    for track in tracks_data:
        all_genres.extend(track['Genres'])
    
    # Collect genres from top artists
    for artist in artists_data:
        all_genres.extend(artist['Genres'])
    
    # Count the occurrences of each genre
    genre_counts = Counter(all_genres)
    
    # Select the top 20 genres
    top_genres = genre_counts.most_common(20)
    top_genre_names = [genre for genre, count in top_genres]
    
    # Create a genre vector
    genre_vector = np.zeros(len(top_genre_names))
    for i, genre in enumerate(top_genre_names):
        genre_vector[i] = genre_counts[genre]
    
    # Normalize the vector
    if np.linalg.norm(genre_vector) != 0:
        genre_vector /= np.linalg.norm(genre_vector)
    
    return genre_vector, top_genre_names

# Main function to get and save the data
def main():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=SCOPE))

    # Get user data
    top_tracks = get_top_tracks(sp)
    top_artists = get_top_artists(sp)

    # Calculate genre vector
    genre_vector, top_genres = calculate_genre_vector(top_tracks, top_artists)

    # Save data to file
    data = {
        'Top Tracks': top_tracks,
        'Top Artists': top_artists,
        'Top Genres': top_genres,
        'Genre Vector': genre_vector.tolist()
    }
    
    with open('spotify_data.json', 'w') as f:
        json.dump(data, f, indent=4)

    print("Data saved to spotify_data.json")

if __name__ == '__main__':
    main()
