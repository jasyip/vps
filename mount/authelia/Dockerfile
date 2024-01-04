ARG AUTHELIA_VERSION
FROM authelia/authelia:${AUTHELIA_VERSION}

EXPOSE 9959
ENV X_AUTHELIA_CONFIG="/etc/authelia.yml"
RUN adduser -DH authelia && chown -R authelia:authelia /app \
    && apk del --no-cache --no-network su-exec

USER authelia
ENTRYPOINT ["/app/authelia"]

COPY ./configuration.yml /etc/authelia.yml
