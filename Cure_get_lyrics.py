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


def song_list_generator(era_url_list):
    ''' Creating list of songs for The Cure from thecure.com
        Input: era_url_list     list of strings, urls for eras on thecure.com
        Output: song_list       list of strings, list containing all songs with
                                  lyrics for The Cure on thecure.com
    '''
    all_song_list = []
    for era_url in era_url_list:
        # Creating a PoolManager, which is an abstraction for a container for a
        #   collection of connections to the host
        http = urllib3.PoolManager()

        # Make a request to the host
        response  = http.request('GET', era_url)

        # If request succeeded, proceed with song list generation
        if response.status == 200:

            # Using BeautifulSoup to store parse html from era_url page
            soup = bs(response.data, 'html.parser')

            # Find all song listings on the page
            song_list = soup.findAll("h3")[1:]

            # Convert individual songs from BeautifulSoup objects to strings
            song_list = [str(i) for i in song_list]

            # Removing unneeded text from song listings and saving to temporary list
            temp = []
            for song in song_list:
                song = song.replace("<h3>", "")\
                           .replace("</h3>", "")
                temp.append(song)

            # Copying temporary list back to song_list
            all_song_list.append(temp)

            # Call function to grab lyrics to put into MongoDB
            scrape_lyrics(era_url_list)

            # Sleep a bit so don't get kicked out of website
            sleep(5)

        # If request not successful, print error message to screen
        else:
            print "URLError: The server could not be found!"

    all_song_list = [item for sublist in all_song_list for item in sublist]
    return all_song_list



def scrape_lyrics(era_url_list):
    ''' Scraping lyrics from all songs listed for The Cure on thecure.com
        Input:  era_url_list  list of strings, list of url lists for eras
        Output: collection    MongoDB, containing lyrics only
    '''
    # Creating mongo database_name & collection_name
    database_name = 'The_Cure'
    collection_name = 'lyrics'

    # Loop through to get some lyrics for each song
    for era in era_url_list:

        # Creating a PoolManager, which is an abstraction for a container for a
        #   collection of connections to the host
        http = urllib3.PoolManager()

        # Making sure to have enough time between requests so not hitting
        #   max requests to website
        response = ""
        while response == "":
            try:
                # Make a request to the host
                response  = http.request('GET', lyrics_url)
            except:
                # Print messages to screen and sleep for 5 seconds and try again
                print "Connection refused by the server."
                print "Sleeping for 5 seconds."
                sleep(5)
                print "Continuing"
                continue

        # If request succeeded, proceed with lyric scraping
        if response.status == 200:

            # Using BeautifulSoup to store era_url page as lxml
            lyrics_soup  = bs(response.data, "lxml")

            # Find all song lyrics on the page
            lyrics = lyrics_soup.findAll("div", attrs={"class": None, \
                                                          "id": None})

            # Removing unneeded text from lyric listing
            lyrics = str(lyrics).replace("[<div>\\n<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->", "")\
                                .replace("\\r\\n", " ")\
                                .replace("<br / >"," ")\
                                .replace("<br/>", " ")\
                                .replace("\\n", " ")\
                                .replace("</div>]", "")\
                                .replace("  ", " ")\
                                .lower()

            # Format song and lyrics pymongo-style
            song_lyrics = {song: lyrics}

            # Insert song and lyrics into mongo database
            # if db
            db_insert_lyrics(database_name, collection_name, song, song_lyrics)

        else:
            error_message = "Lyrics could not be found"
            db_insert_lyrics(database_name, collection_name, song, \
                             error_message)

        sleep(5)
    # return collection for further QC
    collection = connect_to_mongo(database_name, collection_name)
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


def db_insert_lyrics(database_name, collection_name, lyrics):
    ''' Insert lyrics for song into MongoDB table
        Input: database_name    string, MongoDB database name to insert into
               collection name  string, MongoDB collection name to insert into
               lyrics           string, lyrics to insert into MongoDB
        Output: None, collection is just updated
    '''
    # Connect to and initialize mongo database
    collection = connect_to_mongo(database_name,collection_name)

    # Insert new song lyrics into mongo database
    collection.insert_one({song : lyrics})


def lyrics_to_csv(collection, band, query=None):
    ''' Output lyric collection for band to csv file
        Input: collection   string, MongoDB collection name to write out to csv
               band         string, band name
               query        Should the collection first be queried?
        Output: None, write out lyrics df to csv file for later importation
                      into sentiment analysis python script
    '''
    if query == None:
        query = collection.find()

    # Put mongo database into a dataframe and output to csv file
    df =  pd.DataFrame(list(query))

    # Outputting df to csv
    df.to_csv('{}_lyrics.csv'.format(band))


# def lemmatize_lyrics(lyrics, stop_words):
#     # Remove punctutation
#     lyrics = unicode(lyrics.translate(None, punctutation))
#
#     # Run the lyrics through spaCy
#     lyrics = nlp(lyrics)
#
#     # Lemmatize lyrics
#     tokens = [token.lemma_ for token in lyrics]
#
#     return ' '.join(word for word in tokens if word not in stop_words)


if __name__ == '__main__':
    # Using The Cure's official website to grab song lyrics (azlyrics.com keeps
    #   kicking me out for too many requests)
    era_list = ['1978-1979', '1980', '1981-1982', '1983-1984', '1985-1987', '1988-1990', '1991-1993', '1994-2004', '2005-2009']

    # Calling function to create band url for thecure.com
    era_url_list = era_url_generator(era_list)

    # Calling function to create song lyric url for azlyrics.com
    song_list = song_list_generator(era_url_list)

    # Scraping song lyrics from azlyrics.com and inserting into mongo
    #   database
    collection = scrape_lyrics(band, song_list)

    # Outputting lyrics to csv file
    # lyrics_to_csv(collection, band)

''' Mongo code to join albums to songs
db.albums.aggregate([ {$lookup:      {       from: 'songs',       localField: 'song',       foreignField: 'song',       as: 'song'      } } ]).pretty()
'''