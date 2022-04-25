FROM louislam/uptime-kuma:latest

RUN apt-get update
RUN apt-get install -y curl

COPY ./services/uptime/kuma.db /app/data/kuma.db