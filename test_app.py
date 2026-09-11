import os
import unittest
from datetime import datetime, timedelta
from app import app
import database
import models

class LibrarySystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        # Initialize fresh database state
        database.init_db()

    def test_01_authentication_models(self):
        """Test authentication for admin and user models."""
        admin = models.authenticate_user("admin", "admin123")
        self.assertIsNotNone(admin)
        self.assertEqual(admin["role"], "admin")

        user = models.authenticate_user("john_doe", "user123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "user")

        invalid = models.authenticate_user("admin", "wrongpassword")
        self.assertIsNone(invalid)

    def test_02_book_crud_lifecycle(self):
        """Test Add, Search, Update, and Delete for books."""
        # 1. Add Book
        isbn = "978-9999999999"
        title = "Test Automated Book"
        author = "Test Author"
        category = "Computer Science"
        total_copies = 4
        book_id, err = models.add_book(isbn, title, author, category, total_copies, "Test Description", 2024)
        self.assertIsNone(err)
        self.assertIsNotNone(book_id)

        # 2. Search Book
        search_results = models.get_all_books(search_query="Automated")
        self.assertTrue(any(b["id"] == book_id for b in search_results))

        # 3. Update Book
        updated, err = models.update_book(book_id, isbn, "Test Automated Book Updated", author, category, 6, "Updated Description", 2025)
        self.assertTrue(updated)
        updated_book = models.get_book_by_id(book_id)
        self.assertEqual(updated_book["title"], "Test Automated Book Updated")
        self.assertEqual(updated_book["total_copies"], 6)
        self.assertEqual(updated_book["available_copies"], 6)

        # 4. Delete Book
        deleted, err = models.delete_book(book_id)
        self.assertTrue(deleted)
        self.assertIsNone(models.get_book_by_id(book_id))

    def test_03_issue_and_return_lifecycle(self):
        """Test issuing a book and returning it with copy balance tracking."""
        # Add a single-copy book
        isbn = "978-8888888888"
        book_id, _ = models.add_book(isbn, "Single Copy Book", "Author", "Science", 1)
        user = models.get_user_by_username("jane_smith")

        # Issue book to user
        issued, msg = models.issue_book(book_id, user["id"], days=7)
        self.assertTrue(issued, msg)

        # Check that available copies is now 0
        book = models.get_book_by_id(book_id)
        self.assertEqual(book["available_copies"], 0)

        # Verify issuing again fails because 0 copies are available
        issued_again, msg2 = models.issue_book(book_id, user["id"], days=7)
        self.assertFalse(issued_again)

        # Retrieve the borrow record
        borrows = models.get_user_borrows(user["id"], active_only=True)
        active_rec = next((b for b in borrows if b["book_id"] == book_id), None)
        self.assertIsNotNone(active_rec)

        # Return the book
        returned, ret_msg = models.return_book(active_rec["id"])
        self.assertTrue(returned, ret_msg)

        # Check that available copies restored to 1
        book = models.get_book_by_id(book_id)
        self.assertEqual(book["available_copies"], 1)

        # Clean up book
        models.delete_book(book_id)

    def test_04_access_control_and_routes(self):
        """Test HTTP route protections and role-based redirects."""
        # Unauthenticated access to admin dashboard redirects to login
        res = self.client.get("/admin/dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # Unauthenticated access to user dashboard redirects to login
        res = self.client.get("/user/dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # Login as User
        with self.client:
            login_res = self.client.post("/login", data={
                "username": "john_doe",
                "password": "user123"
            }, follow_redirects=True)
            self.assertEqual(login_res.status_code, 200)
            self.assertIn(b"Member Dashboard", login_res.data)

            # User attempting to access Admin page should be blocked & redirected
            admin_attempt = self.client.get("/admin/dashboard", follow_redirects=True)
            self.assertIn(b"Access denied", admin_attempt.data)

            # User catalog page
            catalog_res = self.client.get("/user/books")
            self.assertEqual(catalog_res.status_code, 200)

            # User my-books page
            my_books_res = self.client.get("/user/my-books")
            self.assertEqual(my_books_res.status_code, 200)

            # Logout
            logout_res = self.client.get("/logout", follow_redirects=True)
            self.assertIn(b"Sign In", logout_res.data)

        # Login as Admin
        with self.client:
            admin_login = self.client.post("/login", data={
                "username": "admin",
                "password": "admin123"
            }, follow_redirects=True)
            self.assertEqual(admin_login.status_code, 200)
            self.assertIn(b"Admin Control Dashboard", admin_login.data)

            # Admin books page
            books_res = self.client.get("/admin/books")
            self.assertEqual(books_res.status_code, 200)

            # Admin issues page
            issues_res = self.client.get("/admin/issues")
            self.assertEqual(issues_res.status_code, 200)

            # Admin users page
            users_res = self.client.get("/admin/users")
            self.assertEqual(users_res.status_code, 200)

    def test_05_member_registration(self):
        """Test registration flow for a new library member."""
        test_username = f"newuser_{int(datetime.now().timestamp())}"
        res = self.client.post("/register", data={
            "full_name": "Test User Registration",
            "username": test_username,
            "email": f"{test_username}@example.com",
            "password": "mypassword123",
            "confirm_password": "mypassword123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Account created successfully", res.data)

        # Login with newly registered user
        with self.client:
            login_res = self.client.post("/login", data={
                "username": test_username,
                "password": "mypassword123"
            }, follow_redirects=True)
            self.assertEqual(login_res.status_code, 200)
            self.assertIn(b"Test User Registration", login_res.data)

if __name__ == "__main__":
    unittest.main()
