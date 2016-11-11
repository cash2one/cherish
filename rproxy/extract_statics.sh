BASE_DIR=$(pwd)

docker run --rm --user root -v ${BASE_DIR}/static:/code/static docker.zuoyetong.com.cn/account_center/account_web:latest python manage.py collectstatic --noinput
