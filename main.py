import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'kdufi46-qyvemf489-nvkfwf82'

SITE = "http://localhost:5000"

CLIENT_ID = '6676a4e7136b4a6193cd30dcebbcc4f3'
CLIENT_SECRET = '3c7a99cd3e56483ebd5651ed50265413'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
  return "Welcome to my Spotify App! <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
  scope = 'user-read-private user-read-email'
  params = {
    'client_id': CLIENT_ID,
    'response_type': 'code',
    'scope': scope,
    'redirect_uri': REDIRECT_URI,
    'show_dialog': False        # set to True for debugging
  }

  auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
  return redirect(auth_url)

@app.route('/callback')
def callback():
  if 'error' in request.args: # error handling
    if request.args['error'] == 'access_denied':
      return redirect(SITE + '/denied') # Redirect to a custom error page
    return SITE # error page -> jsonify({'error': request.args['error']})
  
  if 'code' in request.args:
    req_body = {
      'code': request.args['code'],
      'grant_type': 'authorization_code',
      'redirect_uri': REDIRECT_URI,
      'client_id': CLIENT_ID,
      'client_secret': CLIENT_SECRET
    }
    
    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in'] # 3600 - token expires after 1 day
    return redirect('/playlists')

# Get user's playlists' info
@app.route('/playlists')
def get_playlists():
  if 'access_token' not in session: # error handling
    return redirect('/login')

  if datetime.now().timestamp() > session['expires_at']:
    return redirect('refresh-token')
  
  headers = {
    'Authorization': f"Bearer {session['access_token']}"
  }

  # Playlists retrieved per request
  limit = 50
  offset = 0 if 'offset' not in request.args else int(request.args['offset'])

  params = {
    'limit': limit,
    'offset': offset
  }

  response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
  playlists = response.json()

  # Update the offset for the next request
  next_offset = offset + limit

  # Check if there are more playlists to retrieve
  if len(playlists['items']) == limit:
    # If there are more playlists, include the next_offset in the redirect URL
    return redirect(f'/playlists?offset={next_offset}')
  return jsonify(playlists)

@app.route('/refresh-token')
def refresh_token():
  if 'refresh_token' not in session:
    return redirect('/login')
  
  if datetime.now().timestamp() > session['expires_at']:
    req_body = {
      'grant_type': 'refresh_token',
      'refresh_token': session['refresh_token'],
      'client_id': CLIENT_ID,
      'client_secret': CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlists')

if __name__ == '__main__':
  app.run(host='0.0.0.0', debug=True)


# Creating playlists
# current time & date
curr_td = datetime.now()
# formated time & date in the form "5:06 PM 12/19/2023"
formatted_td = curr_td.strftime('%I:%M %p %m/%d%Y')

# Clean playlist
@app.route('/get_playlist/<playlist_id>')
def get_playlist(playlist_id):
  headers = {
    'Authorization': f"Bearer {session['access_token']}",
  }
  response = requests.get(f"{API_BASE_URL}/playlists/{playlist_id}/tracks", headers=headers)
  data = response.json()
  clean_tracks = [item for item in data['items'] if not item['track']['explicit']]
  return jsonify(clean_tracks)

@app.route('/create_clean_playlist/<playlist_id>')
def create_clean_playlist(playlist_id):
  # Get clean tracks from the original playlist
  clean_tracks = get_playlist(playlist_id)

  # Get the original playlist name
  headers = {
    'Authorization': f"Bearer {session['access_token']}",
    'Content-Type': 'application/json',
  }
  response = requests.get(f"{API_BASE_URL}/playlists/{playlist_id}", headers=headers)
  data = response.json()
  playlist_name = data['name']

  # Create a new playlist
  payload = {
    'name': f'[Clean] {playlist_name}',
    'description': f'A playlist with only clean songs from {playlist_name}. {formatted_td}',
    'public': True
  }
  response = requests.post(f'{API_BASE_URL}/users/{session["user_id"]}/playlists', headers=headers, json=payload)
  new_playlist = response.json()

  # Add clean tracks to the new playlist
  # track_uris = [track['track']['uri'] for track in clean_tracks]
  # requests.post(f"{API_BASE_URL}/playlists/{new_playlist['id']}/tracks", headers=headers, json={'uris': track_uris})

  # return redirect(f"/playlists/{new_playlist['id']}")

    # Add the clean tracks to the new playlist
  payload = {
    'uris': clean_tracks,
  }
  response = requests.post(f"{API_BASE_URL}/playlists/{new_playlist['id']}/tracks", headers=headers, json=payload)

  return new_playlist
