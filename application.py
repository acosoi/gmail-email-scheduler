from __future__ import print_function
import configparser
import csv
import dateparser
import datetime
import pickle
import pytz
import os.path
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request



# if modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.compose']

# configuration variables, will be set later on
MAIN_LOOP_DELAY = 60
SCHEDULE_CSV_PATH = './schedule.csv'



# retrieve the subject from a message JSON or return None if not found
def getSubjectFromMessage(message):
    headers = message['payload']['headers']
    for header in headers:
        if (header['name'] == "Subject"):
            return header['value']
    return None

def readConfigIni():

    config = configparser.ConfigParser()
    config.read('config.ini')

    # how long to wait between main loop runs (in seconds)
    global MAIN_LOOP_DELAY
    MAIN_LOOP_DELAY = int(config['CONFIG']['MAIN_LOOP_DELAY'])

    # where to read the schedule.csv file from
    global SCHEDULE_CSV_PATH
    SCHEDULE_CSV_PATH = config['CONFIG']['SCHEDULE_CSV_PATH']

def main():

    # read the config ini file
    readConfigIni()

    creds = None

    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # if there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    print("gmail-scheduler started and connected to Google")
    print("Current time is " + str(datetime.datetime.now(pytz.timezone("Europe/Bucharest"))))

    # start out with no copy of the previous schedule
    oldSchedule = {}

    # we're done setting up the GMail service, begin the main program loop
    while True:

        # if anything fails, print out the exception but don't stop
        try:

            # reload the config ini, just in case any changes took place
            readConfigIni()

            # save the current time
            timezone = pytz.timezone("Europe/Bucharest")
            currentTime = datetime.datetime.now(timezone)

            # read schedule.csv and populate the schedule dictionary
            schedule = {}
            with open(SCHEDULE_CSV_PATH) as csvfile:
                csvreader = csv.reader(csvfile, delimiter='|')
                for row in csvreader:
                    if len(row) == 2:
                        schedule[row[0]] = row[1]

            # a dictionary of newly-scheduled e-mails that will be later verified if they exist
            verifyIfScheduled = {}

            # compare the new schedule to the old one
            for key in oldSchedule.keys():
                if key not in schedule:
                    print("Removed '" + key + "' from schedule.")
            for key in schedule.keys():
                if key not in oldSchedule:
                    print("Scheduled '" + key + "' to be sent at " + schedule[key])
                    verifyIfScheduled[key] = schedule[key]
            for key in schedule.keys():
                if key in oldSchedule and schedule[key] != oldSchedule[key]:
                    print("Rescheduled '" + key + "' from " + oldSchedule[key] + " to " + schedule[key])

            # store the schedule for the next comparison
            oldSchedule = schedule

            # retrieve a list of all saved drafts
            listDraftsResults = service.users().drafts().list(userId='me').execute()
            drafts = listDraftsResults.get('drafts', [])

            # process each draft
            for draft in drafts:

                draftId = str(draft['id'])

                # retrieve information about the draft
                getDraftResponse = service.users().drafts().get(userId='me', id=draftId).execute()

                # extract the subject from the response
                subject = getSubjectFromMessage(getDraftResponse['message'])

                # if we were expecting to find this e-mail, remove it from the list
                if subject in verifyIfScheduled:
                    verifyIfScheduled.pop(subject)

                # if we managed to extract the subject and it is scheduled
                if subject != None and subject in schedule.keys():

                    # retrieve when this e-mail should be sent and parse the information
                    timestamp = dateparser.parse(schedule[subject], settings={'TIMEZONE': 'Europe/Bucharest', 'RETURN_AS_TIMEZONE_AWARE': True})

                    # is it time to send the e-mail?
                    if (currentTime >= timestamp):

                        print("Sending '" + subject + "'...")
                        sendResult = service.users().drafts().send(userId='me', body={ 'id': draftId }).execute()
                        print("Sent!")

            # were we expecting to find certain e-mails but couldn't?
            for key in verifyIfScheduled.keys():
                print("Couldn't find a draft called '" + key + "', currently scheduled for " + schedule[key])

        # if anything went wrong, print it out
        except Exception as ex:
            print("ERROR! Exception encountered in main loop...")
            print(type(ex))
            print(ex)
            print(ex.args)
            print("Done printing exception!")

        # wait before running again
        time.sleep(MAIN_LOOP_DELAY)



if __name__ == '__main__':
    main()
