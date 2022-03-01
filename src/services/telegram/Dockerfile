FROM python:3

COPY common/requirements.txt /app/common/requirements.txt
COPY services/calculator/requirements.txt /app/services/calculator/requirements.txt
RUN pip3 install -r /app/common/requirements.txt
RUN pip3 install -r /app/services/calculator/requirements.txt

COPY . /app
WORKDIR /app/services/calculator

# RUN pip install pipreqs
# RUN pipreqs 

ENV PYTHONPATH=/app
ENTRYPOINT ["python3", "app.py"]
