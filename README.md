# FragileBot
A minimalist Discord music bot. Written fully in Python 🐍.

## Description
This is a hobby project that aims to create a fully functional music bot for the Discord messaging platform. It aims to be a suitable replacement to the now-defunct Groovy music bot.

### Why?
Although there are many other projects that attempt to achieve the exact same functionality as mine (some of which admittedly do a better job than this project at its current state); this project aims to have minimal boilerplate code which plagues many other open-source alternatives, have a smaller scope in its functionalities in favor of doing the few things it does *decently*, and be a headache-free experience for any intermediate user willing to host their own bot for the sole purpose of listening to some tunes with friends.

**TL;DR:** It just plays music.

### Features:

 - Full YouTube and Spotify support
 - Full playback functionality (pause/skip/resume etc.)
 - Full queue management functionality (remove/move etc.)
 - Looping & shuffling
 - Seeking
 - Lyrics

### Requirements:

 - Docker (and Compose)
 - Bot token from Discord
 - Spotify Client and Secret Tokens
 
### Installation:

1. Clone the repository
2. Set your tokens in the environment variables of your system
3. Run "docker compose up -d" within the repository folder
4. Profit
