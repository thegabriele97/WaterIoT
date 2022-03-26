FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/raspberrydevconn/requirements.txt /app/services/raspberrydevconn/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/raspberrydevconn/requirements.txt

COPY . /app
WORKDIR /app/services/raspberrydevconn

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
