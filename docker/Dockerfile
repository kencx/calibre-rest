FROM python:3.11-slim-bullseye as base

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

ENV CALIBRE_CONFIG_DIRECTORY=/app/.calibre \
    CALIBRE_TEMP_DIR=/tmp \
    CALIBRE_CACHE_DIRECTORY=/tmp

RUN useradd -s /bin/bash calibre -u 1000 && \
    mkdir -p ${CALIBRE_CONFIG_DIRECTORY} && \
    chown -R 1000:1000 ${CALIBRE_CONFIG_DIRECTORY}

EXPOSE 80 443
CMD ["/usr/bin/supervisord"]


FROM base as app
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --chmod=0755 ./docker/stop-supervisor.sh /etc/supervisor/stop-supervisor.sh

COPY ./docker/nginx.conf /etc/nginx/nginx.conf

COPY . /app
WORKDIR /app


FROM base as calibre_builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget && \
    wget -nv -O- \
    https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=/opt && \
    apt-get remove --purge --auto-remove -y && \
    apt-get clean && \
    rm -rf \
    /tmp/* \
    /var/lib/apt/lists/* \
    /var/tmp/*


FROM calibre_builder as calibre
COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --chmod=0755 ./docker/stop-supervisor.sh /etc/supervisor/stop-supervisor.sh

COPY ./docker/nginx.conf /etc/nginx/nginx.conf

COPY . /app
WORKDIR /app
