FROM alpine:latest

RUN mkdir /artemis
#RUN mkdir /certs
WORKDIR /artemis

RUN apk add wget
RUN wget -O jre14.tar https://cdn.azul.com/zulu/bin/zulu14.28.21-ca-jre14.0.1-linux_musl_x64.tar.gz
RUN tar -xvf ./jre14.tar
#RUN ln -s /artemis/zulu14.28.21-ca-jre14.0.1-linux_musl_x64/bin/java /usr/bin/java
ENV PATH="${PATH}:/artemis/zulu14.28.21-ca-jre14.0.1-linux_musl_x64/bin/"

RUN wget -O "artemis.tar.gz" "https://archive.apache.org/dist/activemq/activemq-artemis/2.19.0/apache-artemis-2.19.0-bin.tar.gz"
RUN tar -xvf ./artemis.tar.gz
RUN ln -s /artemis/apache-artemis-2.19.0 /artemis/current

RUN /artemis/current/bin/artemis create --user admin --password admin --http-host 0.0.0.0 --require-login --relax-jolokia adc_broker

COPY broker.xml /artemis/adc_broker/etc/

EXPOSE 8161 5672 5771 61616

ENTRYPOINT ["/artemis/adc_broker/bin/artemis", "run"]
