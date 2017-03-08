FROM python:3.4
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
RUN mkdir /code/osis_common
WORKDIR /code
ADD requirements.txt /code/
ADD /osis_common/requirements.txt /code/osis_common/
RUN pip install -r requirements.txt
ADD . /code/
