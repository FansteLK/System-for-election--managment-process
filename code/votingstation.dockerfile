
FROM python:3
RUN mkdir -p /opt/src/Voting_station
WORKDIR /opt/src/Voting_station

COPY Voting_station/application.py ./application.py
COPY Voting_station/configuration.py ./configuration.py
COPY Voting_station/requirements.txt ./requirements.txt
COPY Voting_station/roleDecorator.py ./roleDecorator.py

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install tzdata
RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/Voting_station"

ENTRYPOINT ["python", "./application.py"]
