import json
from fuzzywuzzy import fuzz

# Load Spotify data 
def load_spotify_data(spotify_file='spotify_data.json'):
    with open(spotify_file, 'r') as f:
        return json.load(f)

# Load Ticketmaster data
def load_ticketmaster_data(ticketmaster_file='ticketmaster_events_data.json'):
    with open(ticketmaster_file, 'r') as f:
        return json.load(f)['events']

# Calculate genre scores based on event and Spotify data
def calculate_genre_scores(event_info, spotify_data):
    # Get top genres and artists from Spotify data
    spotify_genres = spotify_data.get('Top Genres', [])[:20]
    spotify_artists = spotify_data.get('Top Artists', [])

    # Assign weights to genres based on user ranking
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
            # Calculate partial match score for genre based on genre similarity
            for spotify_genre in spotify_genres:
                partial_match_score = fuzz.partial_ratio(genre.lower(), spotify_genre.lower()) / 100
                scores.append(partial_match_score * genre_weights.get(spotify_genre, 0))

    return sum(scores) / len(scores) if scores else 0.0

# Calculate final score based on genre scores and distance
def calculate_final_score(event_info, spotify_data):
    genre_score = calculate_genre_scores(event_info, spotify_data)
    # Get distance score from event data
    distance_score = event_info.get('Venue', {}).get('Distance', 1.0) 
    # Normalize distance score
    distance_score = (distance_score - 0.1) / (10 - 0.1)
    # Combine genre score and distance score with custom weights
    return 0.9 * genre_score + 0.1 * (1 - distance_score)

# Rank events based on similarity to user preferences
def rank_events(ticketmaster_data, spotify_data):
    ranked_events = []
    # Keep track of seen event names to avoid duplicates
    seen_event_names = set()  

    for event in ticketmaster_data:
        event_name = event['Event Name']
        
        # Skip duplicates
        if event_name in seen_event_names:
            continue
        
        seen_event_names.add(event_name) 
        final_score = calculate_final_score(event, spotify_data)
        event_details = {
            'Event Name': event_name,
            'Artists': event['Headliners'] + event['Supporting Acts'],
            'Genres': event['Genres'] + event.get('Subgenres', []),
            'Date': event.get('Date and Time'),
            'Location': event['Venue']['City'] + ', ' + event['Venue']['State'],
            'Address': event['Venue']['Address'],
            'Distance': event['Venue'].get('Distance', 'N/A'),
            'Similarity Score': final_score,
        }
        ranked_events.append(event_details)

    # Sort events by similarity score
    ranked_events.sort(key=lambda x: x['Similarity Score'], reverse=True)
    # Return top 20 ranked events
    return ranked_events[:20]

# Save ranked events to a JSON file
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
