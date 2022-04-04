FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/raspberrydevconn/requirements.txt /app/services/raspberrydevconn2/requirements.txt
COPY services/raspberrydevconn/requirements_rpi.txt /app/services/raspberrydevconn2/requirements_rpi.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/raspberrydevconn2/requirements.txt
RUN pip3 install -r /app/services/raspberrydevconn2/requirements_rpi.txt

COPY ./common /app/common
COPY services/raspberrydevconn/app.py /app/services/raspberrydevconn2/app.py
COPY services/raspberrydevconn2 /app/services/raspberrydevconn2
WORKDIR /app/services/raspberrydevconn2

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
