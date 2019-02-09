from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class ExchangeRate(Base):
    """
    Exchange rates for different currencies vs USD
    """
    __tablename__ = 'exchange_rates'

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer, nullable=False)
    base = Column(String(3), nullable=False)
    currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    original_amount = Column(Float, nullable=False)
    converted_amount = Column(Float, nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'timestamp': self.timestamp,
            'base': self.base,
            'currency': self.currency,
            'rate': self.rate,
            'original_amount': self.original_amount,
            'converted_amount': self.converted_amount,
        }
