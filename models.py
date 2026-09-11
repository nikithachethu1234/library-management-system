from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

FINE_RATE_PER_DAY = 2.0  # $2.00 per day overdue

# --- User Operations ---

def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)).fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),)).fetchone()
    conn.close()
    return user

def create_user(username, password, full_name, email, role="user"):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, email, role)
        VALUES (?, ?, ?, ?, ?)
        """, (username.strip(), password_hash, full_name.strip(), email.strip(), role))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def authenticate_user(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

def get_all_users():
    conn = get_db()
    users = conn.execute("""
    SELECT u.*,
           (SELECT COUNT(*) FROM borrow_records br WHERE br.user_id = u.id AND br.status IN ('borrowed', 'overdue')) AS active_borrows,
           (SELECT COUNT(*) FROM borrow_records br WHERE br.user_id = u.id) AS total_borrows
    FROM users u
    ORDER BY u.created_at DESC
    """).fetchall()
    conn.close()
    return users

# --- Book Operations ---

def get_all_books(search_query=None, category=None):
    conn = get_db()
    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if search_query:
        query_pattern = f"%{search_query.strip()}%"
        sql += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR description LIKE ?)"
        params.extend([query_pattern, query_pattern, query_pattern, query_pattern])

    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY title ASC"
    books = conn.execute(sql, params).fetchall()
    conn.close()
    return books

def get_book_by_id(book_id):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return book

def get_book_by_isbn(isbn):
    conn = get_db()
    book = conn.execute("SELECT * FROM books WHERE LOWER(isbn) = LOWER(?)", (isbn.strip(),)).fetchone()
    conn.close()
    return book

def get_all_categories():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT category FROM books ORDER BY category ASC").fetchall()
    conn.close()
    return [r["category"] for r in rows if r["category"]]

def add_book(isbn, title, author, category, total_copies, description="", published_year=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        total_copies = int(total_copies)
        available_copies = total_copies
        cursor.execute("""
        INSERT INTO books (isbn, title, author, category, total_copies, available_copies, description, published_year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (isbn.strip(), title.strip(), author.strip(), category.strip(), total_copies, available_copies, description.strip(), published_year))
        conn.commit()
        book_id = cursor.lastrowid
        return book_id, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def update_book(book_id, isbn, title, author, category, total_copies, description="", published_year=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        book = conn.execute("SELECT total_copies, available_copies FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            return False, "Book not found."

        total_copies = int(total_copies)
        difference = total_copies - book["total_copies"]
        new_available = book["available_copies"] + difference

        if new_available < 0:
            return False, f"Cannot reduce total copies below currently issued copies ({book['total_copies'] - book['available_copies']} copies are currently borrowed)."

        cursor.execute("""
        UPDATE books
        SET isbn = ?, title = ?, author = ?, category = ?, total_copies = ?, available_copies = ?, description = ?, published_year = ?
        WHERE id = ?
        """, (isbn.strip(), title.strip(), author.strip(), category.strip(), total_copies, new_available, description.strip(), published_year, book_id))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def delete_book(book_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check for active borrowings
        active = conn.execute("""
        SELECT COUNT(*) as count FROM borrow_records
        WHERE book_id = ? AND status IN ('borrowed', 'overdue')
        """, (book_id,)).fetchone()["count"]

        if active > 0:
            return False, f"Cannot delete book: {active} copies are currently borrowed and not yet returned."

        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Borrow & Return Operations ---

def refresh_overdue_statuses():
    """Scan and mark records as overdue if due_date has passed, and update accrued fine."""
    conn = get_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    now_dt = datetime.now()

    # Find active borrowings past due date
    records = conn.execute("""
    SELECT id, due_date FROM borrow_records
    WHERE status IN ('borrowed', 'overdue') AND due_date < ?
    """, (now_str,)).fetchall()

    for rec in records:
        due_dt = datetime.strptime(rec["due_date"], "%Y-%m-%d %H:%M:%S")
        days_overdue = max(0, (now_dt - due_dt).days)
        fine = round(days_overdue * FINE_RATE_PER_DAY, 2)
        conn.execute("""
        UPDATE borrow_records
        SET status = 'overdue', fine_amount = ?
        WHERE id = ?
        """, (fine, rec["id"]))

    conn.commit()
    conn.close()

def issue_book(book_id, user_id, days=14):
    """Issue a book to a user for a given number of days."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check book availability
        book = conn.execute("SELECT id, available_copies, title FROM books WHERE id = ?", (book_id,)).fetchone()
        if not book:
            return False, "Book not found."
        if book["available_copies"] <= 0:
            return False, f"No copies available for '{book['title']}'."

        # Check user exists
        user = conn.execute("SELECT id, full_name FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False, "User not found."

        # Check if user already has an active borrow of the same book
        existing = conn.execute("""
        SELECT id FROM borrow_records
        WHERE book_id = ? AND user_id = ? AND status IN ('borrowed', 'overdue')
        """, (book_id, user_id)).fetchone()
        if existing:
            return False, f"User already has an active issued copy of this book."

        # Check user borrowing limit (max 5 active books)
        active_count = conn.execute("""
        SELECT COUNT(*) as count FROM borrow_records
        WHERE user_id = ? AND status IN ('borrowed', 'overdue')
        """, (user_id,)).fetchone()["count"]
        if active_count >= 5:
            return False, "User has reached the maximum borrowing limit (5 books)."

        now = datetime.now()
        borrow_date = now.strftime("%Y-%m-%d %H:%M:%S")
        due_date = (now + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        # Create borrow record
        cursor.execute("""
        INSERT INTO borrow_records (book_id, user_id, borrow_date, due_date, status, fine_amount)
        VALUES (?, ?, ?, ?, 'borrowed', 0.0)
        """, (book_id, user_id, borrow_date, due_date))

        # Decrement available copies
        cursor.execute("""
        UPDATE books
        SET available_copies = available_copies - 1
        WHERE id = ?
        """, (book_id,))

        conn.commit()
        return True, "Book issued successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def return_book(record_id):
    """Process return of an issued book, calculate any overdue fine, and update available copies."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        record = conn.execute("""
        SELECT br.*, b.title
        FROM borrow_records br
        JOIN books b ON br.book_id = b.id
        WHERE br.id = ?
        """, (record_id,)).fetchone()

        if not record:
            return False, "Borrow record not found."

        if record["status"] == "returned":
            return False, "This book has already been marked as returned."

        now = datetime.now()
        return_date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        due_dt = datetime.strptime(record["due_date"], "%Y-%m-%d %H:%M:%S")

        fine = 0.0
        if now > due_dt:
            days_overdue = (now - due_dt).days
            if days_overdue > 0:
                fine = round(days_overdue * FINE_RATE_PER_DAY, 2)

        # Update record to returned
        cursor.execute("""
        UPDATE borrow_records
        SET return_date = ?, status = 'returned', fine_amount = ?
        WHERE id = ?
        """, (return_date_str, fine, record_id))

        # Increment available copies
        cursor.execute("""
        UPDATE books
        SET available_copies = available_copies + 1
        WHERE id = ?
        """, (record["book_id"],))

        conn.commit()
        fine_msg = f" Overdue fine: ${fine:.2f}." if fine > 0 else " Returned on time, no fine."
        return True, f"'{record['title']}' returned successfully.{fine_msg}"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_all_borrow_records(status_filter=None):
    conn = get_db()
    sql = """
    SELECT br.*, b.title as book_title, b.isbn, b.author, u.username, u.full_name as user_name, u.email
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    JOIN users u ON br.user_id = u.id
    """
    params = []
    if status_filter and status_filter != "all":
        sql += " WHERE br.status = ?"
        params.append(status_filter)

    sql += " ORDER BY br.id DESC"
    records = conn.execute(sql, params).fetchall()
    conn.close()
    return records

def get_borrow_record_by_id(record_id):
    conn = get_db()
    record = conn.execute("""
    SELECT br.*, b.title as book_title, b.author, u.username, u.full_name as user_name
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    JOIN users u ON br.user_id = u.id
    WHERE br.id = ?
    """, (record_id,)).fetchone()
    conn.close()
    return record

def get_user_borrows(user_id, active_only=False):
    conn = get_db()
    sql = """
    SELECT br.*, b.title as book_title, b.author, b.isbn, b.category
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    WHERE br.user_id = ?
    """
    params = [user_id]
    if active_only:
        sql += " AND br.status IN ('borrowed', 'overdue')"

    sql += " ORDER BY br.id DESC"
    records = conn.execute(sql, params).fetchall()
    conn.close()
    return records

# --- Dashboard & Analytics Operations ---

def get_admin_dashboard_stats():
    refresh_overdue_statuses()
    conn = get_db()

    total_books = conn.execute("SELECT COUNT(*) as count FROM books").fetchone()["count"]
    copies_row = conn.execute("SELECT SUM(total_copies) as total_copies, SUM(available_copies) as avail_copies FROM books").fetchone()
    total_copies = copies_row["total_copies"] or 0
    available_copies = copies_row["avail_copies"] or 0
    issued_copies = total_copies - available_copies

    total_users = conn.execute("SELECT COUNT(*) as count FROM users WHERE role = 'user'").fetchone()["count"]
    overdue_count = conn.execute("SELECT COUNT(*) as count FROM borrow_records WHERE status = 'overdue'").fetchone()["count"]
    total_fines = conn.execute("SELECT SUM(fine_amount) as total FROM borrow_records").fetchone()["total"] or 0.0

    recent_records = conn.execute("""
    SELECT br.*, b.title as book_title, u.full_name as user_name, u.username
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    JOIN users u ON br.user_id = u.id
    ORDER BY br.id DESC
    LIMIT 8
    """).fetchall()

    categories = conn.execute("""
    SELECT category, COUNT(*) as count, SUM(total_copies) as copies
    FROM books
    GROUP BY category
    ORDER BY count DESC
    """).fetchall()

    conn.close()

    return {
        "total_books": total_books,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "issued_copies": issued_copies,
        "total_users": total_users,
        "overdue_count": overdue_count,
        "total_fines": round(total_fines, 2),
        "recent_records": recent_records,
        "categories": categories
    }

def get_user_dashboard_stats(user_id):
    refresh_overdue_statuses()
    conn = get_db()

    active_borrows = conn.execute("""
    SELECT br.*, b.title as book_title, b.author, b.isbn, b.category
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    WHERE br.user_id = ? AND br.status IN ('borrowed', 'overdue')
    ORDER BY br.due_date ASC
    """, (user_id,)).fetchall()

    returned_count = conn.execute("""
    SELECT COUNT(*) as count FROM borrow_records
    WHERE user_id = ? AND status = 'returned'
    """, (user_id,)).fetchone()["count"]

    overdue_count = sum(1 for b in active_borrows if b["status"] == "overdue")
    total_fines = conn.execute("""
    SELECT SUM(fine_amount) as total FROM borrow_records
    WHERE user_id = ?
    """, (user_id,)).fetchone()["total"] or 0.0

    recent_history = conn.execute("""
    SELECT br.*, b.title as book_title, b.author
    FROM borrow_records br
    JOIN books b ON br.book_id = b.id
    WHERE br.user_id = ?
    ORDER BY br.id DESC
    LIMIT 6
    """, (user_id,)).fetchall()

    conn.close()

    return {
        "active_borrows": active_borrows,
        "active_count": len(active_borrows),
        "returned_count": returned_count,
        "overdue_count": overdue_count,
        "total_fines": round(total_fines, 2),
        "recent_history": recent_history
    }
