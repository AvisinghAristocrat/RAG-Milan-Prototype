FROM postgres:15

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      build-essential git postgresql-server-dev-15 ca-certificates && \
    git clone --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && make && make install && \
    rm -rf /tmp/pgvector && \
    apt-get remove -y build-essential git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
