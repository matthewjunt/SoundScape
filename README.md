# SoundScape: Event Recommendation System

This program integrates data from Spotify and Ticketmaster to recommend concerts and music events based on user listening history. It retrieves the user's top tracks and artists from Spotify, then fetches relevant events from Ticketmaster based on location. The events are ranked according to their similarity to the user's music preferences.

## Contents

1. **File Descriptions**
   - `spotify_data.py`: This file fetches the user's top tracks and artists from Spotify using the Spotify API and saves the data in a JSON file.
   - `app.py`: This file runs the application, handles page routing, retrieves the events from ticketmaster, and handles the rest of the backend functions.
   - `algorithm.py`: This file processes the data obtained from the previous files, calculates similarity scores between Spotify genres and Ticketmaster events, and ranks the events based on that score and the distance

2. **Data Files**
   - `spotify_data.json`: Contains the user's top tracks, top artists, top genres, and a normalized genre vector derived from the user's music preferences.
   - `ticketmaster_events_data.json`: Contains event details fetched from Ticketmaster, including event names, venues, dates, genres, and artists performing.
   - `ranked_events.json`: Contains the top-ranked events based on similarity to the user's preferences, including the similarity score for each event.

3. **How To Run**
   - With your own Spotify Login/Data
      - Replace the spotify developer credentials of Client Secret and Client ID in `spotify_data.py`
      - Run the command `python3 app.py` and login to your spotify upon searching on the webpage
      - Note: You will not be able to login with your spotify using my Client Secret/ID since my Spotify Developer account is still in "Development" status, requiring me to add allowed users manually. 
      - Continue with the rest of the instructions below
   - Without your own Spotify Login/Data (using my own data that is in the `spotify_data.json` file)
      - Comment out lines 97 and 98 in app.py, in order to not get an error from trying to retrieve spotify data without the client secret.
      - Run the command `python3 app.py`, go to the localhost web url and input location, date range, and select either genre search or automatic spotify search. 
      - Note: My data file, `ticketmaster_events_data.json`, uses the location of Dallas.
      - Note: larger cities (such as Houston, Dallas, etc) work better currently as I am still refining the location weighting
      - The top 20 ranked events will be saved to `ranked_events.json`.

4. **Notes**
   - While this algorithm is complete and works correctly, I may do some more refining of it based on user testing with different accounts. I am currently using my own ranking algorithm based on genre weights, artist matches, and distance calculation. However, I may implement a cosine similarity function in the future. 
   - I have had limited ability to test this with multiple accounts, since I only have one spotify account. I did test it on one other account from a friend, but that is the extent so far that I have been able to test. 
   
## Dependencies

To run this program you will need these Python packages:
- `requests`: For making HTTP requests to APIs.
- `spotipy`: For accessing the Spotify Web API.
- `numpy`: For numerical operations and handling arrays.
- `collections`: For counting and organizing data.
- `fuzzywuzzy`: For string similarity matching.
- `geopy`: For location processing.
- `flask`: For backend processing.
- `geohash`: For location processing. 

You can install these dependencies using pip:

```bash
pip install requests spotipy numpy fuzzywuzzy geopy flask geohash

```

