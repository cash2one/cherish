FROM docker.zuoyetong.com.cn/openresty:1.9-techu-dns
MAINTAINER "Bijia Lan <lbj.world@gmail.com>"

COPY ./static /code/static
COPY ./middleware $NGINX_PREFIX/middleware
COPY ./nginx/nginx.conf $NGINX_PREFIX/conf/nginx.conf
