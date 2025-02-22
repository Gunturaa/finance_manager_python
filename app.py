from flask import Flask, render_template, request, redirect, url_for, send_file, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import mysql.connector
from datetime import datetime
import pandas as pd
from datetime import date 
from io import BytesIO
import logging
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Fungsi untuk koneksi ke database
def connect_to_database():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="",  
        database="finance_manager"
    )

# Route untuk halaman utama
@app.route('/')
def index():
    return render_template('index.html')

# Route untuk menambahkan transaksi
@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        transaction_type = request.form['type']

        db = connect_to_database()
        cursor = db.cursor()
        query = "INSERT INTO transactions (date, description, amount, category, type) VALUES (%s, %s, %s, %s, %s)"
        values = (date, description, amount, category, transaction_type)
        logging.debug("Inserting transaction: date=%s, description=%s, amount=%s, category=%s, type=%s", date, description, amount, category, transaction_type)
        cursor.execute(query, values)
        logging.debug("Inserted transaction: %s", values)  # Log the inserted transaction
        logging.debug("Transaction inserted successfully.")
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('view_transactions'))
    return render_template('add_transaction.html')
# Fungsi untuk mengambil transaksi dari database
def get_transactions():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT id, date, description, amount, category, type FROM transactions")
    transactions = cursor.fetchall()
    cursor.close()
    db.close()
    return transactions

# Route untuk download laporan transaksi sebagai PDF
@app.route('/download_pdf')
def download_pdf():
    transactions = get_transactions()
    pdf_filename = "transaksi.pdf"

    # Buat file PDF
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter
    y_position = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y_position, "Laporan Transaksi Keuangan")
    y_position -= 30

    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "ID")
    c.drawString(100, y_position, "Tanggal")
    c.drawString(200, y_position, "Deskripsi")
    c.drawString(350, y_position, "Jumlah")
    c.drawString(450, y_position, "Kategori")
    c.drawString(520, y_position, "Jenis")
    y_position -= 20
    c.line(50, y_position, 550, y_position)
    y_position -= 20

    for transaction in transactions:
        if y_position < 50:  # Jika terlalu bawah, buat halaman baru
            c.showPage()
            y_position = height - 50

        c.drawString(50, y_position, str(transaction[0]))
        c.drawString(100, y_position, str(transaction[1]))
        c.drawString(200, y_position, transaction[2])
        c.drawString(350, y_position, f"Rp {transaction[3]:,.0f}")
        c.drawString(450, y_position, transaction[4])
        c.drawString(520, y_position, transaction[5])
        y_position -= 20

    c.save()

    # Log the file path
    logging.debug("PDF file created: %s", os.path.abspath(pdf_filename))

    return send_file(pdf_filename, as_attachment=True)

@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    db = connect_to_database()
    cursor = db.cursor()
    if request.method == 'POST':
        date = request.form['date']
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        transaction_type = request.form['type']

        query = "UPDATE transactions SET date=%s, description=%s, amount=%s, category=%s, type=%s WHERE id=%s"
        values = (date, description, amount, category, transaction_type, transaction_id)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('view_transactions'))
    else:
        cursor.execute("SELECT * FROM transactions WHERE id=%s", (transaction_id,))
        transaction = cursor.fetchone()
        cursor.close()
        db.close()
        return render_template('edit_transaction.html', transaction=transaction)


# Route untuk melihat semua transaksi
@app.route('/view')
def view_transactions():
    db = connect_to_database()
    cursor = db.cursor()

    # Ambil semua transaksi
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    
    print("Fetched transactions:", transactions)  # Debugging output

    # Hitung jumlah transaksi hari ini
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE date = %s", (today,))
    total_today = cursor.fetchone()[0] or 0  # Jika NULL, set ke 0

    cursor.close()
    db.close()

    return render_template('view_transactions.html', transactions=transactions, total_today=total_today)




# Route untuk menghitung saldo
@app.route('/balance')
def calculate_balance():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0] or 0
    balance = total_income - total_expense
    cursor.close()
    db.close()
    return f"Saldo Anda saat ini: {balance}"

# Route untuk menambahkan tagihan rutin
@app.route('/add_bill', methods=['GET', 'POST'])
def add_bill():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        due_date = request.form['due_date']

        db = connect_to_database()
        cursor = db.cursor()
        query = "INSERT INTO bills (name, amount, due_date) VALUES (%s, %s, %s)"
        values = (name, amount, due_date)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('view_bills'))
    return render_template('add_bill.html')

# Route untuk melihat tagihan rutin
@app.route('/view_bills')
def view_bills():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM bills")
    bills = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('view_bills.html', bills=bills)

# Route untuk menambahkan anggaran bulanan
@app.route('/add_budget', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        month = request.form['month']

        db = connect_to_database()
        cursor = db.cursor()
        query = "INSERT INTO budgets (category, amount, month) VALUES (%s, %s, %s)"
        values = (category, amount, month)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('view_budgets'))
    return render_template('add_budget.html')

# Route untuk melihat anggaran bulanan
@app.route('/view_budgets')
def view_budgets():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM budgets")
    budgets = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('view_budgets.html', budgets=budgets)

# Route untuk menambahkan hutang-piutang
@app.route('/add_debt', methods=['GET', 'POST'])
def add_debt():
    if request.method == 'POST':
        person = request.form['person']
        amount = float(request.form['amount'])
        debt_type = request.form['type']

        db = connect_to_database()
        cursor = db.cursor()
        query = "INSERT INTO debts (person, amount, type) VALUES (%s, %s, %s)"
        values = (person, amount, debt_type)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()
        return redirect(url_for('view_debts'))
    return render_template('add_debt.html')

# Route untuk melihat hutang-piutang
@app.route('/view_debts')
def view_debts():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM debts")
    debts = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('view_debts.html', debts=debts)

# Route untuk download pengeluaran ke Excel
@app.route('/download_excel')
def download_excel():
    db = connect_to_database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    cursor.close()
    db.close()

    # Convert to DataFrame
    df = pd.DataFrame(transactions, columns=["ID", "Tanggal", "Deskripsi", "Jumlah", "Kategori", "Jenis"])
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pengeluaran')
    output.seek(0)

    return send_file(output, download_name="pengeluaran.xlsx", as_attachment=True)

@app.route('/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    db = connect_to_database()
    cursor = db.cursor()
    
    query = "DELETE FROM transactions WHERE id = %s"
    cursor.execute(query, (transaction_id,))
    db.commit()
    
    cursor.close()
    db.close()
    
    return redirect(url_for('view_transactions'))


if __name__ == '__main__':
    app.run(debug=True)
