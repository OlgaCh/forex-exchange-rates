#  Open Exchange Rate API Wrapper

Goal of this app is to collect up to date exchange rates for the given currency
using `USD` as a base currency.
Then having exchange rate calculate amount in `USD` person would receive upon exchange will be done.

## Setup

To setup please run in terminal:
> docker-compose up -d --build

It will create and start containers with `Flask` web app, and 2 data storages for `mysql`
and `redis`.

##### Important notice
1. Before starting docker containers `sample-settings.py` should be renamed to `settings.py` 
and have all required sections populated.


2. Data both from `MySQL` and `redis` gets persisted on local storage.
So please don't forget to remove respective volumes when you stop using the app.

    It can be done with
    > docker volume rm redis data-volume


## Using API

API has several endpoints to request exchange rates update from Open Exchange Rate or
list currently availble exchanges.

Requesting exchange rate:

> curl http://0.0.0.0:5000/grab_and_save/$currency/$amount_to_change/

View last exchange rates:

* to get last exchange:
> curl http://0.0.0.0:5000/last/

* to get last N exchnges done:
> curl http://0.0.0.0:5000/last/$N/

* to get last exchange per currency:
> curl http://0.0.0.0:5000/last/$currency/

* to get last N exchanges per currency
> curl http://0.0.0.0:5000/last/$currency/$N/


