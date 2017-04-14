import requests
from bs4 import BeautifulSoup as bs
import urllib3.request
from collections import defaultdict
from pymongo import MongoClient


def get_soup(query=True):
    ''' Creating album-song-year list of songs for The Cure from azlyrics.com
        Input: query        list of strings, urls for eras on thecure.com
        Output: song_list   BeautifulSoup object containing html of The Cure
                              albums/songs/years from azlyrics.com
    '''
    # Setting url for site with The Cure albums and songs listed on same page
    album_song_url = "http://www.azlyrics.com/c/cure.html"

    # Creating a PoolManager, which is an abstraction for a container for a collection of connections to the host
    http = urllib3.PoolManager()

    # Make a request to the host
    response  = http.request('GET', album_song_url)

    # If request succeeded, proceed with song list generation
    if response.status == 200:

        # Using BeautifulSoup to store parse html from era_url page
        soup = bs(response.data, 'html.parser')

    return soup


def album_song_list_generator(soup):
    # Creating mongo database_name & collection_name
    database_name = 'The_Cure'
    collection_name = 'album_info'

    # Check if database is already populated (non-empty)
    collection = connect_to_mongo(database_name, collection_name)

    if list(collection.find()) == []:
        # Grabbing all album titles from BeautifulSoup object
        albums = soup.findAll("b")

        # Grabbing all song titles from BeautifulSoup object
        songs = soup.findAll("a")[32:-10]

        # Grabbing year for each album from BeautifulSoup object
        years = soup.findAll("div", {"class":"album"})[0:15]
        for year in years:
            year = str(year).split("</b> ")[1]\
                            .replace("(", "")\
                            .replace(")</div>","")

        # Reformatting albums and songs to remove html elements and make lower case
        albums = [str(album).replace("<b>", "")\
                             .replace("</b>", "")\
                             .replace('"','')\
                             .lower() for album in albums]

        album_song_dict = defaultdict(list)
    #    songs = songs[1:]
        j = 0
        for song in songs:
            if "href" in str(song):
                song = str(song).split(">")[1]\
                .replace("</a","")\
                .lower()
                print albums[j], song
                album_song_dict[albums[j]].append(song)
            else:
                j+=1
                continue

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


def db_insert_album_info(database_name, collection_name, album_info):
    ''' Insert songs and year released for albums into MongoDB table
        Input: database_name    string, MongoDB database name to insert into
               collection name  string, MongoDB collection name to insert into
               album_info       string, album name, songs, year to insert into
                                  MongoDB
        Output: None, collection is just updated
    '''
    # Connect to and initialize mongo database
    collection = connect_to_mongo(database_name,collection_name)

    # Insert new song lyrics into mongo database
    collection.insert_one(all_lyrics)


if __name__ == '__main__':
    soup = get_soup()
    album_song_list_generator(soup)
