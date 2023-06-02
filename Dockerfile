FROM python:3.10.11-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN mkdir -p /usr/src/app
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc default-libmysqlclient-dev libffi-dev libssl-dev curl gettext && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade setuptools pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc

COPY . .

# CMD [ "/bin/bash", "-c", "python manage.py migrate;python manage.py runserver 0.0.0.0:8056"]