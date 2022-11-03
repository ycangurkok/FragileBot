import discord
from discord.ext import commands
from yt_dlp import YoutubeDL


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.vc = None
        self.song_queue = []

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
                formats = [x for x in info['formats'] if len(x) > 25]
            except Exception:
                return False

        return {'source': formats[0]['url'], 'title': info['title']}

    @commands.command(name='hello',aliases=['hi'])
    async def sendHello(self, ctx):
        await ctx.send(f"Hello {ctx.author}")

    @commands.command(name='join',aliases=['j'])
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
        elif self.vc is None:
            self.vc = await ctx.author.voice.channel.connect()
        else:
            await ctx.send(f"Already in channel **{self.vc.channel}**")

    @commands.command(name='disconnect',aliases=['leave','dc','l'])
    async def dc(self, ctx):
        self.song_queue = []
        self.vc.stop()
        await self.vc.disconnect()
        self.vc = None

    def getCurrentSong(self, src):
        for song in self.song_queue:
            if src == song['source']:
                return song
        return None

    @commands.command(name='skip',aliases=['s'])
    async def skip(self, ctx):
        if self.vc:
            try:
                # noinspection PyProtectedMember
                sauce = self.vc.source._process.args[8]
                await ctx.send(f"Skipped {self.getCurrentSong(sauce)['title']}")
                self.vc.stop()
            except Exception:
                await ctx.send("No songs in queue")
        else:
            await ctx.send("Not connected to a voice client")

    def playNext(self, ctx, song):
        if self.vc.is_playing():
            return
        if self.song_queue.index(song)+1 == len(self.song_queue):
            return
        self.vc.play(discord.FFmpegPCMAudio(self.song_queue[self.song_queue.index(song)+1]['source'],
                                            **self.FFMPEG_OPTIONS),
                     after=lambda e: self.playNext(ctx,self.song_queue[self.song_queue.index(song)+1]))

    async def playSong(self, ctx, song):
        if self.vc.is_playing():
            return
        try:
            url = self.song_queue[self.song_queue.index(song)]['source']
        except Exception:
            return
        self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.playNext(ctx,song))

    @commands.command(name='play',aliases=['p'])
    async def play(self, ctx, *args):
        query = " ".join(args)
        if ctx.author.voice is None:
            await ctx.send("Please connect to a voice channel")
            return
        elif self.vc is not None and self.vc.is_paused():
            if query == "":
                self.vc.resume()
                return
            song = self.search_yt(query)
            self.song_queue.append(song)
            await ctx.send(f"**{song['title']}** added to the queue")
            return
        elif self.vc is None:
            self.vc = await ctx.author.voice.channel.connect()

        if query == "":
            await ctx.send("Please search a valid song")
            return

        song = self.search_yt(query)
        self.song_queue.append(song)

        if self.vc.is_playing():
            await ctx.send(f"Queued **{song['title']}**")
            return

        await ctx.send(f"Playing **{song['title']}**")
        await self.playSong(ctx, song)

    @commands.command(name="clear",aliases=['stop','c'])
    async def clear(self, ctx):
        # noinspection PyProtectedMember
        self.song_queue = [x for x in self.song_queue if x == self.getCurrentSong(self.vc.source._process.args[8])]
        await ctx.send("Queue cleared")

    @commands.command(name="queue",aliases=['q'])
    async def queue(self, ctx):
        try:
            # noinspection PyProtectedMember
            current_song = self.getCurrentSong(self.vc.source._process.args[8])
            new_queue = self.song_queue[self.song_queue.index(current_song):len(self.song_queue)]
        except Exception:
            await ctx.send("No songs in queue")
            return
        retval = ""
        i = 0
        for song in new_queue:
            i += 1
            retval = retval + f"**{i}.** {song['title']} \n"
        await ctx.send(retval)

    @commands.command(name="pause")
    async def pause(self, ctx):
        if self.vc.is_playing():
            self.vc.pause()
        else:
            await ctx.send("No song to pause")

    @commands.command(name="resume",aliases=['r'])
    async def resume(self, ctx):
        if self.vc.is_paused():
            self.vc.resume()
        else:
            await ctx.send("No song to resume")