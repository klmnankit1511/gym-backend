"""Create the configured SQL Server database when it does not exist."""

import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import settings


def main() -> None:
    database_url = make_url(settings.database_url)
    database_name = database_url.database

    if not database_name or not re.fullmatch(r"[A-Za-z0-9_-]+", database_name):
        raise ValueError("DATABASE_URL must contain a safe database name")

    master_url = database_url.set(database="master")
    engine = create_engine(master_url, isolation_level="AUTOCOMMIT")

    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM sys.databases WHERE name = :name"),
                {"name": database_name},
            ).scalar()
            if not exists:
                escaped_name = database_name.replace("]", "]]")
                connection.exec_driver_sql(f"CREATE DATABASE [{escaped_name}]")
                print(f"Created database: {database_name}")
            else:
                print(f"Database already exists: {database_name}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
