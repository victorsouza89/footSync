#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import webdriver
binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe')

import re, os, datetime, time, httplib2

with open('flashscore_links.txt') as file:
    lines = file.readlines()
    teams = [line.rstrip() for line in lines]

# scraping works in portuguese and english
separator = "Classificação|Standings|Live Standings"

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'syncFoot'

def main():
    # connect to google
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    # get now
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    
    # get the calendar we're gonna change
    futebol = None
    for c in service.calendarList().list().execute()['items']:
        try:
            if 'syncFoot' in c['description']:
                futebol = c['id']
        except:
            None

    if not futebol:
        calendar = {
            'summary': 'syncFoot',
            'description': 'syncFoot',
            'timeZone': 'America/Sao_Paulo'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        futebol = created_calendar['id']
    print(futebol)

    print('Starting...')
    # deletes listed upcoming events
    eventsResult = service.events().list(
        calendarId=futebol, timeMin=now, maxResults=500, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    if not events:
        print('No upcoming events found.')
    else:
        for event in events:
            print("Deleting", event['id'])
            service.events().delete(calendarId=futebol, eventId=event['id']).execute()

    # for each link
    for link_sport in teams:
        # Inicia        
        op = webdriver.FirefoxOptions()
        op.add_argument('-headless')
        profile = webdriver.FirefoxProfile()
        profile.set_preference("dom.disable_beforeunload", True)
        driver = webdriver.Firefox(
            firefox_binary=binary, executable_path=r'C:\\geckodriver.exe', options=op, firefox_profile=profile)
        driver.get(link_sport)


        # SCRAPING
        st = False
        while not st:
            time.sleep(0.5)
            print ("SEARCH")
            elem = driver.find_element_by_id("live-table").text
            if elem:
                st = True
                driver.close()
                scrape(elem, service, futebol)
                
def scrape(elem, service, futebol):
    elem = re.split("\n-", elem)
    comp = None
    for c in elem:
        print("--------------------")
        if c:
            c = re.split(separator, c)
            if len(c) > 1:
                comp = c[0]
            c = c[-1]
            j = c.splitlines()
            print(comp)
            print(j)
            data = re.split("\.\s*|:", j[1])
            data_ = datetime.datetime(datetime.date.today().year, int(data[1]), int(data[0]), int(data[2]), int(data[3]))
            present = datetime.datetime.now()
            if data_ < present:
                data_ = datetime.datetime(datetime.date.today().year + 1, int(data[1]), int(data[0]), int(data[2]), int(data[3]))
            dataFinal = data_ + datetime.timedelta(hours = 2)
            data_ = data_.strftime("%Y-%m-%dT%H:%M:00"+ gmt +":00")
            dataFinal = dataFinal.strftime("%Y-%m-%dT%H:%M:00"+ gmt +":00")
            mandante = j[2]
            visitante = j[3]
            confronto = mandante+" X "+visitante
            print (data_)
            print (dataFinal)

            event = {
            'summary': confronto,
            'description': comp,
            'start': {
            'dateTime': str(data_)
            },
            'end': {
            'dateTime': str(dataFinal)
            },
            'reminders': {
            'useDefault': False,
            }
            }
            event = service.events().insert(calendarId=futebol, body=event).execute()
            print ('Event created: %s' % (event.get('htmlLink')))
            print("\n\n")

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


# get and format gmt
t1 = datetime.datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "%Y-%m-%d %H:%M:%S")
t2 = datetime.datetime.strptime(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "%Y-%m-%d %H:%M:%S")
gmt = format(int((t1 - t2).total_seconds()/3600), '03d')
g, m, t = gmt
if g == '0':
    gmt = '+' + m + t

if __name__ == '__main__':
    main()
