FROM python:alpine

WORKDIR /code
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]