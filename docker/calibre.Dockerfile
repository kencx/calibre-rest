FROM calibre_rest_base:latest

# install calibre
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
