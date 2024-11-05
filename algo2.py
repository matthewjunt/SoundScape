import json
from fuzzywuzzy import fuzz

# Load Spotify data 
def load_spotify_data(spotify_file='spotify_data.json'):
    with open(spotify_file, 'r') as f:
        return json.load(f)

def load_ticketmaster_data(ticketmaster_file='ticketmaster_events_data.json'):
    with open(ticketmaster_file, 'r') as f:
        return json.load(f)['events']

def calculate_genre_scores(event_info, spotify_data):
    spotify_genres = spotify_data.get('Top Genres', [])[:20]
    spotify_artists = spotify_data.get('Top Artists', [])

    genre_weights = {genre: (20 - i / 2) / 20 for i, genre in enumerate(spotify_genres)}
    scores = []

    # Check for direct artist match
    for artist in spotify_artists:
        if artist["Artist Name"] in event_info['Headliners'] or artist["Artist Name"] in event_info['Supporting Acts']:
            # Exact artist match gets the highest score
            return 1.0  

    # If no artist match, calculate based on genre
    for genre in event_info.get('Genres', []) + event_info.get('Subgenres', []):
        if genre in genre_weights:
            scores.append(genre_weights[genre])
        else:
            for spotify_genre in spotify_genres:
                partial_match_score = fuzz.partial_ratio(genre.lower(), spotify_genre.lower()) / 100
                scores.append(partial_match_score * genre_weights.get(spotify_genre, 0))

    return sum(scores) / len(scores) if scores else 0.0

def calculate_final_score(event_info, spotify_data):
    genre_score = calculate_genre_scores(event_info, spotify_data)
    distance_score = event_info.get('Venue', {}).get('Distance', 1.0) 
    # Normalize distance score
    distance_score = (distance_score - 0.1) / (10 - 0.1)
    return 0.9 * genre_score + 0.1 * (1 - distance_score)

def rank_events(ticketmaster_data, spotify_data):
    ranked_events = []
    for event in ticketmaster_data:
        final_score = calculate_final_score(event, spotify_data)
        event_details = {
            'Event Name': event['Event Name'],
            'Artists': event['Headliners'] + event['Supporting Acts'],
            'Genres': event['Genres'] + event.get('Subgenres', []),
            'Date': event.get('Date and Time'),
            'Location': event['Venue']['City'] + ', ' + event['Venue']['State'],
            'Address': event['Venue']['Address'],
            'Distance': event['Venue'].get('Distance', 'N/A'),
            'Similarity Score': final_score,
            
        }
        ranked_events.append(event_details)

    ranked_events.sort(key=lambda x: x['Similarity Score'], reverse=True)
    return ranked_events[:20]

def save_ranked_events(ranked_events, output_file='ranked_events.json'):
    with open(output_file, 'w') as f:
        json.dump(ranked_events, f, indent=4)

if __name__ == "__main__":
    spotify_data = load_spotify_data()
    ticketmaster_data = load_ticketmaster_data()

    ranked_events = rank_events(ticketmaster_data, spotify_data)
    save_ranked_events(ranked_events)

    # Optional: Print the top 20 ranked events
    # for event in ranked_events:
    #     print(f"{event['Event Name']}: {event['Similarity Score']}")

