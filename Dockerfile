# syntax=docker/dockerfile:1

FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get install -y \
  gringo

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN rm requirements.txt

COPY src/ .
