from collections import defaultdict

if __name__ == '__main__':
    albums = soup.findAll("b")
    songs = soup.findAll("a")[32:-10]

    albums = [str(album).replace("<b>", "")\
                         .replace("</b>", "")\
                         .replace('"','')\
                         .lower() for album in albums]
    album_song_dict = defaultdict(list)
    songs = songs[1:]
    j = 0
    for song in songs:
        song = str(song).split(">")[1].replace("</a","").lower()
        if "href" in song:
            print albums[j], song
            album_song_dict[albums[j]].append(song)
        else:
            j+=1
            continue
