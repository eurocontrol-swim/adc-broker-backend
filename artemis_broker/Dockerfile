FROM alpine:latest

#ARG certs_dir

RUN mkdir /artemis
RUN mkdir /certs
WORKDIR /artemis

# this section is secific to Thales environment
ENV http_proxy="http://10.31.255.65:8080"
ENV https_proxy="https://10.31.255.65:8080"
ENV HTTP_PROXY="http://10.31.255.65:8080"
ENV HTTPS_PROXY="https://10.31.255.65:8080"

RUN sed -i -e 's/https/http/' /etc/apk/repositories
# end of the specific section

RUN apk add wget
RUN wget -O jre14.tar https://cdn.azul.com/zulu/bin/zulu14.28.21-ca-jre14.0.1-linux_musl_x64.tar.gz
RUN tar -xvf ./jre14.tar
RUN ln -s /artemis/zulu14.28.21-ca-jre14.0.1-linux_musl_x64/bin/java /usr/bin/java
RUN java --version

RUN wget -O "artemis.tar.gz" "https://archive.apache.org/dist/activemq/activemq-artemis/2.19.0/apache-artemis-2.19.0-bin.tar.gz"
RUN tar -xvf ./artemis.tar.gz
RUN ln -s /artemis/apache-artemis-2.19.0 /artemis/current

RUN /artemis/current/bin/artemis create --user admin --password admin --http-host 0.0.0.0 --require-login --relax-jolokia adc_broker
#RUN /artemis/current/bin/artemis create --user admin --password admin --http-host 0.0.0.0 --allow-anonymous --relax-jolokia adc_broker
COPY broker.xml /artemis/adc_broker/etc/
#COPY ${certs_dir}/broker* /certs/
COPY certs/broker.ks certs/broker.ts /certs/

EXPOSE 8161 5672 5771 61616

ENTRYPOINT ["/artemis/adc_broker/bin/artemis", "run"]
