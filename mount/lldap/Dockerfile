ARG LLDAP_VERSION
FROM nitnelave/lldap:${LLDAP_VERSION}

RUN apk del --no-cache --no-network --purge apk-tools tini bash && \
    rm -rf /etc/apk /lib/apk /usr/share/apk /var/lib/apk /var/cache/apk && \
    which -a gosu | xargs rm && \
    rm lldap_config.docker_template.toml /docker-entrypoint.sh

USER $USER

COPY ./lldap_config.toml /data/

ENTRYPOINT ["/app/lldap"]
CMD ["run", "--config-file", "/data/lldap_config.toml"]
