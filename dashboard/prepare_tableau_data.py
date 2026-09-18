import csv
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CUSTOMER_SOURCE = PROCESSED_DIR / "customer_churn_clean.csv"
RETENTION_SOURCE = PROCESSED_DIR / "customer_retention_priorities.csv"

TABLEAU_CUSTOMER_OUTPUT = PROCESSED_DIR / "tableau_customer_data.csv"
TABLEAU_RETENTION_OUTPUT = PROCESSED_DIR / "tableau_retention_data.csv"


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        return list(csv.DictReader(csv_file))


def write_rows(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def age_band(age_value):
    age = int(float(age_value))

    if age < 30:
        return "Under 30"
    if age <= 39:
        return "30-39"
    if age <= 49:
        return "40-49"
    if age <= 59:
        return "50-59"
    return "60+"


def tenure_band(tenure_value):
    # Simple tenure bands used for dashboard grouping: 0-2, 3-5, 6-8, and 9-10 years.
    tenure = int(float(tenure_value))

    if tenure <= 2:
        return "0-2 years"
    if tenure <= 5:
        return "3-5 years"
    if tenure <= 8:
        return "6-8 years"
    return "9-10 years"


def prepare_customer_data():
    tableau_customers = read_rows(CUSTOMER_SOURCE)

    for row in tableau_customers:
        row["age_band"] = age_band(row["age"])
        row["tenure_band"] = tenure_band(row["tenure"])
        row["activity_status"] = "Active" if row["is_active_member"] == "1" else "Inactive"
        row["churn_status"] = "Churned" if row["exited"] == "1" else "Retained"

    fieldnames = list(tableau_customers[0].keys())
    write_rows(TABLEAU_CUSTOMER_OUTPUT, tableau_customers, fieldnames)
    return tableau_customers


def prepare_retention_data():
    tableau_retention = read_rows(RETENTION_SOURCE)

    for row in tableau_retention:
        row["age_band"] = age_band(row["Age"])
        row["activity_status"] = "Active" if row["IsActiveMember"] == "1" else "Inactive"
        row["actual_churn_status"] = "Churned" if row["ActualExited"] == "1" else "Retained"

    fieldnames = list(tableau_retention[0].keys())
    write_rows(TABLEAU_RETENTION_OUTPUT, tableau_retention, fieldnames)
    return tableau_retention


def validate_outputs(tableau_customers, tableau_retention):
    customer_ids = [row["customer_id"] for row in tableau_customers]
    retention_ids = [row["CustomerId"] for row in tableau_retention]
    customer_duplicates = len(customer_ids) - len(set(customer_ids))
    retention_duplicates = len(retention_ids) - len(set(retention_ids))
    customer_churn_counts = Counter(row["churn_status"] for row in tableau_customers)
    retention_churn_counts = Counter(row["ActualExited"] for row in tableau_retention)
    retention_priority_counts = Counter(row["RetentionPriority"] for row in tableau_retention)

    print("Tableau customer data:", TABLEAU_CUSTOMER_OUTPUT)
    print("Rows:", len(tableau_customers), "Columns:", len(tableau_customers[0]))
    print("Duplicate customer_id:", int(customer_duplicates))
    print("Churn status counts:", dict(customer_churn_counts))
    print()
    print("Tableau retention data:", TABLEAU_RETENTION_OUTPUT)
    print("Rows:", len(tableau_retention), "Columns:", len(tableau_retention[0]))
    print("Duplicate CustomerId:", int(retention_duplicates))
    print("ActualExited counts:", dict(retention_churn_counts))
    print("Retention priority counts:", dict(retention_priority_counts))


def main():
    tableau_customers = prepare_customer_data()
    tableau_retention = prepare_retention_data()
    validate_outputs(tableau_customers, tableau_retention)


if __name__ == "__main__":
    main()
