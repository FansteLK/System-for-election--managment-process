
FROM python:3

RUN mkdir -p /opt/src/mod
WORKDIR /opt/src/mod

COPY mod/application.py ./application.py
COPY mod/configuration.py ./configuration.py
COPY mod/models.py ./models.py
COPY mod/requirements.txt ./requirements.txt

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install tzdata
RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/mod"

ENTRYPOINT ["python", "./application.py"]