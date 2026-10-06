FROM python:3.12-slim
WORKDIR /app
RUN pip install flask==3.0.3 prometheus-client==0.20.0 gunicorn==22.0.0
COPY exporter.py .
EXPOSE 9101
CMD ["gunicorn","--bind","0.0.0.0:9101","--workers","1","exporter:app"]
