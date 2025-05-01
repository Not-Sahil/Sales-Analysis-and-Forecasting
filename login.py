import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
from mysql.connector import Error
import bcrypt
import subprocess

# === MAIN WINDOW ===
root = tk.Tk()
root.title("Sales Forecasting App - Login")
root.geometry("400x500")
root.configure(bg="#000000")

# === STYLING ===
FONT = ("Helvetica", 14)
BG_COLOR = "#000000"
ENTRY_BG = "#1e1e1e"
TEXT_COLOR = "#ffffff"
PLACEHOLDER_COLOR = "#828282"
BTN_BG = "#0095F6"
BTN_HOVER_BG = "#0077cc"
BORDER_RADIUS = 15

# === LOGO ===
image = Image.open("sales_forecasting_logo.png")
image = image.resize((100, 100), Image.Resampling.LANCZOS)
logo = ImageTk.PhotoImage(image)

logo_label = tk.Label(root, image=logo, bg=BG_COLOR)
logo_label.pack(pady=(30, 10))

# === TITLE ===
title_label = tk.Label(root, text="Sales Forecasting App", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
title_label.pack(pady=(0, 20))

# === PLACEHOLDER HANDLING ===
def clear_placeholder(event, entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(fg=TEXT_COLOR)

def set_placeholder(entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg=PLACEHOLDER_COLOR)

# === ROUNDED ENTRY FIELD ===
def create_rounded_entry(placeholder, show=""):
    frame = tk.Frame(root, bg=BG_COLOR)
    frame.pack(pady=5)

    canvas = tk.Canvas(frame, width=280, height=40, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # Draw rounded rectangle
    canvas.create_arc((0, 0, BORDER_RADIUS * 2, BORDER_RADIUS * 2), start=90, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((280 - BORDER_RADIUS * 2, 0, 280, BORDER_RADIUS * 2), start=0, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((0, 40 - BORDER_RADIUS * 2, BORDER_RADIUS * 2, 40), start=180, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((280 - BORDER_RADIUS * 2, 40 - BORDER_RADIUS * 2, 280, 40), start=270, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_rectangle(BORDER_RADIUS, 0, 280 - BORDER_RADIUS, 40, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_rectangle(0, BORDER_RADIUS, 280, 40 - BORDER_RADIUS, fill=ENTRY_BG, outline=ENTRY_BG)

    # Entry field
    entry = tk.Entry(frame, font=FONT, bg=ENTRY_BG, fg=PLACEHOLDER_COLOR, borderwidth=0, relief="flat", insertbackground=TEXT_COLOR, show=show)
    entry.place(x=10, y=5, width=260, height=30)

    # Placeholder handling
    entry.insert(0, placeholder)
    entry.bind("<FocusIn>", lambda event: clear_placeholder(event, entry, placeholder))
    entry.bind("<FocusOut>", lambda event: set_placeholder(entry, placeholder))
    
    return entry

# === CREATE ENTRY FIELDS ===
entry_username = create_rounded_entry("Username")
entry_password = create_rounded_entry("Password", show="*")

# === LOGIN FUNCTION ===
def login():
    username = entry_username.get()
    password = entry_password.get()

    if not username or username == "Username":
        messagebox.showerror("Error", "Please enter a valid username!")
        return
    if not password or password == "Password":
        messagebox.showerror("Error", "Please enter a valid password!")
        return

    try:
        conn = mysql.connector.connect(host='localhost', user='root', password='sahil123', database='sales_project')
        cursor = conn.cursor()

        # Check if the username exists
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result:
            stored_password = result[0].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                messagebox.showinfo("Success", "Login successful!")
                root.destroy()
                subprocess.run(["python", "trend.py"])  # Open dashboard on successful login
            else:
                messagebox.showerror("Error", "Incorrect password!")
        else:
            messagebox.showerror("Error", "Username not found!")

    except Error as e:
        messagebox.showerror("Error", f"Database error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# === LOGIN BUTTON ===
def on_enter(event):
    btn_login.config(bg=BTN_HOVER_BG)

def on_leave(event):
    btn_login.config(bg=BTN_BG)

btn_login = tk.Button(root, text="Login", font=("Helvetica", 14, "bold"), bg=BTN_BG, fg=TEXT_COLOR, relief="flat", activebackground=BTN_HOVER_BG, activeforeground=TEXT_COLOR, cursor="hand2", borderwidth=0, command=login)
btn_login.pack(pady=20, ipadx=30, ipady=5)

# Add hover effect
btn_login.bind("<Enter>", on_enter)
btn_login.bind("<Leave>", on_leave)

# === FOOTER ===
footer_text = tk.Label(root, text="Don't have an account?", font=("Helvetica", 12), bg=BG_COLOR, fg=PLACEHOLDER_COLOR)
footer_text.pack()

def go_to_signup():
    root.destroy()
    subprocess.run(["python", "signup.py"])

signup_link = tk.Label(root, text="Sign Up", font=("Helvetica", 12, "bold"), bg=BG_COLOR, fg=BTN_BG, cursor="hand2")
signup_link.pack()
signup_link.bind("<Button-1>", lambda e: go_to_signup())

# === FADE-IN EFFECT ===
def fade_in(opacity=0):
    if opacity <= 1:
        root.attributes("-alpha", opacity)
        root.after(30, fade_in, opacity + 0.05)

fade_in()

# === MAIN LOOP ===
root.mainloop()
