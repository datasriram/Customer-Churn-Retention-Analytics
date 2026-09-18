import csv
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Customer-Churn-Records.csv"
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "customer_churn.db"
CLEAN_CSV_PATH = PROJECT_ROOT / "data" / "processed" / "customer_churn_clean.csv"


COLUMNS = [
    ("CustomerId", "customer_id", "INTEGER", int),
    ("CreditScore", "credit_score", "INTEGER", int),
    ("Geography", "geography", "TEXT", str),
    ("Gender", "gender", "TEXT", str),
    ("Age", "age", "INTEGER", int),
    ("Tenure", "tenure", "INTEGER", int),
    ("Balance", "balance", "REAL", float),
    ("NumOfProducts", "num_of_products", "INTEGER", int),
    ("HasCrCard", "has_cr_card", "INTEGER", int),
    ("IsActiveMember", "is_active_member", "INTEGER", int),
    ("EstimatedSalary", "estimated_salary", "REAL", float),
    ("Satisfaction Score", "satisfaction_score", "INTEGER", int),
    ("Card Type", "card_type", "TEXT", str),
    ("Point Earned", "points_earned", "INTEGER", int),
    ("Exited", "exited", "INTEGER", int),
]


def load_clean_rows():
    clean_rows = []

    with RAW_DATA_PATH.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            clean_rows.append({
                sql_column: converter(row[raw_column])
                for raw_column, sql_column, _, converter in COLUMNS
            })

    return clean_rows


def write_clean_csv(rows):
    fieldnames = [sql_column for _, sql_column, _, _ in COLUMNS]

    with CLEAN_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_rows = load_clean_rows()
    column_definitions = ", ".join(
        f"{sql_column} {sqlite_type}"
        for _, sql_column, sqlite_type, _ in COLUMNS
    )
    sql_columns = [sql_column for _, sql_column, _, _ in COLUMNS]
    placeholders = ", ".join(["?"] * len(sql_columns))

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("DROP TABLE IF EXISTS customers")
        connection.execute(f"CREATE TABLE customers ({column_definitions})")
        connection.executemany(
            f"INSERT INTO customers ({', '.join(sql_columns)}) VALUES ({placeholders})",
            [[row[column] for column in sql_columns] for row in clean_rows],
        )
        connection.commit()

    write_clean_csv(clean_rows)

    print(f"Created SQLite database: {DATABASE_PATH}")
    print(f"Created clean customer CSV: {CLEAN_CSV_PATH}")
    print(f"Rows loaded: {len(clean_rows)}")


if __name__ == "__main__":
    main()
