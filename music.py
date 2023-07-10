import discord
import spotipy
import random
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from yt_dlp import YoutubeDL
from contextlib import suppress
from datetime import timedelta
import azapi

oauth = SpotifyClientCredentials(client_id="",
                                 client_secret="")


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None
        self.song_queue = []
        self.spotify = spotipy.Spotify(client_credentials_manager=oauth)
        self.looping = 0
        self.lyrics_api = azapi.AZlyrics('google',0.5)

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
                formats = [x for x in info['formats'] if len(x) > 25]
            except Exception:
                return False

        return {'source': formats[0]['url'], 'title': info['title'], 'duration': info['duration']}

    @commands.command(name='hello', aliases=['hi'])
    async def sendHello(self, ctx):
        await ctx.send(f"Hello {ctx.author}")

    @commands.command(name='join', aliases=['j'])
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
        elif self.vc is None:
            self.vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.send(f"Already in channel **{self.vc.channel}**")

    @commands.command(name='disconnect', aliases=['leave', 'dc'])
    async def dc(self, ctx):
        with suppress(Exception):
            self.song_queue = []
            self.vc.stop()
            await self.vc.disconnect()
            self.vc = None

    @commands.command(name='remove', aliases=['r'])
    async def remove(self, ctx, *args):
        try:
            query = int(" ".join(args))
            song = self.song_queue.pop(query - 1)
            await ctx.send(f"Removed song **{song['title']}**")
        except Exception:
            await ctx.send("Please enter a valid index number")

    def getCurrentSong(self, src):
        for song in self.song_queue:
            if src == song['source']:
                return song
        return None

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        if self.vc:
            try:
                # noinspection PyProtectedMember
                sauce = self.vc.source._process.args[8]
                nxt = ""
                if self.song_queue.index(self.getCurrentSong(sauce)) + 1 == len(self.song_queue):
                    await ctx.send(f"Skipped **{self.getCurrentSong(sauce)['title']}**. Queue finished.")
                else:
                    await ctx.send(f"Skipped **{self.getCurrentSong(sauce)['title']}**. "
                                   f"Now playing **"
                                   f"{self.song_queue[self.song_queue.index(self.getCurrentSong(sauce))+1]['title']}** "
                                   f"[{timedelta(seconds=self.song_queue[self.song_queue.index(self.getCurrentSong(sauce))+1]['duration'])}]")
                self.vc.stop()
            except Exception:
                await ctx.send("No songs in queue")
        else:
            await ctx.send("Not connected to a voice client")

    def playNext(self, ctx, song):
        if self.vc.is_playing():
            return
        if self.looping == 0:
            if self.song_queue.index(song) + 1 == len(self.song_queue):
                return
            self.vc.play(discord.FFmpegPCMAudio(self.song_queue[self.song_queue.index(song) + 1]['source'],
                                                **self.FFMPEG_OPTIONS),
                         after=lambda e: self.playNext(ctx, self.song_queue[self.song_queue.index(song) + 1]))
        elif self.looping == 1:
            self.vc.play(discord.FFmpegPCMAudio(self.song_queue[self.song_queue.index(song)]['source'],
                                                **self.FFMPEG_OPTIONS),
                         after=lambda e: self.playNext(ctx, self.song_queue[self.song_queue.index(song)]))
        else:
            if self.song_queue.index(song) + 1 == len(self.song_queue):
                self.vc.play(discord.FFmpegPCMAudio(self.song_queue[0]['source'], **self.FFMPEG_OPTIONS),
                             after=lambda e: self.playNext(ctx, self.song_queue[0]))
            else:
                self.vc.play(discord.FFmpegPCMAudio(self.song_queue[self.song_queue.index(song) + 1]['source'],
                                                    **self.FFMPEG_OPTIONS),
                             after=lambda e: self.playNext(ctx, self.song_queue[self.song_queue.index(song) + 1]))

    async def playSong(self, ctx, song):
        if self.vc.is_playing():
            return
        try:
            url = self.song_queue[self.song_queue.index(song)]['source']
        except Exception:
            return
        self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.playNext(ctx, song))

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *args):
        query = " ".join(args)
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
            return
        elif self.vc is not None and self.vc.is_paused():
            if query == "":
                self.vc.resume()
                return
            if "open.spotify" in query:
                result = self.spotify.track(query)
                query = result['artists'][0]['name'] + " " + result['name']
            song = self.search_yt(query)
            self.song_queue.append(song)
            await ctx.send(f"Queued **{song['title']}** [{timedelta(seconds=song['duration'])}]")
            return
        elif self.vc is None:
            self.vc = await ctx.author.voice.channel.connect()

        if query == "":
            await ctx.send("Please search a valid song")
            return

        if "open.spotify" in query:
            result = self.spotify.track(query)
            query = result['artists'][0]['name'] + " " + result['name']
        song = self.search_yt(query)
        self.song_queue.append(song)

        if self.vc.is_playing():
            await ctx.send(f"Queued **{song['title']}** [{timedelta(seconds=song['duration'])}]")
            return

        await ctx.send(f"Playing **{song['title']}** [{timedelta(seconds=song['duration'])}]")
        await self.playSong(ctx, song)

    @commands.command(name="clear", aliases=['c'])
    async def clear(self, ctx):
        # noinspection PyProtectedMember
        self.song_queue = [x for x in self.song_queue if x == self.getCurrentSong(self.vc.source._process.args[8])]
        self.vc.stop()
        await ctx.send("Queue cleared")

    @commands.command(name="queue", aliases=['q'])
    async def queue(self, ctx):
        retval = ""
        i = 0
        duration = 0
        try:
            for song in self.song_queue:
                i += 1
                duration += song['duration']
                # noinspection PyProtectedMember
                if song == self.getCurrentSong(self.vc.source._process.args[8]):
                    retval = retval + f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}] " \
                                      f"**[PLAYING]** \n"
                    continue
                retval = retval + f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}] \n"
            retval += f"\nTotal Duration: **{timedelta(seconds=duration)}**"
            await ctx.send(retval)
        except Exception:
            await ctx.send("No songs in queue")

    @commands.command(name="queueRemaining", aliases=['qr'])
    async def queueRemaining(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            new_queue = self.song_queue[self.song_queue.index(current_song):len(self.song_queue)]
        except Exception:
            await ctx.send("No songs in queue")
            return
        retval = ""
        i = 0
        duration = 0
        for song in new_queue:
            duration += song['duration']
            i += 1
            retval = retval + f"**{i}.** {song['title']} [{timedelta(seconds=song['duration'])}]\n"
        retval += f"\nRemaining Duration: **{timedelta(seconds=duration)}**"
        await ctx.send(retval)

    @commands.command(name="pause", aliases=["stop"])
    async def pause(self, ctx):
        if self.vc.is_playing():
            self.vc.pause()
        else:
            await ctx.send("No song to pause")

    @commands.command(name="resume")
    async def resume(self, ctx):
        if self.vc.is_paused():
            self.vc.resume()
        else:
            await ctx.send("No song to resume")

    @commands.command(name="loop", aliases=['l', 'repeat'])
    async def loop(self, ctx):
        if self.looping == 0:
            self.looping = 1
            await ctx.send("Looping the song")
        elif self.looping == 1:
            self.looping = 2
            await ctx.send("Looping the queue")
        else:
            self.looping = 0
            await ctx.send("Looping disabled")

    @commands.command(name="lyrics")
    async def lyrics(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song_title = self.getCurrentSong(self.vc.source._process.args[8])['title']
        except Exception:
            await ctx.send("No song currently playing")
            return

        self.lyrics_api.title = current_song_title
        self.lyrics_api.getLyrics()
        lyrics = self.lyrics_api.lyrics
        try:
            if len(lyrics) > 2000:
                if len(lyrics) > 4000:
                    await ctx.send("Lyrics too long for Discord")
                    return

                firstpart, secondpart = lyrics[:len(lyrics) // 2], lyrics[len(lyrics) // 2:]
                await ctx.send(f"""```{firstpart}```""")
                await ctx.send(f"""```{secondpart}```""")
                return
            await ctx.send(lyrics)
        except Exception:
            await ctx.send("No lyrics found")
            return

    @commands.command(name="shuffle")
    async def shuffle(self, ctx):
        # noinspection PyProtectedMember
        shuffle_q = self.song_queue[self.song_queue.index(self.getCurrentSong(self.vc.source._process.args[8])) + 1:]
        random.shuffle(shuffle_q)
        i = 1
        for song in shuffle_q:
            # noinspection PyProtectedMember
            self.song_queue[self.song_queue.index(self.getCurrentSong(self.vc.source._process.args[8])) + i] = song
            i += 1
        await ctx.send("Queue shuffled")

    @commands.command(name="previous", aliases=['prev'])
    async def previous(self, ctx):
        idx = None
        try:
            # noinspection PyProtectedMember
            idx = self.song_queue.index(self.getCurrentSong(self.vc.source._process.args[8]))
            if idx == 0:
                await ctx.send("No previous song found")
                return
        except Exception:
            await ctx.send("No song currently playing/paused")
            return
        self.vc.stop()
        prev_song = self.song_queue[idx - 1]
        self.vc.play(discord.FFmpegPCMAudio(prev_song['source'],
                                            **self.FFMPEG_OPTIONS),
                     after=lambda e: self.playNext(ctx, self.song_queue[idx - 1]))
        await ctx.send(f"Replaying **{prev_song['title']}** [{timedelta(seconds=prev_song['duration'])}]")

    @commands.command(name="rewind")
    async def rewind(self, ctx):
        idx = None
        try:
            # noinspection PyProtectedMember
            idx = self.song_queue.index(self.getCurrentSong(self.vc.source._process.args[8]))
        except Exception:
            await ctx.send("No song currently playing/paused")
            return
        self.vc.stop()
        self.vc.play(discord.FFmpegPCMAudio(self.song_queue[idx]['source'],
                                            **self.FFMPEG_OPTIONS),
                     after=lambda e: self.playNext(ctx, self.song_queue[idx]))
        await ctx.send(f"Replaying **{self.song_queue[idx]['title']}** "
                       f"[{timedelta(seconds=self.song_queue[idx]['duration'])}]")

    @commands.command(name="seek")
    async def seek(self, ctx, *args):
        try:
            query = int(" ".join(args))
        except Exception:
            await ctx.send("Invalid input given")
            return
        idx = None
        try:
            # noinspection PyProtectedMember
            idx = self.song_queue.index(self.getCurrentSong(self.vc.source._process.args[8]))
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
        self.vc.play(discord.FFmpegPCMAudio(self.song_queue[idx]['source'],
                                            **temp_ffmpeg_options),
                     after=lambda e: self.playNext(ctx, self.song_queue[idx]))
        await ctx.send(f"Playing **{self.song_queue[idx]['title']}** at **{timedelta(seconds=query)}**")
