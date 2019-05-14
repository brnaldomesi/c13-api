FROM python:3.7

EXPOSE 3031
EXPOSE 8080
ENV PYTHONPATH=/opt/cadence13/podcast-api/ext/podcast-db/src:/opt/cadence13/podcast-api/src

RUN pip install -U pip
RUN pip install -U uwsgi
RUN pip install pipenv

COPY Pipfile /tmp/
COPY Pipfile.lock /tmp/
WORKDIR /tmp/
RUN pipenv install --system --deploy

COPY docker-entrypoint.sh /usr/local/bin/
RUN ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

COPY ./src /opt/cadence13/podcast-api/src/
COPY ./ext /opt/cadence13/podcast-api/ext/

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["public"]
