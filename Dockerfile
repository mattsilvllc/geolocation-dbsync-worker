FROM ubuntu:14.04
#RUN apt-get update -y && apt-get install -y software-properties-common
#RUN add-apt-repository ppa:fkrull/deadsnakes-python2.7
#RUN apt-get update -y && apt-get install -y wget build-essential python2.7 checkinstall
#WORKDIR ~/Downloads/
#RUN wget http://python.org/ftp/python/2.7.5/Python-2.7.5.tgz
#RUN tar -xvf Python-2.7.5.tgz
#WORKDIR Python-2.7.5
#RUN ./configure
#RUN make
#RUN sudo checkinstall
#WORKDIR ~/Downloads/
RUN wget -O get-pip.py https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py
