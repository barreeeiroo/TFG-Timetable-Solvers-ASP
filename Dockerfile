# syntax=docker/dockerfile:1

FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y \
  git gringo

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN rm requirements.txt

COPY src/ .
