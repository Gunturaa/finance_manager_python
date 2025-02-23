from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import mysql.connector
from datetime import datetime
import pandas as pd
from datetime import date 
from io import BytesIO
import logging
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b'%\x15\xf8\xa7\xbf\xa79\xa9\x16\xa22\x91\xb6\x1eJI\xb9\xa3\x993O\xcfPm'  # Secret key yang dihasilkan

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

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
        
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
    
    # Get total income
    cursor.execute("SELECT SUM(amount) AS total_income FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()['total_income'] or 0
    
    # Get total expenses
    cursor.execute("SELECT SUM(amount) AS total_expenses FROM transactions WHERE type = 'expense'")
    total_expenses = cursor.fetchone()['total_expenses'] or 0
    
    # Calculate current balance
    current_balance = total_income - total_expenses
    
    # Get recent transactions
    cursor.execute("SELECT date, description, amount, type FROM transactions ORDER BY date DESC LIMIT 5")
    recent_transactions = cursor.fetchall()
    
    # Get data for chart
    cursor.execute("SELECT date, SUM(amount) AS amount FROM transactions WHERE type = 'income' GROUP BY date ORDER BY date")
    income_data = cursor.fetchall()
    cursor.execute("SELECT date, SUM(amount) AS amount FROM transactions WHERE type = 'expense' GROUP BY date ORDER BY date")
    expenses_data = cursor.fetchall()
    
    labels = [data['date'] for data in income_data]
    income_values = [data['amount'] for data in income_data]
    expenses_values = [data['amount'] for data in expenses_data]
    
    cursor.close()
    db.close()
    
    return render_template('dashboard.html', total_income=total_income, total_expenses=total_expenses, current_balance=current_balance, recent_transactions=recent_transactions, labels=labels, income_data=income_values, expenses_data=expenses_values)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = connect_to_database()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))



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

    total_expenses = 0

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

        if transaction[5] == 'expense':
            total_expenses += transaction[3]

    y_position -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_position, f"Total Pengeluaran: Rp {total_expenses:,.0f}")

    c.save()

    # Log the file path
    logging.debug("PDF file created: %s", os.path.abspath(pdf_filename))

    return send_file(pdf_filename, as_attachment=True)


@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
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

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    db = connect_to_database()
    cursor = db.cursor()
    query = "DELETE FROM transactions WHERE id = %s"
    cursor.execute(query, (transaction_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_transactions'))

# Route untuk melihat semua transaksi
@app.route('/view_transactions')
def view_transactions():
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, date, description, amount, type FROM transactions")
    transactions = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('view_transactions.html', transactions=transactions)

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
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
        
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
    
    # Fetch bills from the database
    cursor.execute("SELECT id, name, amount, due_date FROM bills")
    bills = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('view_bills.html', bills=bills)

@app.route('/edit_bill/<int:bill_id>', methods=['POST'])
def edit_bill(bill_id):
    is_paid = request.form['is_paid']
    db = connect_to_database()
    cursor = db.cursor()
    query = "UPDATE bills SET is_paid = %s WHERE id = %s"
    values = (is_paid, bill_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_bills'))

@app.route('/delete_bill/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    db = connect_to_database()
    cursor = db.cursor()
    query = "DELETE FROM bills WHERE id = %s"
    cursor.execute(query, (bill_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_bills'))

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
    cursor.execute("SELECT id, category, amount, month FROM budgets")
    budgets = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('view_budgets.html', budgets=budgets)

@app.route('/edit_budget/<int:budget_id>', methods=['POST'])
def edit_budget(budget_id):
    category = request.form['category']
    amount = request.form['amount']
    month = request.form['month']
    db = connect_to_database()
    cursor = db.cursor()
    query = "UPDATE budgets SET category = %s, amount = %s, month = %s WHERE id = %s"
    values = (category, amount, month, budget_id)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_budgets'))

@app.route('/delete_budget/<int:budget_id>', methods=['POST'])
def delete_budget(budget_id):
    db = connect_to_database()
    cursor = db.cursor()
    query = "DELETE FROM budgets WHERE id = %s"
    cursor.execute(query, (budget_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_budgets'))

# Route untuk menambahkan hutang-piutang
@app.route('/add_debt', methods=['GET', 'POST'])
def add_debt():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        person = request.form['person']
        amount = request.form['amount']
        debt_type = request.form['type']
        
        db = connect_to_database()
        cursor = db.cursor()
        query = "INSERT INTO debts (person, amount, type) VALUES (%s, %s, %s)"
        values = (person, amount, debt_type)
        cursor.execute(query, values)
        db.commit()
        cursor.close()
        db.close()
        
        flash('Debt added successfully!', 'success')
        return redirect(url_for('view_debts'))
    
    return render_template('add_debt.html')

# Route untuk melihat hutang/piutang
@app.route('/view_debts')
def view_debts():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
        
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
    
    # Fetch debts from the database
    cursor.execute("SELECT id, person, amount, type, is_paid FROM debts")
    debts = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('view_debts.html', debts=debts)

@app.route('/edit_debt/<int:debt_id>', methods=['GET', 'POST'])
def edit_debt(debt_id):
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))
    
    db = connect_to_database()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        person = request.form['person']
        amount = request.form['amount']
        debt_type = request.form['type']
        is_paid = request.form['is_paid']
        
        query = "UPDATE debts SET person = %s, amount = %s, type = %s, is_paid = %s WHERE id = %s"
        values = (person, amount, debt_type, is_paid, debt_id)
        cursor.execute(query, values)
        db.commit()
        
        cursor.close()
        db.close()
        
        flash('Debt updated successfully!', 'success')
        return redirect(url_for('view_debts'))
    
    # Fetch the debt details to pre-fill the form
    cursor.execute("SELECT id, person, amount, type, is_paid FROM debts WHERE id = %s", (debt_id,))
    debt = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    if debt is None:
        flash('Debt not found.', 'danger')
        return redirect(url_for('view_debts'))
    
    return render_template('edit_debt.html', debt=debt)

@app.route('/delete_debt/<int:debt_id>', methods=['POST'])
def delete_debt(debt_id):
    db = connect_to_database()
    cursor = db.cursor()
    query = "DELETE FROM debts WHERE id = %s"
    cursor.execute(query, (debt_id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for('view_debts'))

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
    
    # Calculate total expenses
    total_expenses = df[df['Jenis'] == 'expense']['Jumlah'].sum()

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Pengeluaran')
        workbook = writer.book
        worksheet = writer.sheets['Pengeluaran']
        worksheet.write(len(df) + 2, 0, 'Total Pengeluaran')
        worksheet.write(len(df) + 2, 1, f"Rp {total_expenses:,.0f}")
    output.seek(0)

    return send_file(output, download_name="pengeluaran.xlsx", as_attachment=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')  # Menggunakan metode hashing yang benar

        db = connect_to_database()
        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO user (username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
            db.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            db.close()

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
