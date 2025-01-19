import discord
import spotipy
import random
import os
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from yt_dlp import YoutubeDL
from contextlib import suppress
from datetime import timedelta

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

oauth = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                 client_secret=SPOTIFY_CLIENT_SECRET)


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None
        self.song_queue = []
        self.looping = 0

        # Initialize Spotify client with error handling
        try:
            self.spotify = spotipy.Spotify(client_credentials_manager=oauth)
        except Exception as e:
            print(f"Error initializing Spotify client: {e}")
            self.spotify = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]
                formats = [f for f in info['formats'] if f['ext'] == 'm4a' or f['ext'] == 'webm']
                if not formats:
                    return False
            except Exception as e:
                print(f"Error searching YouTube: {e}")
                return False

        return {'source': formats[0]['url'], 'title': info['title'], 'duration': info['duration']}

    @commands.command(name='join', aliases=['j'])
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
        elif self.vc is None or not self.vc.is_connected():
            try:
                self.vc = await ctx.author.voice.channel.connect()
                await ctx.send(f"Joined **{ctx.author.voice.channel}**")
            except Exception as e:
                await ctx.send(f"Error connecting to voice channel: {e}")
                print(f"Error connecting to voice channel: {e}")
        else:
            await ctx.send(f"Already in channel **{self.vc.channel}**")

    @commands.command(name='disconnect', aliases=['leave', 'dc'])
    async def dc(self, ctx):
        if self.vc is None or not self.vc.is_connected():
            await ctx.send("I am not connected to any voice channel.")
        else:
            try:
                self.song_queue = []
                self.vc.stop()
                await self.vc.disconnect()
                self.vc = None
                await ctx.send("Disconnected from the voice channel.")
            except Exception as e:
                await ctx.send(f"Error disconnecting from voice channel: {e}")
                print(f"Error disconnecting from voice channel: {e}")

    @commands.command(name='remove', aliases=['r'])
    async def remove(self, ctx, *args):
        try:
            query = int(" ".join(args))
            if query < 1 or query > len(self.song_queue):
                await ctx.send("Please enter a valid index number.")
                return

            song = self.song_queue.pop(query - 1)
            await ctx.send(f"Removed song **{song['title']}** from the queue.")
        except ValueError:
            await ctx.send("Please enter a valid index number.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            print(f"Error removing song: {e}")

    def getCurrentSong(self, src):
        for song in self.song_queue:
            if src == song['source']:
                return song
        return None

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        if self.vc and self.vc.is_playing():
            try:
                # noinspection PyProtectedMember
                sauce = self.vc.source._process.args[8]
                current_song = self.getCurrentSong(sauce)
                if current_song is None:
                    await ctx.send("Current song not found in the queue.")
                    return

                current_index = self.song_queue.index(current_song)
                if current_index + 1 == len(self.song_queue):
                    await ctx.send(f"Skipped **{current_song['title']}**. Queue finished.")
                else:
                    next_song = self.song_queue[current_index + 1]
                    await ctx.send(f"Skipped **{current_song['title']}**. Now playing **{next_song['title']}** "
                                f"[{timedelta(seconds=next_song['duration'])}]")

                self.vc.stop()
            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                print(f"Error skipping song: {e}")
        else:
            await ctx.send("Not connected to a voice client or no song is currently playing.")

    def playNext(self, ctx, song):
        if self.vc.is_playing():
            return

        try:
            current_index = self.song_queue.index(song)
        except ValueError:
            return

        if self.looping == 0:
            if current_index + 1 == len(self.song_queue):
                return
            next_song = self.song_queue[current_index + 1]
        elif self.looping == 1:
            next_song = song
        else:
            next_song = self.song_queue[(current_index + 1) % len(self.song_queue)]

        self.vc.play(discord.FFmpegPCMAudio(next_song['source'], **self.FFMPEG_OPTIONS),
                    after=lambda e: self.playNext(ctx, next_song))

    async def playSong(self, ctx, song):
        if self.vc.is_playing():
            return
        try:
            url = song['source']
        except KeyError:
            return
        self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.playNext(ctx, song))

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *args):
        query = " ".join(args)
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
            return

        if self.vc is None:
            self.vc = await ctx.author.voice.channel.connect()

        if self.vc.is_paused() and query == "":
            self.vc.resume()
            await ctx.send("Resumed the music.")
            return

        if "open.spotify" in query:
            try:
                result = self.spotify.track(query)
                query = result['artists'][0]['name'] + " " + result['name']
            except Exception as e:
                await ctx.send(f"Error fetching Spotify track: {e}")
                print(f"Error fetching Spotify track: {e}")
                return

        song = self.search_yt(query)
        if not song:
            await ctx.send("Could not find the song on YouTube.")
            return

        self.song_queue.append(song)
        await ctx.send(f"Queued **{song['title']}** [{timedelta(seconds=song['duration'])}]")

        if not self.vc.is_playing():
            await self.playSong(ctx, song)

    @commands.command(name="clear", aliases=['c'])
    async def clear(self, ctx):
        with suppress(Exception):
            if self.vc and self.vc.is_playing():
                # noinspection PyProtectedMember
                current_song = self.getCurrentSong(self.vc.source._process.args[8])
                self.song_queue = [current_song] if current_song else []
            else:
                self.song_queue = []
            self.vc.stop()
            await ctx.send("Queue cleared")

    @commands.command(name="queue", aliases=['q'])
    async def queue(self, ctx):
        retval = ""
        duration = 0
        try:
            current_song = None
            if self.vc and self.vc.is_playing():
                # noinspection PyProtectedMember
                current_song = self.getCurrentSong(self.vc.source._process.args[8])

            for i, song in enumerate(self.song_queue, start=1):
                duration += song['duration']
                if song == current_song:
                    retval += f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}] **[PLAYING]** \n"
                else:
                    retval += f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}] \n"

            retval += f"\nTotal Duration: **{timedelta(seconds=duration)}**"
            await ctx.send(retval)
        except Exception as e:
            await ctx.send("No songs in queue")
            print(f"Error displaying queue: {e}")

    @commands.command(name="queueRemaining", aliases=['qr'])
    async def queueRemaining(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            new_queue = self.song_queue[self.song_queue.index(current_song):] if current_song else []
        except Exception:
            await ctx.send("No songs in queue")
            return

        retval = ""
        duration = 0
        for i, song in enumerate(new_queue, start=1):
            duration += song['duration']
            retval += f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}]\n"

        retval += f"\nRemaining Duration: **{timedelta(seconds=duration)}**"
        await ctx.send(retval)

    @commands.command(name="pause", aliases=["stop"])
    async def pause(self, ctx):
        if self.vc and self.vc.is_playing():
            self.vc.pause()
            await ctx.send("Paused the music.")
        else:
            await ctx.send("No song is currently playing.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        if self.vc and self.vc.is_paused():
            self.vc.resume()
            await ctx.send("Resumed the music.")
        else:
            await ctx.send("No song is currently paused.")

    @commands.command(name="loop", aliases=['l', 'repeat'])
    async def loop(self, ctx):
        if self.looping == 0:
            self.looping = 1
            await ctx.send("Looping the current song.")
        elif self.looping == 1:
            self.looping = 2
            await ctx.send("Looping the entire queue.")
        else:
            self.looping = 0
            await ctx.send("Looping disabled.")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            if current_song:
                current_index = self.song_queue.index(current_song)
                shuffle_q = self.song_queue[current_index + 1:]
                random.shuffle(shuffle_q)
                self.song_queue = self.song_queue[:current_index + 1] + shuffle_q
                await ctx.send("Queue shuffled")
            else:
                await ctx.send("No song currently playing")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            print(f"Error shuffling queue: {e}")

    @commands.command(name="previous", aliases=['prev'])
    async def previous(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            idx = self.song_queue.index(current_song)
            if idx == 0:
                await ctx.send("No previous song found")
                return
        except Exception:
            await ctx.send("No song currently playing/paused")
            return

        self.vc.stop()
        prev_song = self.song_queue[idx - 1]
        self.vc.play(discord.FFmpegPCMAudio(prev_song['source'], **self.FFMPEG_OPTIONS),
                    after=lambda e: self.playNext(ctx, prev_song))
        await ctx.send(f"Replaying **{prev_song['title']}** [{timedelta(seconds=prev_song['duration'])}]")

    @commands.command(name="rewind")
    async def rewind(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            idx = self.song_queue.index(current_song)
        except Exception:
            await ctx.send("No song currently playing/paused")
            return

        self.vc.stop()
        self.vc.play(discord.FFmpegPCMAudio(self.song_queue[idx]['source'], **self.FFMPEG_OPTIONS),
                    after=lambda e: self.playNext(ctx, self.song_queue[idx]))
        await ctx.send(f"Replaying **{self.song_queue[idx]['title']}** [{timedelta(seconds=self.song_queue[idx]['duration'])}]")

    @commands.command(name="seek")
    async def seek(self, ctx, *args):
        try:
            query = int(" ".join(args))
        except ValueError:
            await ctx.send("Invalid input given")
            return

        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            idx = self.song_queue.index(current_song)
            if query >= self.song_queue[idx]['duration']:
                await ctx.send("The seek value cannot exceed the song duration")
                return
        except Exception:
            await ctx.send("No song currently playing/paused")
            return

        options = f"-vn -ss {query}"
        temp_ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                            'options': options}
        self.vc.stop()
        self.vc.play(discord.FFmpegPCMAudio(self.song_queue[idx]['source'], **temp_ffmpeg_options),
                    after=lambda e: self.playNext(ctx, self.song_queue[idx]))
        await ctx.send(f"Playing **{self.song_queue[idx]['title']}** at **{timedelta(seconds=query)}**")
