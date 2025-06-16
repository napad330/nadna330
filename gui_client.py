import tkinter as tk
from tkinter import messagebox
import requests
import socket

# กำหนด URL ของ API ของเรา
API_BASE_URL = "http://127.0.0.1:5000"

def get_ip_address():
    """
    ดึง IP address ของเครื่องที่ใช้งานอยู่
    """
    try:
        # สร้าง socket เพื่อเชื่อมต่อกับ DNS server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "127.0.0.1"  # fallback to localhost if can't get IP

def login_action():
    license_key = entry_license_key.get()
    ip_address = get_ip_address()
    
    if not license_key:
        messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอก License Key")
        return

    status_label.config(text=f"กำลังตรวจสอบ License Key: {license_key} สำหรับ IP: {ip_address}...")
    
    try:
        # ขั้นแรก: ลองลงทะเบียน License Key กับเครื่องนี้ (ถ้ายังไม่เคยลงทะเบียน)
        register_response = requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "ip_address": ip_address
        })
        
        if register_response.status_code == 201:
            status_label.config(text="ลงทะเบียน License Key สำเร็จ! กำลังตรวจสอบสถานะ...")
        elif register_response.status_code == 200 and register_response.json().get("status") == "registered":
            status_label.config(text="License Key นี้เคยลงทะเบียนกับ IP นี้แล้ว กำลังตรวจสอบสถานะ...")
        else:
            message = register_response.json().get("message", "Unknown error")
            messagebox.showerror("ลงทะเบียนไม่สำเร็จ", f"ไม่สามารถลงทะเบียน License Key ได้: {message}")
            status_label.config(text=f"สถานะ: ลงทะเบียนไม่สำเร็จ: {message}", fg="red")
            return

        # ขั้นที่สอง: ตรวจสอบสถานะของ License Key
        validate_response = requests.post(f"{API_BASE_URL}/validate", json={
            "key": license_key,
            "ip_address": ip_address
        })

        if validate_response.status_code == 200:
            data = validate_response.json()
            if data["status"] == "valid":
                messagebox.showinfo("เข้าสู่ระบบสำเร็จ", "License Key ของคุณถูกต้องและใช้งานได้!")
                status_label.config(text="สถานะ: เข้าสู่ระบบสำเร็จ", fg="green")
                # คุณสามารถใส่โค้ดสำหรับเปิดใช้งานแอปพลิเคชันหลักของคุณที่นี่
            else:
                message = data.get("message", "ไม่มีข้อความ")
                messagebox.showwarning("สถานะ License Key", f"สถานะ License Key: {data['status']}. ข้อความ: {message}")
                status_label.config(text=f"สถานะ: {data['status']}: {message}", fg="orange")
        elif validate_response.status_code == 403:
            data = validate_response.json()
            message = data.get("message", "ไม่มีข้อความ")
            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", f"License Key ของคุณ {data['status']}. ข้อความ: {message}")
            status_label.config(text=f"สถานะ: {data['status']}: {message}", fg="red")
        elif validate_response.status_code == 404:
            data = validate_response.json()
            message = data.get("message", "ไม่มีข้อความ")
            messagebox.showerror("เข้าสู่ระบบไม่สำเร็จ", f"ไม่พบ License Key นี้ในระบบ. ข้อความ: {message}")
            status_label.config(text=f"สถานะ: {data['status']}: {message}", fg="red")
        else:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการตรวจสอบ License Key (Status: {validate_response.status_code}): {validate_response.text}")
            status_label.config(text=f"สถานะ: ข้อผิดพลาด {validate_response.status_code}", fg="red")

    except requests.exceptions.ConnectionError:
        messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อกับ License API ได้ กรุณาตรวจสอบว่า API กำลังทำงานอยู่")
        status_label.config(text="สถานะ: API ไม่สามารถเข้าถึงได้", fg="red")
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        status_label.config(text="สถานะ: เกิดข้อผิดพลาด", fg="red")

# ตั้งค่าหน้าต่างหลัก
root = tk.Tk()
root.title("License Key Login")
root.geometry("400x250")
root.resizable(False, False)
root.configure(bg="#222222") # Dark background

# ตั้งค่าสไตล์ (optional, for a nicer look)
style = {
    "bg": "#333333",
    "fg": "#E0E0E0",
    "font": ("Arial", 12),
    "border": 0,
    "highlightthickness": 0,
}

button_style = {
    "bg": "#8BC34A", # Greenish button
    "fg": "white",
    "font": ("Arial", 14, "bold"),
    "activebackground": "#689F38",
    "activeforeground": "white",
    "relief": "flat",
    "borderwidth": 0,
    "padx": 20,
    "pady": 10,
}

# License Key Input Frame
input_frame = tk.Frame(root, bg="#222222")
input_frame.pack(pady=20)

label_license_key = tk.Label(input_frame, text="License Key", **style)
label_license_key.pack(pady=5)

entry_license_key = tk.Entry(input_frame, width=30, **style, insertbackground="white")
entry_license_key.pack()

# Login Button
login_button = tk.Button(root, text="Login", command=login_action, **button_style)
login_button.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="", bg="#222222", fg="#E0E0E0", font=("Arial", 10, "italic"))
status_label.pack(pady=10)

root.mainloop() 