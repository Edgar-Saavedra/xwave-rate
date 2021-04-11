#!/usr/bin/env python
# https://www.discogs.com/developers#page:database,header:database-search
# https://github.com/joalla/discogs_client/blob/master/discogs_client/client.py
# https://docs.python-guide.org/scenarios/scrape/
# https://developers.google.com/sheets/api/quickstart/python
from __future__ import print_function
import grequests
import os.path
from googleapiclient import discovery
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from lxml import html
import inquirer
import json
import discogs_client
from googleapiclient.errors import HttpError
import pprint

# https://developers.google.com/sheets/api/reference/rest?apix=true
# If modifying these scopes, delete the file token.json.
SCOPES_MULTIPLE = [
  'https://www.googleapis.com/auth/spreadsheets',
  'https://www.googleapis.com/auth/youtube.force-ssl'
]
SCOPES_WRITE = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = ''
# https://developers.google.com/sheets/api/guides/concepts
# Some API methods require a range in A1 notation. This is a string like Sheet1!A1:B2, that refers to a group of cells in the spreadsheet, and is typically used in formulas. For example, valid ranges are:

# Sheet1!A1:B2 refers to the first two cells in the top two rows of Sheet1.
# Sheet1!A:A refers to all the cells in the first column of Sheet1.
# Sheet1!1:2 refers to all the cells in the first two rows of Sheet1.
# Sheet1!A5:A refers to all the cells of the first column of Sheet 1, from row 5 onward.
# A1:B2 refers to the first two cells in the top two rows of the first visible sheet.
# Sheet1 refers to all the cells in Sheet1.
SAMPLE_RANGE_NAME = 'Sheet1'
CURRENTLY_PLAYING = 'http://xwaveradio.org/wp-content/plugins/shoutcast/now-playing.php'

def readSheetRow(row):
  print(row)
  # Print columns A and E, which correspond to indices 0 and 4.
  # print('%s, %s' % (row[0], row[4]))

def getCredentials(scopes = [], existingTokensFile = 'token.json', refresh = False):
  creds = None
  if os.path.exists(existingTokensFile):
      creds = Credentials.from_authorized_user_file(existingTokensFile, scopes)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid or refresh:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          'credentials.json', scopes)
      creds = flow.run_local_server()
    # Save the credentials for the next run
    with open(existingTokensFile, 'w') as token:
      token.write(creds.to_json())

  return creds

def callGoogleAPI(scopes=[], api='sheets', version='v4', refresh=False):
  creds = getCredentials(scopes=scopes, refresh=refresh)
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  # https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery.Resource-class.html

  # Call the Sheets API
  return discovery.build(api, version, credentials=creds)

def readSheets(sheetID=SAMPLE_SPREADSHEET_ID, sheetRange = SAMPLE_RANGE_NAME):
  service = callGoogleAPI(scopes=SCOPES_MULTIPLE)
  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheetID,
                              range=sheetRange).execute()
  values = result.get('values', )
  if not values:
      print('No data found.')
  else:
      print('Title, Rating:')
      for row in values:
        readSheetRow(row)

def onSuccess(saveValues=[], sheetID=SAMPLE_SPREADSHEET_ID, sheetRange = SAMPLE_RANGE_NAME):
  writeSheets(value=saveValues, sheetID=sheetID, sheetRange = sheetRange)
  # readSheets()

def writeSheets(value = [], sheetID=SAMPLE_SPREADSHEET_ID, sheetRange = SAMPLE_RANGE_NAME):
  service = callGoogleAPI(scopes=SCOPES_MULTIPLE)
  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheetID,
                              range=sheetRange).execute()
  songExist = False
  for row in result['values']:
    if row[0] == value[0]:
      songExist = True

  if not songExist:
    value.append(' , '.join([str(elem) for elem in searchYoutube(value)]))
    result['values'].append(value)
    # # The A1 notation of a range to search for a logical table of data.
    # # Values will be appended after the last row of the table.
    range_ = result['range']  # TODO: Update placeholder value.

    # # How the input data should be interpreted.
    value_input_option = 'USER_ENTERED'  # TODO: Update placeholder value. ['INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED']

    # # How the input data should be inserted.
    insert_data_option = 'INSERT_ROWS'  # TODO: Update placeholder value. ['OVERWRITE', 'INSERT_ROWS']

    request = service.spreadsheets().values().update(spreadsheetId=sheetID, range=range_, valueInputOption=value_input_option, body=result)
    response = request.execute()


    print(response)
  else:
      print('======================================')
      print("Song Found!")
      print(f"{value[0]}")
      print('======================================')


def searchYoutube(value=[]):
  # https://developers.google.com/youtube/v3/docs/search/list?hl=en&apix_params=%7B%22part%22%3A%5B%22testing%22%2C%22part%202%20asf%22%5D%7D
  youtubeLinks = []
  creds = getCredentials(scopes=SCOPES_MULTIPLE);
  youtube = discovery.build(
        'youtube', 'v3', credentials=creds)
  try :
    request = youtube.search().list(
      part='snippet',
      q=f"{value[0]} song"
    )
    response = request.execute()
    if(len(response['items'])):
      pp = pprint.PrettyPrinter(indent=4)
      for video in response['items']:
        if 'videoId' in video['id']:
          print("\n\n\n")
          pp.pprint(video)
          youtubeLinks.append(f"https://youtube.com/watch?v={video['id']['videoId']}")
          print("\n\n\n")
  except HttpError as err:
    print("\n\n\n")
    print(" Error with youtube! ")
    print(err._get_reason())
    print("\n\n\n")

  return youtubeLinks


def responseCallback(res):
  if res.status_code == 200:
    if os.path.exists('token.json'):
      with open('private.data.json') as f:
        data = json.load(f)
      # parser.feed(res.content)
      xml = html.fromstring(res.content)
      # print(xml.find('div').itertext())
      song = '';
      for text in xml.find('div').itertext() :
        if (text != 'Now Playing'):
          song += text

      questions = [
        inquirer.List('rating',
          message="This song is a >>",
          choices= range(10, 0, -1),
        ),
        inquirer.List('language',
          message="What's The Language???",
          choices=["English", "Español", "Deustch", "Français", "Greek", "Russian", "Instrumental", "Other"],
        ),
        inquirer.List('dance',
          message="Is This Dancable???",
          choices=[0, 1],
        ),
        inquirer.List('non-dude',
          message="Non Dude Voice???",
          choices=[0, 1],
        ),
        inquirer.List('genre',
          message="Genre???",
          choices=[
            "Punk",
            "Post-Punk",
            "Synth",
            "Synth-Punk",
            "Goth",
            "Electronic",
            "Deathrock",
            "Minimal",
            "Rockabilly",
            "Shoegaze",
            "Metal",
            "Pop",
            "Pyschobilly",
            "Alternative",
            "Other"
          ],
        ),
      ]

      inquire = inquirer.prompt(questions)
      feelz = input("This song makes me feel >> ")

      if (len(song) > 0):
        params = {
          "q": song,
          "key": data['discogKey'],
          "secret": data['discogSecrete']
        }

        # https://www.discogs.com/developers
        rs = (grequests.get(u, params=params) for u in ['https://api.discogs.com/database/search'])

        labels = ""
        year = ""
        discogs_url = ""
        country = ""
        album = ""

        for response in grequests.map(rs):
          results = response.json()['results']
          if (len(results) > 0):
            index = 0
            print(results[index])
            labels = ', '.join([str(elem) for elem in results[index]['label']])
            if 'year' in results[index]:
              year = results[index]['year']
            country = results[index]['country']
            discogs_url = f"https://www.discogs.com/{results[index]['uri']}"


        onSuccess(saveValues=[
          song,
          inquire['rating'],
          feelz,
          inquire['language'],
          inquire['dance'],
          inquire['non-dude'],
          inquire['genre'],
          labels,
          year,
          country,
          discogs_url,
        ],
        sheetID=data['spreadSheedId'])


def main():
  urls = [
    CURRENTLY_PLAYING
  ]
  rs = (grequests.get(u) for u in urls)

  for response in grequests.map(rs):
    responseCallback(response)

if __name__ == '__main__':
    main()