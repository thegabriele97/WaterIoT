FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/nodered/requirements.txt /app/services/nodered/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/nodered/requirements.txt

COPY . /app
WORKDIR /app/services/nodered

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
