
FROM python:3
RUN mkdir -p /opt/src/Dameon
WORKDIR /opt/src/Dameon

COPY Dameon/application.py ./application.py
COPY Dameon/configuration.py ./configuration.py
COPY Dameon/models.py ./models.py
COPY Dameon/requirements.txt ./requirements.txt

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install tzdata
RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/Dameon"

ENTRYPOINT ["python", "./application.py"]




