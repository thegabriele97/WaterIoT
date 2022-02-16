FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/catalog/requirements.txt /app/services/catalog/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/catalog/requirements.txt

COPY . /app
WORKDIR /app/services/catalog

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
