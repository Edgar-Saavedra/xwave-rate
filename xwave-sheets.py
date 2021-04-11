#!/usr/bin/env python
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

# https://developers.google.com/sheets/api/reference/rest?apix=true
# If modifying these scopes, delete the file token.json.
SCOPES_READ = ['https://www.googleapis.com/auth/spreadsheets.readonly']
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

def callGoogleAPI(scopes):
  """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.json'):
      creds = Credentials.from_authorized_user_file('token.json', scopes)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          'credentials.json', scopes)
      creds = flow.run_local_server()
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
      token.write(creds.to_json())
  # https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery.Resource-class.html

  # Call the Sheets API
  return discovery.build('sheets', 'v4', credentials=creds)

def readSheets(sheetID=SAMPLE_SPREADSHEET_ID, sheetRange = SAMPLE_RANGE_NAME):
  service = callGoogleAPI(SCOPES_READ)
  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheetID,
                              range=sheetRange).execute()
  values = result.get('values', [])
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
  service = callGoogleAPI(SCOPES_WRITE)
  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheetID,
                              range=sheetRange).execute()
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
          choices=["English", "Español", "Deustch", "Française", "Greek", "Russian", "Other"],
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
            "Goth",
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
        onSuccess(saveValues=[
          song,
          inquire['rating'],
          feelz,
          inquire['language'],
          inquire['dance'],
          inquire['non-dude'],
          inquire['genre'],
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