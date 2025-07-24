# Import required libraries
import customtkinter as ctk
import mysql.connector
from tkinter import messagebox
import tkinter.ttk as ttk
from datetime import datetime

# MySQL database connection details
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "task_manager"
}

# Global variables
current_user_id = None
current_task_id = None

# Run MySQL query
def run_query(query, params=None, fetch=False):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchall() if fetch else None
        conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()

# Open main app after login
def open_main_app():
    login_frame.destroy()
    app.geometry("1000x620")

    header = ctk.CTkFrame(app, fg_color="#1a1a1a", height=60)
    header.pack(fill="x")
    ctk.CTkLabel(header, text="To-Do Dashboard", font=("Arial Bold", 22)).pack(pady=10)

    container = ctk.CTkFrame(app)
    container.pack(expand=True, fill="both", padx=20, pady=10)

    input_frame = ctk.CTkFrame(container)
    input_frame.pack(fill="x", pady=10)

    ctk.CTkLabel(input_frame, text="Add / Edit Task", font=("Arial Bold", 16)).pack(anchor="w", padx=10)

    global desc_entry, date_entry, cat_entry, status_var, add_button, update_button, task_table

    form_row = ctk.CTkFrame(input_frame)
    form_row.pack(fill="x", padx=10, pady=5)

    desc_entry = ctk.CTkEntry(form_row, placeholder_text="Task Description")
    desc_entry.pack(side="left", padx=5, expand=True, fill="x")

    date_entry = ctk.CTkEntry(form_row, placeholder_text="Due Date (YYYY-MM-DD)")
    date_entry.pack(side="left", padx=5, expand=True, fill="x")
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    cat_entry = ctk.CTkEntry(form_row, placeholder_text="Category")
    cat_entry.pack(side="left", padx=5, expand=True, fill="x")

    status_var = ctk.StringVar(value="Pending")
    status_menu = ctk.CTkOptionMenu(form_row, values=["Pending", "Done"], variable=status_var, width=140)
    status_menu.pack(side="left", padx=5)

    button_frame = ctk.CTkFrame(input_frame)
    button_frame.pack(fill="x", padx=10, pady=5)

    add_button = ctk.CTkButton(button_frame, text="Add Task", command=add_task)
    add_button.pack(side="left", expand=True, fill="x", padx=5)

    update_button = ctk.CTkButton(button_frame, text="Update Task", command=update_task, state="disabled")
    update_button.pack(side="left", expand=True, fill="x", padx=5)

    ctk.CTkButton(button_frame, text="Edit Task", command=load_task).pack(side="left", expand=True, fill="x", padx=5)
    ctk.CTkButton(button_frame, text="Delete Task", command=delete_task).pack(side="left", expand=True, fill="x", padx=5)

    task_frame = ctk.CTkFrame(container)
    task_frame.pack(expand=True, fill="both", pady=10)

    ctk.CTkLabel(task_frame, text="Task List", font=("Arial Bold", 16)).pack(anchor="w", padx=10)

    task_table = ttk.Treeview(task_frame, columns=(1, 2, 3, 4, 5), show="headings", height=10)
    task_table.pack(expand=True, fill="both", padx=10, pady=5)

    for i, col in enumerate(["ID", "Description", "Due Date", "Category", "Status"], start=1):
        task_table.heading(i, text=col)
        task_table.column(i, width=150, anchor="center")

    refresh_tasks()

# Login function
def login():
    username = username_entry.get()
    password = password_entry.get()
    result = run_query("SELECT id FROM app_users WHERE username = %s AND password = %s", (username, password), fetch=True)
    if result:
        global current_user_id
        current_user_id = result[0][0]
        messagebox.showinfo("Login Successful", f"Welcome {username}!")
        open_main_app()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# ✅ Updated Add Task function
def add_task():
    description = desc_entry.get().strip()
    due_date_str = date_entry.get().strip()
    category = cat_entry.get().strip()
    status = status_var.get()

    if not description or not due_date_str or not category:
        messagebox.showerror("Unsuccessful", "All fields must be filled.")
        return

    # if not (1 <= len(description) <= 5):
    #     messagebox.showerror("Unsuccessful", "Description must be between 1 to 5 characters.")
    #     return

    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        if due_date > datetime.now().date():
            messagebox.showerror("Unsuccessful", "Due date cannot be in the future.")
            return
    except ValueError:
        messagebox.showerror("Unsuccessful", "Unsuccessful")  # Generic message
        return

    run_query(
        "INSERT INTO user_tasks (description, due_date, category, status, user_id) VALUES (%s, %s, %s, %s, %s)",
        (description, due_date_str, category, status, current_user_id)
    )
    messagebox.showinfo("Success", "Task added successfully!")
    clear_fields()
    refresh_tasks()

# Load task into form
def load_task():
    global current_task_id
    selected = task_table.focus()
    if not selected:
        messagebox.showinfo("Select Task", "Please select a task to edit.")
        return

    task = task_table.item(selected)['values']
    if task:
        current_task_id = task[0]
        desc_entry.delete(0, 'end')
        desc_entry.insert(0, task[1])
        date_entry.delete(0, 'end')
        date_entry.insert(0, task[2])
        cat_entry.delete(0, 'end')
        cat_entry.insert(0, task[3])
        status_var.set(task[4])
        update_button.configure(state="normal")
        add_button.configure(state="disabled")

# Update task
def update_task():
    run_query("UPDATE user_tasks SET description=%s, due_date=%s, category=%s, status=%s WHERE id=%s AND user_id=%s",
              (desc_entry.get(), date_entry.get(), cat_entry.get(), status_var.get(), current_task_id, current_user_id))
    messagebox.showinfo("Updated", "Task updated successfully!")
    clear_fields()
    refresh_tasks()

# Delete task
def delete_task():
    selected = task_table.focus()
    if not selected:
        messagebox.showinfo("Select Task", "Please select a task to delete.")
        return
    task_id = task_table.item(selected)['values'][0]
    run_query("DELETE FROM user_tasks WHERE id = %s AND user_id=%s", (task_id, current_user_id))
    messagebox.showinfo("Deleted", "Task deleted successfully!")
    refresh_tasks()

# Refresh task list
def refresh_tasks():
    for row in task_table.get_children():
        task_table.delete(row)
    rows = run_query("SELECT id, description, due_date, category, status FROM user_tasks WHERE user_id=%s", (current_user_id,), fetch=True)
    for row in rows:
        task_table.insert("", "end", values=row)

# ✅ Clear form and re-fill today’s date
def clear_fields():
    desc_entry.delete(0, 'end')
    date_entry.delete(0, 'end')
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    cat_entry.delete(0, 'end')
    status_var.set("Pending")
    update_button.configure(state="disabled")
    add_button.configure(state="normal")

# Setup window and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("To-Do Task Manager")
app.geometry("400x350")

# Login UI
login_frame = ctk.CTkFrame(app)
login_frame.pack(expand=True, fill="both", padx=40, pady=60)

ctk.CTkLabel(login_frame, text="Login", font=("Arial", 20)).pack(pady=10)

username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username")
username_entry.pack(pady=8, fill="x", padx=30)

password_entry = ctk.CTkEntry(login_frame, placeholder_text="Password", show="*")
password_entry.pack(pady=8, fill="x", padx=30)

ctk.CTkButton(login_frame, text="Login", command=login).pack(pady=15)

# Start app
app.mainloop()


