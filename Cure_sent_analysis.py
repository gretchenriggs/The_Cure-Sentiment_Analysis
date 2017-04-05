import requests
from bs4 import BeautifulSoup as bs
import urllib3.request
from pymongo import MongoClient


# Creating band's url page name on azlyrics.com
def band_url_generator(band):
    # Format band name to be all lower case and if band name starts with
    # "the", remove it
    band = band.lower()
    if band.split(" ")[0] == "the":
        band = band[4:]

        # Generate band_url for page on azlyrics.com containing all band's
        #   songs
        band_url = "http://www.azlyrics.com/[first_letter]/[band].html"
        band_url = band_url.replace("[first_letter]", band[0])\
        .replace('[band]', band)
    return band_url

def song_list_generator(band_url):
    # Creating a PoolManager, which is an abstraction for a container for a
    #   collection of connections to the host
    http = urllib3.PoolManager()

    # Make a request to the host
    response  = http.request('GET', band_url)

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


def scrape_lyrics(band, song_list):
    # Creating mongo database_name & collection_name
    database_name = band +'_lyrics'
    collection_name = 'lyrics'

    # Loop through to get some lyrics for each song
    for song in song_list:
        lyrics_url = "http://www.azlyrics.com/lyrics/[band]/[song].html"
        lyrics_url = lyrics_url.replace("[band]", band)\
                               .replace('[song]', song)

        # Make a request to the host
        response  = http.request('GET', lyrics_url)

        # Using BeautifulSoup to store band_url page as lxml
        lyrics_soup  = bs(response.data, "lxml")

        # Find all song lyrics on the page
        lyrics = lyrics_soup.findAll("div", attrs={"class": None, "id": None})

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
        db_insert_lyrics(database_name, collection_name, song_lyrics)



def connect_to_mongo(database_name, collection_name):
    # Initial client to connect to mongo
    client = MongoClient()

    # Access/Initialize database
    database = client[database_name]

    # Access/Initialize Table
    lyric_collection = database[collection_name]
    return lyric_collection

def db_insert_lyrics(database_name, collection_name, lyrics):
    # Connect to and initialize mongo database
    collection = connect_to_mongo(database_name,collection_name)

    # Insert new song lyrics into mongo database
    collection.insert_one(song)


if __name__ == '__main__':
    # Prompt user for band name
    band = raw_input("Enter a band name: ")

    # Calling function to create band url for azlyrics.com
    band_url = band_url_generator(band)

    # Calling function to create song lyric url for azlyrics.com
    song_list = song_list_generator(band_url)

    # Scraping song lyrics from azlyrics.com and inserting into mongo
    #   database
    all_lyrics = scrape_lyrics(band, song_list)
