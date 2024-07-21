import threading
from pytube import YouTube, Playlist
import os
from pydub import AudioSegment
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error
import requests

# Fonction de téléchargement et de conversion
def download_and_convert_to_mp3(url, download_path, playlist_title):
    try:
        print(f"Processing URL: {url}")
        yt = YouTube(url)
        print(f'Downloading... {yt.title}')
        video_stream = yt.streams.filter(only_audio=True).first()
        video_file = video_stream.download(output_path=download_path)
        base, ext = os.path.splitext(video_file)
        mp3_file = base + '.mp3'

        # Convert to mp3 using pydub
        audio = AudioSegment.from_file(video_file)
        audio.export(mp3_file, format='mp3')

        # Add metadata
        audiofile = EasyID3(mp3_file)
        audiofile['title'] = yt.title
        audiofile['artist'] = yt.author
        audiofile['album'] = playlist_title
        audiofile['genre'] = 'Podcast'  # or any other genre you want to set
        audiofile.save()

        # Add album art
        try:
            video_thumbnail = yt.thumbnail_url
            thumbnail_data = requests.get(video_thumbnail).content
            audiofile = ID3(mp3_file)
            audiofile.add(
                APIC(
                    encoding=3,  # 3 is for utf-8
                    mime='image/jpeg',  # image/jpeg or image/png
                    type=3,  # 3 is for the album front cover
                    desc=u'Cover',
                    data=thumbnail_data
                )
            )
            audiofile.save()
        except error as e:
            print(f"Error adding album art: {e}")

        os.remove(video_file)  # Remove the original video file
        print(f"Downloaded and converted to MP3: {yt.title}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Fonction pour télécharger une playlist
def download_playlist(playlist_url, download_path):
    try:
        p = Playlist(playlist_url)
        playlist_title = p.title.replace(" ", "_")

        # Chemin de téléchargement
        playlist_download_path = os.path.join(download_path, playlist_title)
        os.makedirs(playlist_download_path, exist_ok=True)

        # Lister les threads
        threads = []

        # Créer et démarrer un thread pour chaque vidéo
        for url in p.video_urls:
            print(f"Queuing URL: {url}")
            thread = threading.Thread(target=download_and_convert_to_mp3, args=(url, playlist_download_path, p.title))
            threads.append(thread)
            thread.start()

        # Attendre la fin de tous les threads
        for thread in threads:
            thread.join()

        print("All downloads complete.")
    except Exception as e:
        print(f"Error processing playlist {playlist_url}: {e}")

# Menu principal
def main_menu():
    download_path = os.path.expanduser('~/Downloads')

    while True:
        print("\nMenu:")
        print("1. Add playlist to download")
        print("2. Change download path")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            playlist_url = input("Enter the YouTube playlist URL: ")
            download_playlist(playlist_url, download_path)
        elif choice == '2':
            new_path = input("Enter the new download path: ")
            if os.path.isdir(new_path):
                download_path = new_path
                print(f"Download path changed to: {download_path}")
            else:
                print("Invalid path. Please enter a valid directory.")
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
