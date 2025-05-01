import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import mysql.connector
import bcrypt
import subprocess

# === MAIN WINDOW ===
root = tk.Tk()
root.title("Sales Forecasting App - Sign Up")
root.geometry("400x600")
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
title_label = tk.Label(root, text="Create Account", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
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
def create_rounded_entry(placeholder):
    frame = tk.Frame(root, bg=BG_COLOR)
    frame.pack(pady=5)

    canvas = tk.Canvas(frame, width=280, height=40, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    # Draw rounded rectangle manually
    canvas.create_arc((0, 0, BORDER_RADIUS * 2, BORDER_RADIUS * 2), start=90, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((280 - BORDER_RADIUS * 2, 0, 280, BORDER_RADIUS * 2), start=0, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((0, 40 - BORDER_RADIUS * 2, BORDER_RADIUS * 2, 40), start=180, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_arc((280 - BORDER_RADIUS * 2, 40 - BORDER_RADIUS * 2, 280, 40), start=270, extent=90, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_rectangle(BORDER_RADIUS, 0, 280 - BORDER_RADIUS, 40, fill=ENTRY_BG, outline=ENTRY_BG)
    canvas.create_rectangle(0, BORDER_RADIUS, 280, 40 - BORDER_RADIUS, fill=ENTRY_BG, outline=ENTRY_BG)

    # Entry field placed directly inside the frame
    entry = tk.Entry(frame, font=FONT, bg=ENTRY_BG, fg=PLACEHOLDER_COLOR, borderwidth=0, relief="flat", insertbackground=TEXT_COLOR)
    entry.place(x=10, y=5, width=260, height=30)

    # Handle placeholder
    entry.insert(0, placeholder)
    entry.bind("<FocusIn>", lambda event: clear_placeholder(event, entry, placeholder))
    entry.bind("<FocusOut>", lambda event: set_placeholder(entry, placeholder))
    
    return entry

# === CREATE ENTRY FIELDS ===
entry_username = create_rounded_entry("Username")
entry_password = create_rounded_entry("Password")
entry_email = create_rounded_entry("Email")

# === SIGNUP FUNCTION ===
def signup():
    username = entry_username.get().strip()
    password = entry_password.get().strip()
    email = entry_email.get().strip()

    # Validate inputs with specific error messages
    if not username or username == "Username":
        messagebox.showerror("Error", "Username is required!")
        return
    
    if not password or password == "Password":
        messagebox.showerror("Error", "Password is required!")
        return
    
    if not email or email == "Email":
        messagebox.showerror("Error", "Email is required!")
        return
    
    # Email format validation (optional)
    if "@" not in email or "." not in email:
        messagebox.showerror("Error", "Invalid email format!")
        return
    
    # Connect to MySQL Database
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='sahil123',  # Replace with your MySQL password
            database='sales_project'
        )
        cursor = conn.cursor()

        # Check if username or email already exists
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            messagebox.showerror("Error", "Username or email already exists!")
            conn.close()
            return
        
        # Hash the password before storing it
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert into database
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", 
            (username, hashed_password.decode('utf-8'), email)
        )
        conn.commit()
        cursor.close()
        conn.close()

        messagebox.showinfo("Success", "Account created successfully!")
        root.destroy()
        subprocess.run(["python", "login.py"])  # Redirect to login page

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"{err}")

# === SIGN UP BUTTON ===
def on_enter(event):
    btn_signup.config(bg=BTN_HOVER_BG)

def on_leave(event):
    btn_signup.config(bg=BTN_BG)

btn_signup = tk.Button(root, text="Sign Up", font=("Helvetica", 14, "bold"), bg=BTN_BG, fg=TEXT_COLOR, relief="flat", activebackground=BTN_HOVER_BG, activeforeground=TEXT_COLOR, cursor="hand2", borderwidth=0, command=signup)
btn_signup.pack(pady=20, ipadx=20, ipady=1)

# Add hover effects
btn_signup.bind("<Enter>", on_enter)
btn_signup.bind("<Leave>", on_leave)

# === FOOTER ===
footer_text = tk.Label(root, text="Already have an account?", font=("Helvetica", 12), bg=BG_COLOR, fg=PLACEHOLDER_COLOR)
footer_text.pack()

# === GO TO LOGIN FUNCTION ===
def go_to_login():
    root.destroy()
    subprocess.run(["python", "login.py"])

login_link = tk.Label(root, text="Log In", font=("Helvetica", 12, "bold"), bg=BG_COLOR, fg=BTN_BG, cursor="hand2")
login_link.pack()
login_link.bind("<Button-1>", lambda e: go_to_login())

# === FADE-IN EFFECT ===
def fade_in(opacity=0):
    if opacity <= 1:
        root.attributes("-alpha", opacity)
        root.after(30, fade_in, opacity + 0.05)

fade_in()

# === MAIN LOOP ===
root.mainloop()
