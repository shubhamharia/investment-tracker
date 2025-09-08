# Application-wide constants
DECIMAL_PLACES = 8

# Transaction types
TRANSACTION_TYPES = {
    'BUY': 'BUY',
    'SELL': 'SELL',
    'DIVIDEND': 'DIVIDEND',
    'SPLIT': 'SPLIT'
}

# Instrument types
INSTRUMENT_TYPES = {
    'STOCK': 'STOCK',
    'ETF': 'ETF',
    'FUND': 'FUND'
}

# Account types
ACCOUNT_TYPES = {
    'ISA': 'ISA',
    'GIA': 'GIA',
    'LISA': 'LISA',
    'SIPP': 'SIPP'
}

# Currency codes
CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD']

# Data sources
DATA_SOURCES = {
    'YAHOO': 'yahoo',
    'MANUAL': 'manual'
}

# Time periods
TIME_PERIODS = {
    'DAILY': 'daily',
    'WEEKLY': 'weekly',
    'MONTHLY': 'monthly',
    'YEARLY': 'yearly'
}

# Performance metrics
PERFORMANCE_METRICS = {
    'TOTAL_RETURN': 'total_return',
    'REALIZED_GAIN': 'realized_gain',
    'UNREALIZED_GAIN': 'unrealized_gain',
    'DIVIDEND_INCOME': 'dividend_income'
}

# Country codes for tax purposes
COUNTRY_CODES = {
    'UK': 'GB',
    'US': 'US',
    'EU': 'EU'
}

# Tax rates and thresholds (UK example)
TAX_RATES = {
    'UK': {
        'DIVIDEND_ALLOWANCE': 1000,
        'BASIC_RATE': 8.75,
        'HIGHER_RATE': 33.75,
        'ADDITIONAL_RATE': 39.35
    }
}

# Portfolio types
PORTFOLIO_TYPES = {
    'GROWTH': 'growth',
    'INCOME': 'income',
    'BALANCED': 'balanced'
}
