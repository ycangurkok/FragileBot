FROM python:alpine

WORKDIR /code
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install discord pynacl yt-dlp spotipy

COPY . .

CMD ["python", "bot.py"]