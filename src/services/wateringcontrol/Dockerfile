FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/wateringcontrol/requirements.txt /app/services/wateringcontrol/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/wateringcontrol/requirements.txt

COPY . /app
WORKDIR /app/services/wateringcontrol

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
