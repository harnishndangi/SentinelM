"""
Migration script to update sentinelml.db SQLite model_versions table with registry columns.
"""
import sqlite3
from pathlib import Path

def migrate():
    db_path = Path("sentinelml.db")
    if not db_path.exists():
        print("sentinelml.db does not exist yet. It will be created with full schema on startup.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(model_versions)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("artifact_path", "VARCHAR(512)"),
        ("algorithm", "VARCHAR(100)"),
        ("dataset_version", "VARCHAR(50)"),
        ("training_run_id", "VARCHAR(255)"),
        ("metrics_summary", "JSON"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            print(f"Adding column '{col_name}' to 'model_versions' table...")
            cursor.execute(f"ALTER TABLE model_versions ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Database migration complete.")

if __name__ == "__main__":
    migrate()
