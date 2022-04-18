FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/example/requirements.txt /app/services/example/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/example/requirements.txt

COPY ./common /app/common
COPY ./services/example /app/services/example
WORKDIR /app/services/example

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
