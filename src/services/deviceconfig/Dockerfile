FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/deviceconfig/requirements.txt /app/services/deviceconfig/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/deviceconfig/requirements.txt

COPY . /app
WORKDIR /app/services/deviceconfig

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
