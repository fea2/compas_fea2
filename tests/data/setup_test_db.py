# setup_test_db.py
import sqlite3

def setup_test_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE U (
        step TEXT,
        part TEXT,
        key INTEGER,
        U1 REAL,
        U2 REAL,
        U3 REAL,
        magnitude REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE RF (
        step TEXT,
        part TEXT,
        key INTEGER,
        RF1 REAL,
        RF2 REAL,
        RF3 REAL,
        magnitude REAL
    )
    ''')

    # Insert test data
    cursor.executemany('''
    INSERT INTO U (step, part, key, U1, U2, U3, magnitude) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Step1', 'Part1', 1, 0.1, 0.2, 0.3, 0.374),
        ('Step1', 'Part1', 2, 0.4, 0.5, 0.6, 0.877),
        ('Step2', 'Part2', 3, 0.7, 0.8, 0.9, 1.204)
    ])

    cursor.executemany('''
    INSERT INTO RF (step, part, key, RF1, RF2, RF3, magnitude) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Step1', 'Part1', 1, 1.1, 1.2, 1.3, 2.1),
        ('Step1', 'Part1', 2, 1.4, 1.5, 1.6, 2.9),
        ('Step2', 'Part2', 3, 1.7, 1.8, 1.9, 3.4)
    ])

    conn.commit()
    conn.close()
