"""
Data gathering and processing
"""
import pandas as pd
import sqlalchemy

from app.cache_config import cache_timeout, appcache
from app.time_config import *

# postgresql://admin:admin@localhost:5432/ibnse
engine = sqlalchemy.create_engine(getenv("DATABASE_URL"))

