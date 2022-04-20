FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/wateringdatabase/requirements.txt /app/services/wateringdatabase/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/wateringdatabase/requirements.txt

COPY . /app
WORKDIR /app/services/wateringdatabase

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
