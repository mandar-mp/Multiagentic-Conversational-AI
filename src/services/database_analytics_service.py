"""Safe analytics database access for SQL-based insights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import logging
import re
import time

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


FORBIDDEN_SQL_PATTERNS = [
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bmerge\b",
    r"\bcall\b",
    r"\bexecute\b",
    r"\bexec\b",
]


@dataclass
class SQLValidationResult:
    """Validation result for generated SQL."""

    valid: bool
    sql: str
    reason: Optional[str] = None
    tables: Optional[List[str]] = None


class DatabaseAnalyticsService:
    """Schema inspection, SQL validation, and read-only execution."""

    def __init__(
        self,
        db_url: Optional[str],
        dialect: Optional[str] = None,
        allowed_tables: Optional[List[str]] = None,
        blocked_tables: Optional[List[str]] = None,
        max_rows: int = 200,
        query_timeout: int = 30,
        echo: bool = False,
    ):
        self.db_url = db_url
        self.dialect = dialect
        self.allowed_tables = set(allowed_tables or [])
        self.blocked_tables = set(blocked_tables or [])
        self.max_rows = max(1, max_rows)
        self.query_timeout = query_timeout
        self.echo = echo
        self._engine: Optional[Engine] = None

    @property
    def configured(self) -> bool:
        """Return whether analytics database access is configured."""
        return bool(self.db_url)

    @property
    def engine(self) -> Engine:
        """Create the SQLAlchemy engine lazily."""
        if not self.db_url:
            raise RuntimeError("Analytics database is not configured.")
        if self._engine is None:
            connect_args: Dict[str, Any] = {}
            if self.db_url.startswith("sqlite"):
                connect_args["check_same_thread"] = False
            self._engine = create_engine(
                self.db_url,
                connect_args=connect_args,
                future=True,
                echo=self.echo,
            )
        return self._engine

    def get_dialect(self) -> str:
        """Return the configured or detected SQL dialect."""
        if self.dialect:
            return self.dialect
        if not self.configured:
            return "unknown"
        return self.engine.dialect.name

    def get_schema_context(self) -> Dict[str, Any]:
        """Return allowed schema metadata for prompt grounding."""
        if not self.configured:
            return {
                "configured": False,
                "dialect": self.get_dialect(),
                "tables": [],
                "message": "Analytics database is not configured.",
            }

        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        visible_tables = [
            table
            for table in table_names
            if self._table_allowed(table)
        ]

        tables = []
        for table_name in visible_tables:
            columns = [
                {
                    "name": column["name"],
                    "type": str(column.get("type")),
                    "nullable": bool(column.get("nullable", True)),
                }
                for column in inspector.get_columns(table_name)
            ]
            foreign_keys = [
                {
                    "columns": fk.get("constrained_columns") or [],
                    "referred_table": fk.get("referred_table"),
                    "referred_columns": fk.get("referred_columns") or [],
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]
            tables.append(
                {
                    "name": table_name,
                    "columns": columns,
                    "foreign_keys": foreign_keys,
                }
            )

        return {
            "configured": True,
            "dialect": self.get_dialect(),
            "max_rows": self.max_rows,
            "tables": tables,
        }

    def validate_sql(self, sql: str) -> SQLValidationResult:
        """Validate generated SQL before execution."""
        normalized = self._normalize_sql(sql)
        if not normalized:
            return SQLValidationResult(False, "", "SQL was empty.")

        if ";" in normalized[:-1]:
            return SQLValidationResult(False, normalized, "Only one SQL statement is allowed.")

        cleaned = normalized.rstrip(";").strip()
        lowered = cleaned.lower()
        if not (lowered.startswith("select") or lowered.startswith("with")):
            return SQLValidationResult(False, cleaned, "Only read-only SELECT queries are allowed.")

        for pattern in FORBIDDEN_SQL_PATTERNS:
            if re.search(pattern, lowered):
                return SQLValidationResult(False, cleaned, "SQL contains a forbidden operation.")

        referenced_tables = self._extract_referenced_tables(cleaned)
        for table in referenced_tables:
            if not self._table_allowed(table):
                return SQLValidationResult(False, cleaned, f"Table '{table}' is not allowed.")

        limited_sql = self._apply_limit(cleaned)
        return SQLValidationResult(True, limited_sql, tables=referenced_tables)

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute validated SQL and return rows with metadata."""
        validation = self.validate_sql(sql)
        if not validation.valid:
            return {
                "status": "blocked",
                "message": validation.reason,
                "sql": validation.sql,
                "rows": [],
                "columns": [],
            }

        started_at = time.perf_counter()
        with self.engine.connect() as connection:
            result = connection.execute(text(validation.sql))
            rows = result.fetchmany(self.max_rows)
            columns = list(result.keys())

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        serialized_rows = [
            {
                column: self._serialize_value(value)
                for column, value in zip(columns, row)
            }
            for row in rows
        ]
        return {
            "status": "success",
            "message": f"Query returned {len(serialized_rows)} row(s).",
            "sql": validation.sql,
            "tables": validation.tables or [],
            "columns": columns,
            "rows": serialized_rows,
            "row_count": len(serialized_rows),
            "duration_ms": duration_ms,
        }

    def _table_allowed(self, table_name: str) -> bool:
        if table_name in self.blocked_tables:
            return False
        if self.allowed_tables and table_name not in self.allowed_tables:
            return False
        return True

    def _apply_limit(self, sql: str) -> str:
        if re.search(r"\blimit\s+\d+\b", sql, flags=re.IGNORECASE):
            return sql
        return f"{sql.rstrip(';')} LIMIT {self.max_rows}"

    @staticmethod
    def _normalize_sql(sql: str) -> str:
        sql = re.sub(r"```(?:sql)?", "", sql, flags=re.IGNORECASE).replace("```", "")
        return sql.strip()

    @staticmethod
    def _extract_referenced_tables(sql: str) -> List[str]:
        table_names = []
        for pattern in [r"\bfrom\s+([a-zA-Z_][\w\.]*)", r"\bjoin\s+([a-zA-Z_][\w\.]*)"]:
            for match in re.findall(pattern, sql, flags=re.IGNORECASE):
                table_names.append(match.split(".")[-1])
        return list(dict.fromkeys(table_names))

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)
