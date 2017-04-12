import requests
from bs4 import BeautifulSoup as bs
import urllib3.request
from pymongo import MongoClient
import sys
from time import sleep
import pandas as pd


def era_url_generator(era_list):
    ''' Creating The Cure's era for lyrics url page name on thecure.com
        Input:  band      string, raw input from user
        Output: band      string, reformatted band name
                era_url  string, band url on azlyrics.com
    '''

    # Generate era_url list for pages on thecure.com containing all band's
    #   songs
    era_url_list = []
    for era in era_list:
        era_url = "http://www.thecure.com/words/[era]/"
        era_url = era_url.replace("[era]", era)
        era_url_list.append(era_url)
    return era_url_list


def song_list_generator(era_list, query=True):
    ''' Creating list of songs for The Cure from thecure.com
        Input: era_url_list     list of strings, urls for eras on thecure.com
        Output: song_list       list of strings, list containing all songs with
                                  lyrics for The Cure on thecure.com
    '''
    # Calling function to create band url for thecure.com
    era_url_list = era_url_generator(era_list)

    # Creating mongo database_name & collection_name
    database_name = 'The_Cure'
    collection_name = 'lyrics'

    # Check if database is already populated (non-empty)
    collection = connect_to_mongo(database_name, collection_name)

    if list(collection.find()) == []:
        all_song_list = []
        lineup_list = []
        for index, era_url in enumerate(era_url_list):
            # Saving era listing to 'era'
            era = era_list[index]

            # Creating a PoolManager, which is an abstraction for a container for a collection of connections to the host
            http = urllib3.PoolManager()

            # Make a request to the host
            response  = http.request('GET', era_url)

            # If request succeeded, proceed with song list generation
            if response.status == 200:

                # Using BeautifulSoup to store parse html from era_url page
                soup = bs(response.data, 'html.parser')

                lineup = str(soup.findAll("h4")[1])\
                             .replace("<h4>[", "")\
                             .replace(" Cure]</h4>", "")
                raw_song_with_lyrics = []
                temp = soup.get_text().split("\n \n")[2:-4]
                for i, item in enumerate(temp):
                    reformated_song_lyrics = str(temp[i].encode("ascii", "ignore"))\
                           .replace(" \n\n\n{0}\n\nAll Robert's words to all The Cure songs and more...\n\n\n"\
                           .format(era),"")\
                           .replace("[lineup]\n".replace("lineup", lineup), "")\
                           .replace("\r", "")\
                           .split("\n")

                    song = str(soup.findAll("h3")[i+1])\
                                   .replace("<h3>", "")\
                                   .replace("</h3>", "")
                    lyrics = reformated_song_lyrics[1:]
                    lyrics = " ".join(lyrics).lower()\
                                .replace("  ", " ")\
                                .replace("  ", " ")

                    # Format song and lyrics pymongo-style
                    all_lyrics = {'_era' : era,\
                                  '_song': song, \
                                  '_lyrics' : lyrics, \
                                  '_lineup' : lineup}

                    print i, item
                    print era, song
                    print lyrics


                    # Insert song and lyrics into mongo database
                    db_insert_lyrics(database_name, collection_name, all_lyrics)

                    # Return collection for further QC
                    collection = connect_to_mongo(database_name,\
                                                  collection_name)


                # If request not successful, print error message to screen
            else:
                print "URLError: The server could not be found!"

            # Sleep a bit so don't get kicked out of website
            sleep(5)

    return collection


def connect_to_mongo(database_name, collection_name):
    ''' Connect to Mongo database
        Input: database_name      string, MongoDB database name
               collection_name    string, MongoDB collection name
        Output: lyric_collection  database table, connecting to MongoDB table
    '''
    # Initial client to connect to mongo
    client = MongoClient()

    # Access/Initialize database
    database = client[database_name]

    # Access/Initialize Table
    lyric_collection = database[collection_name]
    return lyric_collection


def db_insert_lyrics(database_name, collection_name, all_lyrics):
    ''' Insert lyrics for song into MongoDB table
        Input: database_name    string, MongoDB database name to insert into
               collection name  string, MongoDB collection name to insert into
               lyrics           string, lyrics to insert into MongoDB
        Output: None, collection is just updated
    '''
    # Connect to and initialize mongo database
    collection = connect_to_mongo(database_name,collection_name)

    # Insert new song lyrics into mongo database
    collection.insert_one(all_lyrics)


if __name__ == '__main__':
    # Using The Cure's official website to grab song lyrics (azlyrics.com keeps
    #   kicking me out for too many requests)
    era_list = ['1978-1979', '1980', '1981-1982', '1983-1984', '1985-1987', '1988-1990', '1991-1993', '1994-2004', '2005-2009']

    # Calling function to create song list from thecure.com & store lyrics
    #   in MongoDB database by era : all_lyrics
    collection = song_list_generator(era_list)

    # Scraping song lyrics from azlyrics.com and inserting into mongo
    #   database
    # collection = scrape_lyrics(band, song_list)

    # Outputting lyrics to csv file
    # lyrics_to_csv(collection, band)

''' Mongo code to join albums to songs
db.albums.aggregate([ {$lookup:      {       from: 'songs',       localField: 'song',       foreignField: 'song',       as: 'song'      } } ]).pretty()
'''

''' Code to split songs on era page
g = soup.get_text().split("\n \n")
'''
