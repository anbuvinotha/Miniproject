import os

# Use PostgreSQL for your app
USE_POSTGRES = True

# PostgreSQL connection URI (using your password "root")
POSTGRES_URL = "postgresql+psycopg2://postgres:root@localhost:5432/smart_ai_cfo"

# SQLite fallback (not needed, but kept for development)
SQLITE_URL = "sqlite:///db/smart_ai_cfo.db"

# Decide which database to use
DATABASE_URL = POSTGRES_URL if USE_POSTGRES else SQLITE_URL
