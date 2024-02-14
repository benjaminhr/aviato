FROM python:3.8

WORKDIR /usr/src/app
COPY . /usr/src/app

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg

RUN pip install --no-cache-dir -r requirements.txt

RUN chmod +x ./entrypoint.sh
CMD ["./entrypoint.sh"]