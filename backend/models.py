"""
models.py
---------
Simple data-access layer sitting on top of database.py.
No ORM is used -- plain SQL via sqlite3 -- so it stays easy to read
and modify.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


# ---------------------------------------------------------------------
# Admin (dashboard users)
# ---------------------------------------------------------------------
class Admin:
    @staticmethod
    def create(username, email, password):
        """Create a new admin account. Password is hashed, never stored raw."""
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO admins (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, generate_password_hash(password)),
            )
            conn.commit()
            return True
        except Exception as e:
            print("Admin.create error:", e)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        row = conn.execute(
            "SELECT * FROM admins WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        return row

    @staticmethod
    def verify_password(username, password):
        """Return the admin row if credentials are valid, else None."""
        admin = Admin.get_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            return admin
        return None

    @staticmethod
    def update_last_login(admin_id):
        conn = get_db_connection()
        conn.execute(
            "UPDATE admins SET last_login = datetime('now') WHERE id = ?",
            (admin_id,),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def count():
        conn = get_db_connection()
        n = conn.execute("SELECT COUNT(*) AS n FROM admins").fetchone()["n"]
        conn.close()
        return n


# ---------------------------------------------------------------------
# Leads (contact-form enquiries from the public site)
# ---------------------------------------------------------------------
class Lead:
    @staticmethod
    def create(full_name, email, organisation="", interest="", message=""):
        conn = get_db_connection()
        conn.execute(
            """INSERT INTO leads (full_name, organisation, email, interest, message)
               VALUES (?, ?, ?, ?, ?)""",
            (full_name, organisation, email, interest, message),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all(status=None):
        conn = get_db_connection()
        if status:
            rows = conn.execute(
                "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM leads ORDER BY created_at DESC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(lead_id):
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_status(lead_id, status):
        conn = get_db_connection()
        conn.execute(
            "UPDATE leads SET status = ? WHERE id = ?", (status, lead_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(lead_id):
        conn = get_db_connection()
        conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def stats():
        conn = get_db_connection()
        total = conn.execute("SELECT COUNT(*) AS n FROM leads").fetchone()["n"]
        new = conn.execute(
            "SELECT COUNT(*) AS n FROM leads WHERE status = 'new'"
        ).fetchone()["n"]
        contacted = conn.execute(
            "SELECT COUNT(*) AS n FROM leads WHERE status = 'contacted'"
        ).fetchone()["n"]
        closed = conn.execute(
            "SELECT COUNT(*) AS n FROM leads WHERE status = 'closed'"
        ).fetchone()["n"]
        conn.close()
        return {"total": total, "new": new, "contacted": contacted, "closed": closed}