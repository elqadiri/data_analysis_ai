FROM ubuntu:latest
LABEL authors="zerbo"

ENTRYPOINT ["top", "-b"]