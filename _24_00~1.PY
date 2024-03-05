
# TODO: Remove ('Imprint/Promotion Label:', 'NEW')
# TODO: Env Var string in Settings
# TODO: Open in Spotify app first
# TODO: Add Vivaldi and then Google Chrome functionality, if Viv fails

import os
import subprocess
import shlex
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# constants and initial setup
# Extract environment variables
CLIENT_ID = os.environ.get('CLIENT_ID', 'Client ID does not exist')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'Client Secret does not exist')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'Redirect URI does not exist')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', 'Access Token does not exist')
USER = os.environ.get('USER', 'User does not exist')
scope = "playlist-modify-private"

print(f"The CLIENT_ID is: {CLIENT_ID}")
print(f"The CLIENT_SECRET is: {CLIENT_SECRET}")
print(f"The REDIRECT_URI is: {REDIRECT_URI}")
print(f"The ACCESS_TOKEN is: {ACCESS_TOKEN}")
print(f"The USER is: {USER}")

print("\nI have a secret... 🤫 I have access to a Magical JukeBox which can Time Travel to the day a song became popular.\n\nIn fact, we will create a Playlist for you, of the Top 100 Billboard Songs for that day.\n")
print("In the meantime while we are getting that all together for you, kindly pick a song to play while we wait for it to be ready!\n")
user_date_input = input("Please type a chosen date in this format: YYYY-MM-DD: ")

# spotipy setup for spotify web api access
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=scope))

# Fetch the current user's profile information
current_user = sp.current_user()
current_user_id = current_user['id']

print(current_user)
print(current_user_id)

# import logging
# logging.basicConfig(level=logging.DEBUG)

def fetch_songs_and_artists():
    response = requests.get(f"https://www.billboard.com/charts/hot-100/{user_date_input}/")
    if response.status_code != 200:
        print("Failed to retrieve data")
        exit()

    soup = BeautifulSoup(response.text, 'html.parser')
    songs_and_artists = []

    for element in soup.find_all(["h3", "span"], class_=["c-title", "c-label"]):
        if 'c-title' in element['class']:
            title_text = element.get_text(strip=True)
            current_title = title_text if title_text and all(keyword not in title_text for keyword in ['Songwriter', 'Producer']) else None
        elif 'c-label' in element['class'] and current_title:
            artist_name_text = element.get_text(strip=True)
            if all(char.isdigit() is False for char in artist_name_text):
                songs_and_artists.append((current_title, artist_name_text))
                current_title = None

    return songs_and_artists

def attempt_playback(track_uri, access_token):
    global data
    endpoint = "https://api.spotify.com/v1/me/player/play"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"uris": [track_uri]}

    response = requests.put(endpoint, headers=headers, json=data)
    if response.status_code == 204:
        print("Playback started successfully via Spotify Web API.")
    else:
        print("Failed to start playback via Web API, trying the desktop app...")
        try:
            subprocess.run(["spotify", "--uri=" + track_uri], check=True)
            print(f"Opening track in Spotify app...\n")
        except subprocess.CalledProcessError as e:
            print("Failed to open track in Spotify app:", e)

# main execution flow
songs_and_artists = fetch_songs_and_artists()
playlist_title_name = f"\nHOT 100 Billboard Songs from {user_date_input}:"
print(f"\n{playlist_title_name}")
for i, (song, artist) in enumerate(songs_and_artists, start=1):
    print(f"Song {i}: {song}, Artist {i}: {artist}")

found_song = False
while not found_song:
    user_selection = int(input("\nEnter the song number you wish to play: "))
    if 1 <= user_selection <= len(songs_and_artists):
        selected_song, selected_artist = songs_and_artists[user_selection - 1]
        query = f"track:{selected_song} artist:{selected_artist}"
        result = sp.search(q=query, type="track")

        if result['tracks']['items']:
            found_song = True
            track_url = result['tracks']['items'][0]['external_urls']['spotify']
            track_uri = result['tracks']['items'][0]['uri']
            escaped_track_url = shlex.quote(track_url)
            escaped_track_uri = shlex.quote(track_uri)
            print(f"The URL for this song is: {escaped_track_url}\n")  # print the spotify url
            print(f"The URI for this song is: {escaped_track_uri}\n")  # print the spotify uri

            # at top, replace 'your_spotify_access_token_here' with a valid access token:
            attempt_playback(escaped_track_url, ACCESS_TOKEN)
        else:
            print("Unfortunately, the song is not available right now. Please try another selection: ")
    else:
        print("Invalid selection. Please try again.")


#### Compiling a List of 100 songs for that day, made into a Spotify Playlist:
# songs_and_artists = fetch_songs_and_artists()
# print(f"\nSongs and Artists from {user_date_input}:")
# for i, (song, artist) in enumerate(songs_and_artists, start=1):
#     print(f"Song {i}: {song}, Artist {i}: {artist}")

named_Playlist_for_this_Searched_100 = []

URI_Playlist_for_this_Searched_100 = []


# paired_URI_song_data = song, artist
for iteration_number, (song, artist) in enumerate(songs_and_artists, start=1):   # this part is critical:  iteration_number, (song, artist)
    song_artist_data_pair = (song, artist)

    query = f"track:{song} artist:{artist}"
    result = sp.search(q=query, type="track")

    if result['tracks']['items']:
        #get the URI and append it with the song and artist
        # track_url = result['tracks']['items'][0]['external_urls']['spotify']
        track_uri = result['tracks']['items'][0]['uri']
        track_uri = shlex.quote(track_uri)

        named_Playlist_for_this_Searched_100.append((song, artist, track_uri))

        print(f"The URI for Song# {iteration_number}: {song_artist_data_pair} is: {track_uri}\n")  # print the spotify uri

        URI_Playlist_for_this_Searched_100.append(track_uri)


    else:  #in case there are no results found in a pair:
        named_Playlist_for_this_Searched_100.append((song, artist, None))


print(f"The added URIs are: {URI_Playlist_for_this_Searched_100}")

name = playlist_title_name
user_playlist_create = ""

# creates a playlist
playlist_response = sp.user_playlist_create(user=USER, name=name, public=False, collaborative=False, description="A playlist created by siris.Developer")
playlist_id = playlist_response['id']  # Extract the playlist ID from the response

# adds items to the playlist
sp.playlist_add_items(playlist_id=playlist_id, items=URI_Playlist_for_this_Searched_100)
