FROM ubuntu:14.04
RUN apt-get update -y && apt-get install -y wget build-essential libmysqlclient-dev python-dev
RUN wget -O get-pip.py https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py
