FROM python:3.6

EXPOSE 5000

WORKDIR /forex_exchange_rates_app/

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

COPY requirements.txt /forex_exchange_rates_app/
ARG REQUIREMENTS_FILE=requirements.txt
RUN pip install -r $REQUIREMENTS_FILE

COPY . /forex_exchange_rates_app/.
RUN pip install -e .

CMD python ./forex_exchange_rates_app/app.py