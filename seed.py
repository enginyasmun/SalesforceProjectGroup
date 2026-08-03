"""Initialize or safely migrate the Project Group database."""

import app as portal

portal._SCHEMA_READY = False
portal.ensure_schema()
print(f"Database ready: {portal.DB_PATH}")
print(f"Application version: {portal.APP_VERSION}")
