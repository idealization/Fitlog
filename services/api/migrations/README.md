# Migrations

U5 adds SQLAlchemy models, Alembic configuration, and a database initialization path using `Base.metadata.create_all` for local development and tests.

Local/test app startup uses metadata initialization so the API remains easy to run. Deployed environments should use Alembic revisions instead.

From the repository root:

```bash
FITLOG_DATABASE_URL=sqlite:///./fitlog.db .venv/bin/alembic -c services/api/alembic.ini upgrade head
```

