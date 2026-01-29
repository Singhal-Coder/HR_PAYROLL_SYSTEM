-- Enable Foreign Key support
PRAGMA foreign_keys = ON;

-- 1. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    admin_id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Departments
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY,
    dept_name TEXT UNIQUE NOT NULL
);

-- 3. Roles (Salary Rules)
CREATE TABLE IF NOT EXISTS roles (
    role_id INTEGER PRIMARY KEY,
    designation TEXT UNIQUE NOT NULL,
    base_pf_percent REAL DEFAULT 0.12,
    tax_deduction REAL DEFAULT 0,
    daily_bonus REAL DEFAULT 0,
    start_time TEXT DEFAULT '09:00:00',
    end_time TEXT DEFAULT '18:00:00'
);

-- 4. Employees Master Table
CREATE TABLE IF NOT EXISTS employees (
    emp_code TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    joining_date DATE NOT NULL,
    resignation_date DATE,
    base_salary REAL NOT NULL,
    last_dues_cleared_upto DATE,
    dept_id INTEGER,
    role_id INTEGER,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- 5. Face Encodings
CREATE TABLE IF NOT EXISTS face_encodings (
    id INTEGER PRIMARY KEY,
    emp_code TEXT,
    encoding BLOB NOT NULL,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (emp_code) REFERENCES employees(emp_code) ON DELETE CASCADE
);

-- 6. Attendance Logs
CREATE TABLE IF NOT EXISTS attendance_logs (
    log_id INTEGER PRIMARY KEY,
    emp_code TEXT,
    date DATE NOT NULL,
    in_time TEXT NOT NULL,
    status TEXT,
    method TEXT,
    wifi_verified INTEGER DEFAULT 0,
    evidence_img TEXT,
    FOREIGN KEY (emp_code) REFERENCES employees(emp_code),
    UNIQUE(emp_code, date)
);

-- 7. Leaves
CREATE TABLE IF NOT EXISTS employee_leaves (
    leave_id INTEGER PRIMARY KEY,
    emp_code TEXT,
    leave_date DATE NOT NULL,
    leave_type TEXT NOT NULL,
    status TEXT DEFAULT 'Approved',
    FOREIGN KEY (emp_code) REFERENCES employees(emp_code)
);

-- 8. Salary Slips
CREATE TABLE IF NOT EXISTS salary_slips (
    slip_id INTEGER PRIMARY KEY,
    emp_code TEXT,
    month_year TEXT NOT NULL,
    total_present INTEGER,
    net_salary REAL,
    payment_status TEXT DEFAULT 'Pending',
    payment_date DATE,
    pdf_path TEXT,
    FOREIGN KEY (emp_code) REFERENCES employees(emp_code)
);