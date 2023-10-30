import os
import glob
import sys
import re
import time
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
import pygame
import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont
import tkinter.ttk as ttk
from PIL import ImageTk, Image, ImageDraw
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy import Spotify
##from youtubesearchpython import SearchVideos
from pytube import YouTube
from pydub import AudioSegment
import requests
import webbrowser
import json
##from youtube_transcript_api import YouTubeTranscriptApi
import lyricsgenius
import threading
from urllib.parse import urlparse, parse_qs
import random

username = ""
email = ""





if getattr(sys, 'frozen', False):
    resource_path = sys._MEIPASS
else:
    resource_path = os.path.dirname(os.path.abspath(__file__))

image_path = os.path.join(resource_path, "icon.ico")
bck_path = os.path.join(resource_path, "background.jpg")
play = os.path.join(resource_path, "play.png")
stop = os.path.join(resource_path, "stop.png")

class YouTubeAPI:
    API_KEY = "AIzaSyC4UMckQ0-xpTD1IPA0p02gWCCRxQ8to2A"

    @staticmethod
    def get_trending_videos():
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&maxResults=24&videoCategoryId=10&key={YouTubeAPI.API_KEY}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            videos = []
            for item in data["items"]:
                video_id = item["id"]
                video_title = item["snippet"]["title"]
                videos.append({ "title": video_title}) # "id": video_id,

            return videos

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", "An error occurred while fetching trending videos.")
            print(f"An error occurred: {e}")
            return []


class AudioPlayer:
    def __init__(self, root):
        
        self.root = root
        self.audio_files = []
        self.current_index = None
        self.keep_playing = False
        self.new_theme = False
        self.defualt_color_bg = "#121212"
        self.defualt_color_fg = "#FEFEFE"
        self.defualt_color_bg_text = "#161616"
        self.client_id = ""
        self.client_secret = ""
        self.spotify = None
        self.is_dark_mode = True


        self.light_mode_palette = {
            "bg": self.defualt_color_fg,
            "fg": "#000000",
            "btn_bg": "#ECECEC",
            "btn_fg": "#000000"
        }

        self.dark_mode_palette = {
            "bg": "#03051E",
            "fg": self.defualt_color_fg,
            "btn_bg": "#212121",
            "btn_fg": self.defualt_color_fg
        }
        self.playlist = tk.Listbox(root, bg=self.defualt_color_bg_text, fg=self.defualt_color_fg, selectbackground="#7289DA")
        self.search_results = tk.Listbox(root, bg=self.defualt_color_bg_text, fg=self.defualt_color_fg, selectbackground="#7289DA")
        font3 = tkfont.Font(family="Sans-serif", size=26, weight="normal")
        self.title = tk.Label(root, text="UPlayer", font=font3, bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        self.current_track = tk.StringVar()
        self.current_track.set("")

        self.current_duration = tk.StringVar()
        self.current_duration.set("0:00/0:00")

        pygame.mixer.init()

        self.setup_ui()

        self.auto_check_playlist()

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02}"
        
    def setup_ui(self):
        self.root.title("UPlayer | By Entity.Dev")
        self.root.geometry("800x600")
        self.root.configure(bg=self.defualt_color_bg)
        self.volume = 0.5
        resource_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        #photo = tk.PhotoImage(file = "icon.png")
        trending_label = tk.Label(self.root, text="Trending", bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        trending_label.place(x=620, y=55)
        self.title.place(x=590, y=10)
        trending_box = tk.Listbox(self.root, bg=self.defualt_color_bg_text, fg=self.defualt_color_fg, selectbackground="#7289DA")
        trending_box.place(x=620, y=80, width=160, height=400)

        trending_videos = YouTubeAPI.get_trending_videos()
        for video in trending_videos:
            video_title = video["title"]
            trending_box.insert(tk.END, video_title)

        playlist_label = tk.Label(self.root, text="Playlist", bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        playlist_label.place(x=10, y=55)

        self.playlist.place(x=10, y=80, width=200, height=400)

        search_results_label = tk.Label(self.root, text="Search Results", bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        search_results_label.place(x=250, y=55)

        self.search_results.place(x=250, y=80, width=350, height=400)

        play_button = tk.Button(self.root, text="Play", command=self.play, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        play_button.place(x=280, y=500, width=50, height=40)

        stop_button = tk.Button(self.root, text="Stop", command=self.stop, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        stop_button.place(x=380, y=500, width=50, height=40)

        pause_button = tk.Button(self.root, text="Pause", command=self.pause, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        pause_button.place(x=480, y=500, width=50, height=40)

        resume_button = tk.Button(self.root, text="Resume", command=self.resume, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        resume_button.place(x=580, y=500, width=50, height=40)

        placeholder_font = tkfont.Font(family="Helvetica", size=15, weight="normal", slant="italic")

        search_entry = ttk.Entry(self.root, width=30, font=placeholder_font, style="SearchEntry.TEntry")
        search_entry.insert(0, "Search, Add, Play!")
        search_entry.place(x=20, y=10, width=200)

        style = ttk.Style()
        style.configure("SearchEntry.TEntry", foreground=self.defualt_color_fg, background="#242424",
                        fieldbackground=self.defualt_color_fg, bordercolor=self.defualt_color_fg,
                        borderwidth=10, relief="solid", padding=10, borderradius=10, smooth=True)

        style.theme_use("clam")

        style.map("SearchEntry.TEntry",
                  foreground=[("focus", self.defualt_color_fg), ("!focus", self.defualt_color_fg)],
                  background=[("focus", "#242424"), ("!focus", "#242424")],
                  fieldbackground=[("focus", "#242424"), ("!focus", "#242424")])

        search_entry.bind("<FocusIn>", lambda event: style.configure("SearchEntry.TEntry", background=self.defualt_color_bg))
        search_entry.bind("<FocusOut>", lambda event: style.configure("SearchEntry.TEntry", background=self.defualt_color_bg))
        #search_button = tk.Button(self.root, text="Search", command=lambda: self.search_videos(search_entry.get()))
        #search_button.place(x=530, y=545)
        search_entry.bind("<Return>", lambda event: self.search_videos(search_entry.get()))

        add_to_playlist_button = tk.Button(self.root, text="Add to Playlist", command=self.add_to_playlist, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        add_to_playlist_button.place(x=10, y=550)

        remove_from_playlist_button = tk.Button(self.root, text="Remove From Playlist", command=self.remove_from_playlist, bg=self.defualt_color_bg, fg=self.defualt_color_fg, border=False)
        remove_from_playlist_button.place(x=110, y=550)
        # lyrics_button = tk.Button(root, text="Lyrics", command=self.show_lyrics, bg=self.defualt_color_fg, fg="#000000")
        # lyrics_button.place(x=560, y=510)

        duration_song_label = tk.Label(self.root, text="Song Duration:", bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        duration_song_label.place(x=10, y=525)


        duration_label = tk.Label(self.root, textvariable=self.current_duration, bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        duration_label.place(x=90, y=525)


        # skip_button = tk.Button(self.root, text="Jump Song", command=self.skip_song, bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        # skip_button.place(x=10, y=470)

        current_song_label = tk.Label(self.root, text="Current Song:", bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        current_song_label.place(x=10, y=500)

        current_track_label = tk.Label(self.root, textvariable=self.current_track, bg=self.defualt_color_bg, fg=self.defualt_color_fg)
        current_track_label.place(x=90, y=500)

        volume_slider = tk.Scale(self.root, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL, length=200, sliderlength=15, showvalue=0, bg=self.defualt_color_bg, fg=self.defualt_color_fg, highlightthickness=0, troughcolor=self.defualt_color_bg, command=self.set_volume, border=True, borderwidth=1)
        volume_slider.set(self.volume)
        volume_slider.place(relx=1.0, rely=1.0, anchor=tk.SE, x=-15, y=-30)


    def open_theme_manager(self):
        profile_window = tk.Toplevel(self.root)
        theme_window = tk.Toplevel(profile_window)
        theme_window.title("Theme Manager")
        theme_label = tk.Label(theme_window, text="Select a theme:", bg="#191414", fg=self.defualt_color_fg)
        theme_label.pack(pady=20)
        theme_frame = tk.Frame(theme_window, bg="#191414")
        theme_frame.pack()
        default_theme_button = tk.Button(theme_frame, text="Default", bg="#1DB954", fg=self.defualt_color_fg)
        default_theme_button.pack(side="left", padx=10)
        neon_theme_button = tk.Button(theme_frame, text="Neon", bg="#FF6AD5", fg=self.defualt_color_fg)
        neon_theme_button.pack(side="left", padx=10)

    def search_videos(self, query):
        items = self.search_on_youtube(query)
        self.display_search_results(items)



    def show_lyrics(self):
        lyrics_window = tk.Toplevel(root)
        lyrics_window.title("Lyrics")
        lyrics_window.geometry("400x300")
        lyrics_window.configure(bg=self.defualt_color_fg)

        current_song = app.get_current_song()
        lyrics = self.get_lyrics(current_song)

        lyrics_text = tk.Text(lyrics_window, bg=self.defualt_color_fg, fg="#000000")
        lyrics_text.insert(tk.END, lyrics)
        lyrics_text.pack(fill=tk.BOTH, expand=True)

    def get_lyrics(self, song):
        genius = lyricsgenius.Genius("Z11fJM4G5tCzGGNKscDzUzudTCc-Gwk4C16MW3sLk5Xy0Jt7NeXqCAW5WaSfbbt8")

        search_results = genius.search_song(song)
        if search_results:
            lyrics = search_results.lyrics
        else:
            lyrics = "Lyrics not found"
        return lyrics
    def search_on_youtube(self, query):
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        api_key = "AIzaSyC4UMckQ0-xpTD1IPA0p02gWCCRxQ8to2A"

        youtube = build("youtube", "v3", developerKey=api_key, static_discovery=False)

        try:
            search_response = youtube.search().list(
                q=query,
                part="id,snippet",
                maxResults=10,
                type="video",
                videoCategoryId="10"
            ).execute()

            items = search_response.get("items", [])
            return items
        except HttpError as e:
            messagebox.showerror("Error", "An error occurred while searching on YouTube.")
            print(f"An error occurred: {e}")
            return []

    def display_search_results(self, items):
        self.search_results.delete(0, tk.END)

        for item in items:
            video_id = item["id"]["videoId"]
            video_title = item["snippet"]["title"]

            self.search_results.insert(tk.END, f"{video_title} - {video_id}")

    def set_volume(self, value):
        self.volume = float(value)
        pygame.mixer.music.set_volume(self.volume)

    def generate_safe_filename(self, video_title):
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', video_title)
        return safe_filename


    def extract_video_id(self, url):
        patterns = [
            r"(?:youtube\.com\/.*[?\&]v=|youtu\.be\/)([^#\&\?]*).*",
            r"^(?:https:\/\/)?(?:www\.)?(?:m\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^#\&\?]*).*"
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            else:
                print(f"No match for pattern: {pattern}")

        return None

    def download_from_youtube(self, video_url):
        try:
            video_id = self.extract_video_id(video_url)
            if video_id is None:
                messagebox.showerror("Error", "Invalid YouTube video URL.")
                return
    
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            audio_stream = yt.streams.filter(only_audio=True).first()
    
            if audio_stream is None:
                messagebox.showerror("Error", "No audio stream found for the given YouTube video.")
                return
    
            author = re.sub(r'[<>:"/\\|?*]', '', yt.author)
            title = re.sub(r'[<>:"/\\|?*]', '', yt.title)
            audio_file = audio_stream.download(output_path="audio", filename=f"{author} - {title}")
    
            # Check if the downloaded file exists
            if not os.path.exists(audio_file):
                messagebox.showerror("Error", "Failed to download the audio file.")
                return
    
            audio = AudioSegment.from_file(audio_file)
            wav_file = os.path.splitext(audio_file)[0] + ".wav"
            audio.export(wav_file, format="wav")
    
            self.audio_files.append(wav_file)
            self.playlist.insert("end", os.path.basename(wav_file).replace(".wav", ""))
            self.playlist.itemconfig(len(self.audio_files) - 1, {'fg': '#FFFFFF'})
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while downloading from YouTube: {e}")
            print(f"An error occurred: {e}")

    # def extract_video_id(self, url):
    #     query = urlparse(url)
    #     if query.hostname == 'youtu.be':
    #         return query.path[1:]
    #     if query.hostname in {'www.youtube.com', 'youtube.com'}:
    #         if query.path == '/watch':
    #             p = parse_qs(query.query)
    #             return p['v'][0] if 'v' in p else None
    #         if query.path[:7] == '/embed/':
    #             return query.path.split('/')[2]
    #         if query.path[:3] == '/v/':
    #             return query.path.split('/')[2]
    #     return None

    def remove_from_playlist(self):
        selected_index = self.playlist.curselection()
        if selected_index:
            index = selected_index[0]
            audio_file = self.audio_files.pop(index)
            self.playlist.delete(index)
            if self.current_index is not None:
                if index == self.current_index:
                    self.stop()
                elif index < self.current_index:
                    self.current_index -= 1
            if os.path.exists(audio_file):
                os.remove(audio_file)
    def skip_song(self):
        if self.keep_playing:
            self.stop()
        else:
            self.current_index = (self.current_index + 1) % len(self.audio_files)
            self.play()
    def previous_song(self):
        if self.keep_playing:
            self.stop()
        else:
            if pygame.mixer.music.get_pos() <= 2000:  
                self.current_index = (self.current_index - 1) % len(self.audio_files) 
            self.play()
    def add_to_playlist(self):
        selected_index = self.search_results.curselection()

        if selected_index:
            selected_item = self.search_results.get(selected_index)
            video_id = selected_item.split(" - ")[-1]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            try:
                self.download_from_youtube(video_url)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while adding to playlist: {e}")

    def play(self):
        selected_index = self.playlist.curselection()
    
        if selected_index:
            self.current_index = selected_index[0]
            current_file = self.audio_files[self.current_index]
            pygame.mixer.music.load(current_file)
            pygame.mixer.music.play()
            self.keep_playing = True
    
            self.current_track.set(os.path.basename(current_file).replace(".wav", ""))
    
            audio = AudioSegment.from_file(current_file)
            duration = int(audio.duration_seconds)
            formatted_duration = self.format_time(duration)
            self.current_duration.set(f"0:00/{formatted_duration}")
    
            self.root.after(1000, self.update_duration_label)
    
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            pygame.mixer.music.queue(self.get_next_song())
    def get_current_song(self):
        return self.audio_files[self.current_index]

    def get_next_song(self):
        num_songs = len(self.audio_files)
        next_index = (self.current_index + 1) % num_songs
        return self.audio_files[next_index]

    def play_next_song(self):
        left = self.current_index - 1
        self.current_index = (self.current_index + 1) % len(self.audio_files)
        return self.current_index
    def update_duration_label(self):
        if pygame.mixer.music.get_busy():
            current_time = pygame.mixer.music.get_pos() // 1000
            formatted_time = self.format_time(current_time)

            current_file = self.audio_files[self.current_index]
            audio = AudioSegment.from_file(current_file)
            duration = int(audio.duration_seconds)
            formatted_duration = self.format_time(duration)

            self.current_duration.set(f"{formatted_time}/{formatted_duration}")

        if self.keep_playing:
            self.root.after(1000, self.update_duration_label)

    def stop(self):
        pygame.mixer.music.stop()
        self.keep_playing = False
        self.current_track.set("")
        self.current_duration.set("0:00/0:00")

    def pause(self):
        pygame.mixer.music.pause()
        self.keep_playing = False

    def resume(self):
        pygame.mixer.music.unpause()
        self.keep_playing = True

    def auto_check_playlist(self):
        playlist_folder = "audio"

        audio_files = glob.glob(os.path.join(playlist_folder, "*.wav"))
        new_files = set(audio_files) - set(self.audio_files)

        if new_files:
            for new_file in new_files:
                self.audio_files.append(new_file)
                self.playlist.insert("end", os.path.basename(new_file).replace(".wav", ""))
                self.playlist.itemconfig(len(self.audio_files) - 1, {'fg': '#FFFFFF'})

        deleted_files = set(self.audio_files) - set(audio_files)

        if deleted_files:
            for deleted_file in deleted_files:
                index = self.audio_files.index(deleted_file)
                self.audio_files.remove(deleted_file)
                self.playlist.delete(index)

        self.root.after(10000, self.auto_check_playlist)


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayer(root)

    try:
        root.iconbitmap(image_path)
    except tk.TclError as e:
        print("Error loading image:", e)
    root.mainloop()
