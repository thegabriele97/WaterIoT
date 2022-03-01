FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/telegram/requirements.txt /app/services/telegram/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/telegram/requirements.txt

COPY . /app
WORKDIR /app/services/telegram

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
