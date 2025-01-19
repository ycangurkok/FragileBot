FROM python:3.13.1-alpine

WORKDIR /code

# Install system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev ffmpeg opus-dev

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]