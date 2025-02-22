import mysql.connector

def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="",  # Replace with your MySQL password
        database="finance_manager"
    )

def fetch_transactions():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    cursor.close()
    db.close()
    return transactions

if __name__ == "__main__":
    transactions = fetch_transactions()
    for transaction in transactions:
        print(transaction)
