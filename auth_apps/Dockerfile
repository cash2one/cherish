FROM docker.zuoyetong.com.cn:8888/python:2.7-slim
MAINTAINER "Bijia Lan <lbj.world@gmail.com>"

# add user
ENV SERVICE_USER authcenter
RUN useradd -ms /bin/bash $SERVICE_USER 

# install libs
COPY ./auth_apps/requirements.txt /
ADD http://docker.zuoyetong.com.cn/build/jessie-sources.list /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y build-essential \
                          libpq-dev \
                          gettext \
                          git \
                          libjpeg-dev \
    && pip install -r /requirements.txt \
    && apt-get purge -y build-essential git \
    && apt-get autoremove -y \
    && apt-get remove -y libpq-dev libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# setup env
ENV SERVICE_PORT 8000
EXPOSE $SERVICE_PORT

ADD ./auth_apps /code
WORKDIR /code

# change dir owner
RUN chown -R $SERVICE_USER /code
USER $SERVICE_USER

# run task
CMD ./run-site.sh 
