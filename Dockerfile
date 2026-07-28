
# Backend build stage
FROM python:3.12-trixie AS backend_builder

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    openssh-client \
    git \
    librdkafka-dev \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# COPY ./src/Pipfile.lock ./src/Pipfile ./
COPY ./requirements.txt ./
COPY ./setup.cfg .

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# RUN mkdir -p /root/.ssh && chmod -R 700 /root/.ssh/
# COPY .docker/ssh/* /root/.ssh/
# RUN chmod -R 600 /root/.ssh/id_*

COPY ./ ./

# set date on image
RUN rm -f /etc/localtime
RUN ln -s /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime


# Build full application
FROM backend_builder

RUN groupadd -r appgroup && useradd -r -g appgroup -m -s /bin/bash appuser
# Create the application directory and set ownership to the non-root user
RUN mkdir -p /app && chown -R appuser:appgroup /app

USER appuser

ENV DJANGO_SETTINGS_MODULE=vert_helper.tests.settings

CMD ["python", "-m", "django", "test", "vert_helper.tests", "-v", "2"]

# ENTRYPOINT ["./docker_assets/entrypoint.sh"]

# CMD ["gunicorn", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "warning", "--timeout", "120", "main.wsgi"]
