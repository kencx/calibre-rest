FROM python:3.11-slim-bullseye

LABEL maintainer=""

# install calibre
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    xdg-utils \
    xz-utils \
    libopengl0 \
    libegl1 && \

    wget -nv -O- \
    https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin install_dir=/opt && \

    apt-get clean && \
    rm -rf \
    /tmp/* \
    /var/lib/apt/lists/* \
    /var/tmp/*


COPY ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app
WORKDIR /app

ENV CALIBRE_CONFIG_DIRECTORY=/app/.calibre \
    CALIBRE_TEMP_DIR=/tmp \
    CALIBRE_CACHE_DIRECTORY=/tmp

RUN useradd -s /bin/bash calibre -u 1000 && \
    mkdir -p ${CALIBRE_CONFIG_DIRECTORY} && \
    chown -R 1000:1000 ${CALIBRE_CONFIG_DIRECTORY}
USER 1000:1000

EXPOSE 5000

CMD ["gunicorn", "calibre_rest:create_app('prod')", "-c", "gunicorn.py"]
