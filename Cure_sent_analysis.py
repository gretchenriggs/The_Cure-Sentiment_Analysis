import requests
from bs4 import BeautifulSoup as bs
import urllib3.request
from pymongo import MongoClient
import sys
# import spacy
from time import sleep
import pandas as pd

# Load spacy.en if not loaded already
# If using ipython, execute script using %run -i my_file.py to avoid
#   repeatedly loading in the English module
# if not 'nlp' in locals():
#     print("Loading English Module...")
#     nlp = spacy.load('en')


def band_url_generator(band):
    ''' Creating band's url page name on azlyrics.com
        Input:  band      string, raw input from user
        Output: band      string, reformatted band name
                band_url  string, band url on azlyrics.com
    '''
    # Format band name as lower case with no space and if band name starts
    #   with "the", remove it
    band = band.lower()
    if band.split(" ")[0] == "the":
        band = band[4:]
    band = band.replace(" ", "")
    # Generate band_url for page on azlyrics.com containing all band's
    #   songs
    band_url = "http://www.azlyrics.com/[first_letter]/[band].html"
    band_url = band_url.replace("[first_letter]", band[0])\
                       .replace('[band]', band)\
                       .replace(" ", "")
    return band, band_url


def song_list_generator(band_url):
    ''' Creating list of songs for band from azlyrics.com
        Input: band_url     string, url for band on azlyrics.com
        Output: song_list   list of strings, list containing all songs with
                                  lyrics for specified band on azlyrics.com
    '''
    # Creating a PoolManager, which is an abstraction for a container for a
    #   collection of connections to the host
    http = urllib3.PoolManager()

    # Make a request to the host
    response  = http.request('GET', band_url)

    # If request succeeded, proceed with song list generation
    if response.status == 200:

        # Using BeautifulSoup to store band_url page as lxml
        soup  = bs(response.data, "lxml")

        # Find all song listings on the page
        song_list = soup.findAll("a")[31:][:-10 or None]

        # Convert individual songs from BeautifulSoup objects to strings
        song_list = [str(i) for i in song_list]

        # Removing unneeded text from song listings and saving to temporary list
        temp = []
        for song in song_list:
            if '<a href="../lyrics/' in song:
                song = song.replace("</a>", " ")\
                .split(" ")[1]\
                .replace('href="../lyrics/', '')\
                .replace(band, "")\
                .replace("/", "")\
                .replace('.html"', '')
                temp.append(song)

        # Copying temporary list back to song_list
        song_list = temp
        return song_list

    # If request not successful, print error message to screen
    else:
        print "URLError: The server could not be found!"


def scrape_lyrics(band, song_list):
    ''' Scraping lyrics from all songs listed for band on azlyrics.com
        Input: band          string, band name
               song_list     list of strings, list of song names
        Output: collection   MongoDB, containing song names and lyrics
    '''
    # Creating mongo database_name & collection_name
    database_name = band +'_lyrics'
    collection_name = 'lyrics'

    # Loop through to get some lyrics for each song
    for song in song_list:
        lyrics_url = "http://www.azlyrics.com/lyrics/[band]/[song].html"
        lyrics_url = lyrics_url.replace("[band]", band)\
                               .replace('[song]', song)

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

            # Using BeautifulSoup to store band_url page as lxml
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

    # Prompt user for band name
    band = raw_input("Enter a band name: ")

    # Calling function to create band url for azlyrics.com
    band, band_url = band_url_generator(band)

    # Calling function to create song lyric url for azlyrics.com
    song_list = song_list_generator(band_url)

    # Scraping song lyrics from azlyrics.com and inserting into mongo
    #   database
    collection = scrape_lyrics(band, song_list)

    # Outputting lyrics to csv file
    # lyrics_to_csv(collection, band)
