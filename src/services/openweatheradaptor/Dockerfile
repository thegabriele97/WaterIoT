FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/openweatheradaptor/requirements.txt /app/services/openweatheradaptor/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/openweatheradaptor/requirements.txt

COPY ./common /app/common
COPY ./services/openweatheradaptor /app/services/openweatheradaptor
WORKDIR /app/services/openweatheradaptor

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
