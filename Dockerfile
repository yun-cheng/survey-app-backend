# https://hub.docker.com/_/python
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade -r requirements.txt
COPY . .

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ENV PORT 8080
ENV ENV prod
# HIGHLIGHT 目前需手動添加 CREDENTIALS environment variable

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app