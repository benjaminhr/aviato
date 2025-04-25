
FROM alpine:3.21

RUN apk add --no-cache bash curl jq git

WORKDIR /app
COPY main.sh run-loop.sh /app/
RUN chmod +x /app/main.sh /app/run-loop.sh


ENTRYPOINT ["/app/run-loop.sh"]