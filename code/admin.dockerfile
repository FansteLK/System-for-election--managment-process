
FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY admin/application.py ./application.py
COPY admin/configuration.py ./configuration.py
COPY admin/models.py ./models.py
COPY admin/requirements.txt ./requirements.txt
COPY admin/roleDecorator.py ./roleDecorator.py
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -y install tzdata
RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/admin"

ENTRYPOINT ["python", "./application.py"]