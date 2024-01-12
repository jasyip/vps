ARG LLDAP_VERSION
FROM nitnelave/lldap:${LLDAP_VERSION}

RUN apk del --no-cache --no-network tini && \
    which -a gosu | xargs rm && \
    rm lldap_config.docker_template.toml /docker-entrypoint.sh

ENTRYPOINT ["/app/lldap"]
CMD ["run", "--config-file", "/data/lldap_config.toml"]
USER $USER

COPY ./lldap_config.toml /data/
