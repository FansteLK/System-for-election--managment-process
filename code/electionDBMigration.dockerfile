
FROM python:3

RUN mkdir -p /opt/src/admin
WORKDIR /opt/src/admin

COPY admin/migrate.py ./migrate.py
COPY admin/configuration.py ./configuration.py
COPY admin/models.py ./models.py
COPY admin/requirements.txt ./requirements.txt
COPY admin/roleDecorator.py ./roleDecorator.py

RUN pip install -r ./requirements.txt
ENV PYTHONPATH="/opt/src/admin"

ENTRYPOINT ["python", "./migrate.py"]
#ENTRYPOINT ["sleep", "1200"]