FROM python:3.4
RUN apt-get update && apt-get upgrade -y && apt-get install gettext -y
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
ADD requirements.txt /code/
ADD . /code/
WORKDIR /code
RUN cp .env.docker .env
RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt
