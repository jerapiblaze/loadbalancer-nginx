FROM debian:latest as base

RUN apt update
RUN apt install python3-full -y
RUN apt install nginx -y

FROM base as build

WORKDIR /usr/loadbalancer-nginx
COPY ./requirements.txt ./
RUN python3 -m venv ./.python
RUN ./.python/bin/pip install -r requirements.txt
RUN mkdir /etc/loadbalancer-nginx
RUN mkdir /etc/loadbalancer-nginx/config
RUN rm -f /etc/nginx/sites-enabled/*
RUN sed -i -e "s/worker_connections 768;/worker_connections 10000;/g" /etc/nginx/nginx.conf
RUN sed -i -e "s/# multi_accept on;/multi_accept on;/g" /etc/nginx/nginx.conf

FROM build

WORKDIR /usr/loadbalancer-nginx
COPY . .
EXPOSE 80/tcp
CMD service nginx start && ./.python/bin/python main.py -f /etc/loadbalancer-nginx/config/prod.yaml