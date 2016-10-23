FROM docker.zuoyetong.com.cn:8888/ubuntu:14.04
MAINTAINER "Bijia Lan <lbj.world@gmail.com>"

ADD http://docker.zuoyetong.com.cn/build/trusty-sources.list /etc/apt/sources.list
RUN apt-get update && apt-get -y install wget ca-certificates && rm -rf /var/lib/apt/lists/* 
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && apt-get update && apt-get install -y pgbouncer \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 5432 

RUN useradd -ms /bin/bash pgbouncer
USER pgbouncer
COPY pgbouncer.ini /etc/pgbouncer/
COPY pgbouncer-userlist.txt /etc/pgbouncer/userlist.txt
CMD ["pgbouncer", "-v", "/etc/pgbouncer/pgbouncer.ini"] 
