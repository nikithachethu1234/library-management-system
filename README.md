# LibriVerse - Complete Library Management System

A full-stack, responsive, production-ready Library Management System built with **Python**, **Flask**, **SQLite**, and **Bootstrap 5**.

![LibriVerse](https://img.shields.io/badge/Python-3.13-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)
![Database](https://img.shields.io/badge/SQLite-Integrated-orange.svg)
![UI](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

---

## 🌟 Key Features

### 🔐 Authentication & Role-Based Access Control
- **Two Distinct Roles**: `Admin` and `User` (Library Member).
- **Secure Password Hashing**: Werkzeug's PBKDF2/SHA256 password hashing.
- **Session-Protected Routes**: Role-specific navigation, redirects, and unauthorized access guards.
- **Self-Service Registration**: New members can register for an account directly.
- **1-Click Demo Login Presets**: Dedicated quick-fill buttons for demo credentials on the sign-in screen.

### 🛡️ Admin Capabilities
- **Overview Dashboard**:
  - Key circulation metrics (Total Titles, Total Copies, Available Copies, Currently Issued, Overdue Books, Total Members).
  - Real-time recent circulation stream with one-click return processing.
  - Category collection distribution.
- **Book Management (CRUD)**:
  - Add new books with ISBN, title, author, category, total copies, and description.
  - Search & filter books by keyword or category.
  - Edit existing book details and copy balances.
  - Delete books (with validation preventing deletion of actively loaned copies).
- **Circulation Desk (Issue & Return)**:
  - Issue books to any member with a customizable loan duration (default 14 days).
  - Filter transactions by status: `All`, `Borrowed`, `Overdue`, `Returned`.
  - Accept book returns and automatically compute overdue penalty fines ($2.00/day).
- **Member Directory**:
  - View all registered members and their active borrowing counts.
  - Deep-dive into any member's complete loan history.

### 👤 Member (User) Capabilities
- **Member Dashboard**:
  - Live summary of active loans, returned books, overdue warnings, and fines.
  - Automatic overdue alert banners.
  - Borrowing guidelines and quick catalog search.
- **Browse Catalog**:
  - Responsive card grid of all books with live availability tags.
  - Real-time search by title, author, category, and ISBN.
  - One-click **Borrow** action for available titles (up to 5 active loans).
- **My Borrowed Books**:
  - Track return deadlines with due date highlights.
  - One-click **Return Book** feature.
  - Complete reading history log.

---

## 🔑 Default Login Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full administrative control & book catalog management |
| **Member** | `john_doe` | `user123` | Demo member with active and returned loan history |
| **Member** | `jane_smith` | `user123` | Demo member with sample overdue book and fine calculation |

*(You can also use the **Demo Admin** or **Member Demo** quick-fill buttons on the login page, or register a new member account via `/register`)*.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+ installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database (Optional — auto-initializes on startup)
```bash
python database.py
```
*Creates `library.db` and populates sample books, users, and transactions if not present.*

### 4. Run the Application
```bash
python app.py
```
The server will start on **`http://127.0.0.1:5000`**.

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the complete automated test suite covering authentication, book CRUD, borrowing, returns, and route security:

```bash
python test_app.py
```

---

## 📁 Project Structure

```text
library management system/
├── app.py                   # Main Flask application with routes and controllers
├── database.py              # SQLite database schema, connections, and initial seed data
├── models.py                # Database queries for users, books, circulations, and analytics
├── requirements.txt         # Python dependencies (Flask, Werkzeug)
├── test_app.py              # Automated test suite (5 comprehensive unit & integration tests)
├── README.md                # Project documentation
├── static/
│   ├── css/
│   │   └── style.css        # Responsive styling, modern color theme, badges, and layout
│   └── js/
│       └── main.js          # Dynamic modals, fast search filtering, and auto-dismiss alerts
└── templates/
    ├── base.html            # Main template with role-aware sidebar and responsive header
    ├── login.html           # Login screen with quick-fill demo presets
    ├── register.html        # New member account registration
    ├── admin/
    │   ├── dashboard.html   # Admin metrics, quick actions, recent circulation table
    │   ├── books.html       # Book management table with Add/Edit/Delete modals
    │   ├── issue_return.html# Issue book form and circulation transaction management
    │   ├── users.html       # Member directory with borrowing quotas
    │   └── user_details.html# Member profile and borrowing history log
    └── user/
        ├── dashboard.html   # Member loan overview, overdue alert banners
        ├── books.html       # Book catalog grid with search and direct borrow action
        └── my_books.html    # Active loans with return button and transaction history
```

---

## ⚙️ Technologies Used

- **Backend**: Python 3.13, Flask 3.1.3, Werkzeug 3.1.8
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3.3, Bootstrap Icons 1.11.3
- **Fonts**: Inter (Google Fonts)
