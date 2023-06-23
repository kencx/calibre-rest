FROM python:3.11-slim-bullseye

LABEL maintainer=""

RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    nginx \

    # install calibre system dependencies
    xdg-utils \
    xz-utils \
    libopengl0 \
    libegl1 && \

    apt-get remove --purge --auto-remove -y && \
    apt-get clean && \
    rm -rf \
    /tmp/* \
    /var/lib/apt/lists/* \
    /var/tmp/*

# forward nginx log files to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log

COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --chmod=0755 ./docker/stop-supervisor.sh /etc/supervisor/stop-supervisor.sh

COPY ./docker/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 443
CMD ["/usr/bin/supervisord"]
