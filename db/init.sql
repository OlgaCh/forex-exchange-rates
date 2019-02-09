CREATE DATABASE forex;
use forex;

CREATE TABLE exchange_rates (
  id int(11) NOT NULL AUTO_INCREMENT,
  timestamp INT,
  base VARCHAR(3),
  currency VARCHAR(3),
  rate FLOAT,
  original_amount FLOAT,
  converted_amount FLOAT,
  PRIMARY KEY (id)
);

ALTER TABLE exchange_rates ADD INDEX (timestamp);