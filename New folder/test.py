import requests

def Authkey():
    # คุณต้องนำคีย์ลิขสิทธิ์จากหน้าเว็บ (เช่น จาก Admin Dashboard) มาใส่ที่นี่
    key = "GJEKV-NZWAT-PQPHL-QNRNI"
    
    # คุณต้องเปลี่ยน "YOUR_MACHINE_ID_HERE" เป็นรหัสเครื่องจริง ๆ ที่คุณต้องการใช้
    # รหัสนี้ควรจะคงที่สำหรับแต่ละเครื่องที่ใช้งาน
    machine_id = "N/A"

    try:
        # ใช้ endpoint /validate ที่คาดหวัง key และ machine_id
        response = requests.post("http://127.0.0.1:5000/validate", json={"key": key, "machine_id": machine_id})
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        result = response.json()
        
        if result.get("status") == "valid":
            print("The license is valid!")
        else:
            print("The license does not work: {0}".format(result.get("message", "Unknown error")))
            
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

Authkey()
