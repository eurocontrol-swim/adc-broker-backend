FROM alpine:latest

RUN mkdir /app
WORKDIR /app

# install python
RUN apk add python3
RUN apk add py3-pip

# proton lib installation
RUN apk add g++ make cmake
RUN apk add python3-dev
RUN apk add openssl-dev
ENV OPENSSL_ROOT_DIR="/usr/bin/"
RUN apk add cyrus-sasl
ENV CYRUS_SASL_ROOT_DIR="/usr/sbin/"
ENV CYRUSSASL_ROOT_DIR="/usr/sbin/"
RUN apk add swig

RUN python3 -m pip install sphinx
RUN python3 -m pip install wheel
RUN python3 -m pip install tox

RUN mkdir /proton
RUN wget -O /proton/qpid-proton-0.36.0.tar.gz http://archive.apache.org/dist/qpid/proton/0.36.0/qpid-proton-0.36.0.tar.gz

WORKDIR /proton
RUN tar -xf qpid-proton-0.36.0.tar.gz

WORKDIR /proton/qpid-proton-0.36.0
RUN mkdir build
WORKDIR /proton/qpid-proton-0.36.0/build

RUN python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())"
RUN python3 -c "import distutils.sysconfig as sysconfig; import os; print(os.path.join(sysconfig.get_config_var('LIBDIR'), sysconfig.get_config_var('LDLIBRARY')))"

RUN cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DSYSINSTALL_BINDINGS=ON -DSYSINSTALL_PYTHON=ON -DPYTHON_INCLUDE_DIR=$(python3 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") -DPYTHON_LIBRARY=$(python3 -c "import distutils.sysconfig as sysconfig; import os; print(os.path.join(sysconfig.get_config_var('LIBDIR'), sysconfig.get_config_var('LDLIBRARY')))")
RUN make install
ENV LD_LIBRARY_PATH="/usr/lib64/:${LD_LIBRARY_PATH}"

# python dependencies
RUN pip3 install Django
RUN pip3 install djangorestframework
RUN pip3 install django-rest-swagger
RUN apk add postgresql-dev
RUN pip3 install psycopg2-binary
RUN pip3 install unidecode
RUN pip3 install jsonpath_ng
RUN pip3 install gunicorn

# other dependencies
RUN apk add curl

# copy sources
COPY adc_backend /app/adc_backend
COPY backend /app/backend
COPY manage.py /app/
COPY entrypoint.sh /app/
COPY artemis_broker /app/artemis_broker
COPY fixtures /app/fixtures

WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh"]

