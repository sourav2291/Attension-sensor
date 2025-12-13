import tkinter as tk
from tkinter import messagebox
import json
import os
import random
import subprocess
import sys

USERS_FILE = "users.json"

# ---------------- USER DATA HELPERS ----------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# ---------------- REGISTER WINDOW ----------------
def register_window(parent):
    parent.destroy()

    def register_user():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        email = email_entry.get().strip()

        if not username or not password or not email:
            messagebox.showerror("Error", "All fields are required")
            return

        users = load_users()

        if username in users:
            messagebox.showerror("Error", "Username already exists")
            return

        for u in users.values():
            if u["email"] == email:
                messagebox.showerror("Error", "Email already registered")
                return

        users[username] = {
            "password": password,
            "email": email
        }

        save_users(users)
        messagebox.showinfo("Success", "Account created successfully")
        reg.destroy()
        login()

    reg = tk.Tk()
    reg.title("Register")
    reg.geometry("300x260")
    reg.resizable(False, False)

    tk.Label(reg, text="Register", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(reg, text="Username").pack()
    user_entry = tk.Entry(reg)
    user_entry.pack()

    tk.Label(reg, text="Password").pack()
    pass_entry = tk.Entry(reg, show="*")
    pass_entry.pack()

    tk.Label(reg, text="Email").pack()
    email_entry = tk.Entry(reg)
    email_entry.pack()

    tk.Button(reg, text="Create Account",
              bg="blue", fg="white",
              command=register_user).pack(pady=15)

    reg.mainloop()

# ---------------- FORGOT PASSWORD ----------------
def forgot_password(parent):
    parent.destroy()
    otp_data = {}

    fp = tk.Tk()
    fp.title("Forgot Password")
    fp.geometry("300x360")
    fp.resizable(False, False)

    tk.Label(fp, text="Forgot Password", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(fp, text="Registered Email").pack()
    email_entry = tk.Entry(fp)
    email_entry.pack()

    otp_label = tk.Label(fp, text="", fg="blue", font=("Arial", 10, "bold"))
    otp_label.pack(pady=5)

    tk.Label(fp, text="Enter OTP").pack()
    otp_entry = tk.Entry(fp, state="disabled")
    otp_entry.pack()

    tk.Label(fp, text="New Password").pack()
    new_pass_entry = tk.Entry(fp, show="*")
    new_pass_entry.pack()

    def send_otp():
        email = email_entry.get().strip()
        users = load_users()

        for username, data in users.items():
            if data["email"] == email:
                otp = str(random.randint(100000, 999999))
                otp_data["otp"] = otp
                otp_data["user"] = username

                otp_label.config(text=f"Your OTP: {otp}")
                otp_entry.config(state="normal")
                otp_entry.delete(0, tk.END)
                return

        messagebox.showerror("Error", "Email not found")

    def reset_password():
        if otp_entry.get().strip() != otp_data.get("otp"):
            messagebox.showerror("Error", "Invalid OTP")
            return

        new_pass = new_pass_entry.get().strip()
        if not new_pass:
            messagebox.showerror("Error", "Password cannot be empty")
            return

        users = load_users()
        users[otp_data["user"]]["password"] = new_pass
        save_users(users)

        messagebox.showinfo("Success", "Password reset successful")
        fp.destroy()
        login()

    tk.Button(fp, text="Send OTP", command=send_otp).pack(pady=5)
    tk.Button(fp, text="Reset Password",
              bg="green", fg="white",
              command=reset_password).pack(pady=15)

    fp.mainloop()

# ---------------- LOGIN WINDOW ----------------
def login():
    def check_login():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()

        users = load_users()

        if username in users and users[username]["password"] == password:
            root.destroy()
            subprocess.Popen([sys.executable, "attension_sensor.py", username])
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password")

    global root
    root = tk.Tk()
    root.title("Login - Attention Monitor")
    root.geometry("300x260")
    root.resizable(False, False)

    tk.Label(root, text="Attention Monitor Login",
             font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(root, text="Username").pack()
    user_entry = tk.Entry(root)
    user_entry.pack()

    tk.Label(root, text="Password").pack()
    pass_entry = tk.Entry(root, show="*")
    pass_entry.pack()

    tk.Button(root, text="Login",
              bg="green", fg="white",
              command=check_login, width=15).pack(pady=10)

    tk.Button(root, text="Register",
              command=lambda: register_window(root)).pack()

    tk.Button(root, text="Forgot Password",
              command=lambda: forgot_password(root)).pack(pady=5)

    root.mainloop()

# ---------------- START APP ----------------
if __name__ == "__main__":
    login()
