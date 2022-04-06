FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/thingspeakadaptor/requirements.txt /app/services/thingspeakadaptor/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/thingspeakadaptor/requirements.txt

COPY ./common /app/common
COPY ./services/thingspeakadaptor /app/services/thingspeakadaptor
WORKDIR /app/services/thingspeakadaptor

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
