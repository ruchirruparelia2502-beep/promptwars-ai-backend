"""
Persistent SQLite-Backed Datastore Interface for LabLink
Re-exports the thread-safe, date-partitioned SQLite engine from app.core.db_sqlite.
Maintains 100% backward compatibility for all routers and services while providing:
- True date-partitioned bitmask availability
- BookMyShow 10-Minute Hold expiration & auto-release
- Verified server-side student profiles against client spoofing
- Response caching for GenAI models
"""

from app.core.db_sqlite import db, SQLiteLabDatabase

# Legacy alias for backward compatibility
InMemoryLabDatabase = SQLiteLabDatabase

__all__ = ["db", "SQLiteLabDatabase", "InMemoryLabDatabase"]
