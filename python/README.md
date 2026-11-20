# Back-end - Python

This is the documentation of the user registration module backend.
It uses **Python**, **FastAPI** and **MySQL** (MariaDB with XAMPP).

## 1. What you need

- XAMPP (with MySQL running)
- Python 3.10 or newer

## 2. Start the database

1. Open the **XAMPP Control Panel**.
2. Click **Start** next to **MySQL**. It must turn green.
3. Click **Start** next to **Apache**. It must turn green.

## 3. Create the database and the table

Open phpMyAdmin ([http://localhost/phpmyadmin](http://localhost/phpmyadmin)),copy and run the content below in the **SQL** tab:

```sql
CREATE DATABASE IF NOT EXISTS app_security
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE app_security;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    activation_token_hash CHAR(64) NULL UNIQUE,
    token_expires_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL
);
```

## 4. Install the Python project

Open a terminal in the `python/` folder.

**Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

If PowerShell blocks the activation, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 5. Start the server

```powershell
uvicorn main:app --reload
```

The server runs on [http://127.0.0.1:8000](http://127.0.0.1:8000).

## 7. Test the API

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser. You can test everything from this page.

The activation link is not sent by email. It is printed in the console after each registration.