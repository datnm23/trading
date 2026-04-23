#!/usr/bin/env python3
"""Export journal data from PostgreSQL to CSV/JSON for backup/analysis.

Usage:
    python scripts/export_journal.py --output-dir ./data/exports
    python scripts/export_journal.py --output-dir ./data/exports --format csv
    python scripts/export_journal.py --output-dir ./data/exports --format json
    python scripts/export_journal.py --output-dir ./data/exports --today-only

Set env var TRADING_DB_URL to override default connection string.
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor


DEFAULT_DB_URL = os.getenv(
    "TRADING_DB_URL",
    "postgresql://trader:trading123@localhost:5432/trading_journal"
)

TABLES = ["trades", "journal", "snapshots", "equity_snapshots", "wiki_feedback"]


def export_to_csv(cursor, table: str, output_path: Path):
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    if not rows:
        print(f"⚠️  {table}: no rows")
        return 0

    columns = [desc[0] for desc in cursor.description]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
    print(f"✅ {table}: {len(rows)} rows → {output_path}")
    return len(rows)


def export_to_json(cursor, table: str, output_path: Path):
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    if not rows:
        print(f"⚠️  {table}: no rows")
        return 0

    data = [dict(row) for row in rows]
    # Convert datetime to ISO strings for JSON serialization
    for row in data:
        for key, val in row.items():
            if isinstance(val, datetime):
                row[key] = val.isoformat()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"✅ {table}: {len(rows)} rows → {output_path}")
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description="Export trading journal from PostgreSQL")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL connection string")
    parser.add_argument("--output-dir", default="./data/exports", help="Output directory")
    parser.add_argument("--format", choices=["csv", "json", "both"], default="both",
                        help="Export format")
    parser.add_argument("--today-only", action="store_true",
                        help="Only export today's data (for daily snapshots)")
    parser.add_argument("--tables", nargs="+", default=TABLES,
                        help="Tables to export (default: all)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        conn = psycopg2.connect(args.db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    total_rows = 0
    for table in args.tables:
        # Optional: filter by today
        where_clause = ""
        suffix = ""
        if args.today_only:
            where_clause = f" WHERE DATE(timestamp) = '{today_str}'"
            suffix = f"_{today_str}"

        if args.format in ("csv", "both"):
            path = output_dir / f"{table}{suffix}_{timestamp}.csv"
            try:
                cursor.execute(f"SELECT * FROM {table}{where_clause}")
                total_rows += export_to_csv(cursor, table, path)
            except Exception as e:
                print(f"❌ Failed to export {table} to CSV: {e}")

        if args.format in ("json", "both"):
            path = output_dir / f"{table}{suffix}_{timestamp}.json"
            try:
                cursor.execute(f"SELECT * FROM {table}{where_clause}")
                total_rows += export_to_json(cursor, table, path)
            except Exception as e:
                print(f"❌ Failed to export {table} to JSON: {e}")

    cursor.close()
    conn.close()

    print(f"\n🎉 Export complete: {total_rows} total rows written to {output_dir}")


if __name__ == "__main__":
    main()
