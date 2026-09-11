import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

def get_db():
    """Establish and return a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables and populate sample seed data if empty."""
    conn = get_db()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create books table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT NOT NULL,
        total_copies INTEGER NOT NULL DEFAULT 1,
        available_copies INTEGER NOT NULL DEFAULT 1,
        description TEXT,
        published_year INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create borrow_records table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrow_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        borrow_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL DEFAULT 'borrowed',
        fine_amount REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Check if admin user exists, if not, populate seed data
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
    if cursor.fetchone()["count"] == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()

def seed_data(cursor):
    """Seed users, books, and sample transactions."""
    now = datetime.now()

    # Seed Admin and Demo Users
    users = [
        ("admin", generate_password_hash("admin123"), "System Administrator", "admin@library.local", "admin"),
        ("john_doe", generate_password_hash("user123"), "John Doe", "john@example.com", "user"),
        ("jane_smith", generate_password_hash("user123"), "Jane Smith", "jane@example.com", "user")
    ]

    cursor.executemany("""
    INSERT INTO users (username, password_hash, full_name, email, role)
    VALUES (?, ?, ?, ?, ?)
    """, users)

    # Seed Books
    sample_books = [
        (
            "978-0132350884",
            "Clean Code: A Handbook of Agile Software Craftsmanship",
            "Robert C. Martin",
            "Computer Science",
            5,
            4,
            "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees.",
            2008
        ),
        (
            "978-0201633610",
            "Design Patterns: Elements of Reusable Object-Oriented Software",
            "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
            "Computer Science",
            4,
            3,
            "Capturing a wealth of experience about the design of object-oriented software, four top-notch designers present a catalog of simple and succinct solutions.",
            1994
        ),
        (
            "978-0131103627",
            "The C Programming Language (2nd Edition)",
            "Brian W. Kernighan, Dennis M. Ritchie",
            "Programming",
            6,
            6,
            "The classic reference on C written by the developers of the language.",
            1988
        ),
        (
            "978-0596517748",
            "JavaScript: The Good Parts",
            "Douglas Crockford",
            "Web Development",
            3,
            3,
            "An authoritative dive into the elegant and robust parts of the JavaScript language.",
            2008
        ),
        (
            "978-0451524935",
            "1984",
            "George Orwell",
            "Classic Fiction",
            8,
            7,
            "The classic dystopian novel exploring totalitarianism, surveillance, and freedom of thought.",
            1949
        ),
        (
            "978-0061120084",
            "To Kill a Mockingbird",
            "Harper Lee",
            "Classic Fiction",
            5,
            5,
            "A timeless story of innocence, racism, compassion, and courage in the American South.",
            1960
        ),
        (
            "978-0743273565",
            "The Great Gatsby",
            "F. Scott Fitzgerald",
            "Literature",
            4,
            4,
            "The story of the fabulously wealthy Jay Gatsby and his new love for the beautiful Daisy Buchanan.",
            1925
        ),
        (
            "978-0385504201",
            "The Da Vinci Code",
            "Dan Brown",
            "Thriller",
            5,
            5,
            "A thrilling conspiracy novel centered on the Louvre, symbology, and secret religious history.",
            2003
        ),
        (
            "978-0062316097",
            "Sapiens: A Brief History of Humankind",
            "Yuval Noah Harari",
            "History",
            7,
            7,
            "Explores how biology and history have defined us and enhanced our understanding of what it means to be human.",
            2014
        ),
        (
            "978-0307887894",
            "The Lean Startup",
            "Eric Ries",
            "Business",
            4,
            4,
            "How today's entrepreneurs use continuous innovation to create radically successful businesses.",
            2011
        ),
        (
            "978-0143127741",
            "Thinking, Fast and Slow",
            "Daniel Kahneman",
            "Psychology",
            5,
            5,
            "Nobel laureate Daniel Kahneman takes us on an exploration of the two systems that drive the way we think.",
            2011
        ),
        (
            "978-0679783268",
            "Pride and Prejudice",
            "Jane Austen",
            "Romance",
            6,
            6,
            "Jane Austen's masterwork of manners, education, marriage, and money in 19th-century Britain.",
            1813
        )
    ]

    cursor.executemany("""
    INSERT INTO books (isbn, title, author, category, total_copies, available_copies, description, published_year)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_books)

    # Seed Sample Borrow Records
    # 1. John Doe borrowed Clean Code (active, due in 10 days)
    borrow_date_1 = (now - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
    due_date_1 = (now + timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")

    # 2. Jane Smith borrowed Design Patterns (overdue by 5 days, due date was 5 days ago)
    borrow_date_2 = (now - timedelta(days=19)).strftime("%Y-%m-%d %H:%M:%S")
    due_date_2 = (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
    fine_2 = 5 * 2.0  # $2 per day overdue = $10.00

    # 3. John Doe previously borrowed 1984 and returned it on time
    borrow_date_3 = (now - timedelta(days=25)).strftime("%Y-%m-%d %H:%M:%S")
    due_date_3 = (now - timedelta(days=11)).strftime("%Y-%m-%d %H:%M:%S")
    return_date_3 = (now - timedelta(days=12)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO borrow_records (book_id, user_id, borrow_date, due_date, return_date, status, fine_amount)
    VALUES (1, 2, ?, ?, NULL, 'borrowed', 0.0)
    """, (borrow_date_1, due_date_1))

    cursor.execute("""
    INSERT INTO borrow_records (book_id, user_id, borrow_date, due_date, return_date, status, fine_amount)
    VALUES (2, 3, ?, ?, NULL, 'overdue', ?)
    """, (borrow_date_2, due_date_2, fine_2))

    cursor.execute("""
    INSERT INTO borrow_records (book_id, user_id, borrow_date, due_date, return_date, status, fine_amount)
    VALUES (5, 2, ?, ?, ?, 'returned', 0.0)
    """, (borrow_date_3, due_date_3, return_date_3))

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
