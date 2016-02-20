FROM python:2.7-slim
MAINTAINER "Bijia Lan <lbj.world@gmail.com>"

# setup env
ENV SERVICE_PORT 8000
EXPOSE $SERVICE_PORT
ADD ./auth_apps /code
WORKDIR /code

# install libs
COPY sources.list /etc/apt/sources.list                                         
RUN apt-get update \
    && apt-get install -y build-essential \
                          libmysqlclient-dev \
    && pip install -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && apt-get remove -y libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

ENV SERVICE_USER authcenter
# add user
RUN useradd -ms /bin/bash $SERVICE_USER 
# change dir owner
RUN chown -R $SERVICE_USER /code
USER $SERVICE_USER

# run task
CMD ./run-site.sh 
