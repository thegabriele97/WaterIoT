FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/arduinodevconn/requirements.txt /app/services/arduinodevconn/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/arduinodevconn/requirements.txt

COPY ./common /app/common
COPY ./services /app/services
WORKDIR /app/services/arduinodevconn

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
