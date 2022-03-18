FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/arduinodevconn2/requirements.txt /app/services/arduinodevconn2/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/arduinodevconn2/requirements.txt

COPY ./common /app/common
COPY ./services /app/services
WORKDIR /app/services/arduinodevconn2

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
