
FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY authentication/migrate.py ./migrate.py
COPY authentication/configuration.py ./configuration.py
COPY authentication/models.py ./models.py
COPY authentication/requirements.txt ./requirements.txt
COPY authentication/roleDecorator.py ./roleDecorator.py

RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/authentication"

ENTRYPOINT ["python", "./migrate.py"]
#ENTRYPOINT ["sleep", "1200"]