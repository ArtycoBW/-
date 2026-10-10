"""Set the isolated database before any test module imports application code."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./.local/test.db"
os.environ["DEMO_MODE"] = "true"
