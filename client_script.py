import requests
import uuid
import platform

# กำหนด URL ของ API ของเรา
API_BASE_URL = "http://127.0.0.1:5000"

def get_machine_id():
    """
    สร้างหรือดึง Machine ID ที่ไม่ซ้ำกันสำหรับเครื่องนี้ โดยใช้ HWID หากเป็นไปได้
    สำหรับ Windows จะพยายามใช้ CPU ID หาก WMI พร้อมใช้งาน มิฉะนั้นจะใช้ UUID จากชื่อโฮสต์
    """
    try:
        import wmi # การนำเข้า wmi อาจล้มเหลวหากไม่ได้ติดตั้ง
        c = wmi.WMI()
        # ใช้ ProcessorId ของ CPU เป็น Machine ID
        # คุณอาจเลือกใช้ Motherboard SerialNumber (c.Win32_BaseBoard()[0].SerialNumber)
        # หรือ DiskDrive SerialNumber (c.Win32_DiskDrive()[0].SerialNumber)
        # ขึ้นอยู่กับความต้องการความเฉพาะเจาะจงและเสถียรภาพ
        for processor in c.Win32_Processor():
            return processor.ProcessorId
    except ImportError:
        # Fallback หากไม่พบ WMI หรือไม่ใช่ระบบ Windows
        print("WMI module not found or not on Windows. Using UUID from hostname as fallback.")
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))
    except Exception as e:
        print(f"Error getting machine ID with WMI: {e}. Using UUID from hostname as fallback.")
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))

def get_machine_id_alternative():
    """
    ตัวอย่างการสร้าง Machine ID ที่เฉพาะเจาะจงมากขึ้นสำหรับ Windows
    ต้องติดตั้ง: pip install WMI (อาจต้องมี pywin32 ด้วย)
    """
    try:
        import wmi
        c = wmi.WMI()
        # ใช้ SerialNumber ของ CPU เป็น Machine ID
        for processor in c.Win32_Processor():
            return processor.ProcessorId
    except ImportError:
        print("WMI module not found. Using UUID as fallback.")
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node())) # ใช้ชื่อโฮสต์
    except Exception as e:
        print(f"Error getting machine ID with WMI: {e}. Using UUID as fallback.")
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))

def register_license(license_key):
    machine_id = get_machine_id_alternative() # หรือ get_machine_id()
    print(f"Machine ID: {machine_id}")
    url = f"{API_BASE_URL}/register"
    payload = {"key": license_key, "machine_id": machine_id}
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        print(f"Register API Response: {response_data}")
        return response_data
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the License API. Is it running?")
        return {"status": "error", "message": "API Not Reachable"}
    except Exception as e:
        print(f"An unexpected error occurred during registration: {e}")
        return {"status": "error", "message": str(e)}

def validate_license(license_key):
    machine_id = get_machine_id_alternative() # หรือ get_machine_id()
    print(f"Machine ID: {machine_id}")
    url = f"{API_BASE_URL}/validate"
    payload = {"key": license_key, "machine_id": machine_id}
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        print(f"Validate API Response: {response_data}")
        return response_data
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the License API. Is it running?")
        return {"status": "error", "message": "API Not Reachable"}
    except Exception as e:
        print(f"An unexpected error occurred during validation: {e}")
        return {"status": "error", "message": str(e)}

def login_with_license_key():
    print("\n=== ระบบเข้าสู่ระบบ License ===")
    license_key = input("กรุณากรอก License Key ของคุณ: ")
    machine_id = get_machine_id()

    print(f"กำลังตรวจสอบ License Key: {license_key} สำหรับ Machine ID: {machine_id}...")

    try:
        # ขั้นแรก: ลองลงทะเบียน License Key กับเครื่องนี้ (ถ้ายังไม่เคยลงทะเบียน)
        register_response = requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "machine_id": machine_id
        })
        
        if register_response.status_code == 201:
            print("ลงทะเบียน License Key สำเร็จ! กำลังตรวจสอบสถานะ...")
        elif register_response.status_code == 200 and register_response.json().get("status") == "registered":
            print("License Key นี้เคยลงทะเบียนกับเครื่องนี้แล้ว กำลังตรวจสอบสถานะ...")
        else:
            print(f"ไม่สามารถลงทะเบียน/ตรวจสอบ License Key ได้: {register_response.json().get('message', 'Unknown error')}")
            return

        # ขั้นที่สอง: ตรวจสอบสถานะของ License Key
        validate_response = requests.post(f"{API_BASE_URL}/validate", json={
            "key": license_key,
            "machine_id": machine_id
        })

        if validate_response.status_code == 200:
            data = validate_response.json()
            if data["status"] == "valid":
                print("เข้าสู่ระบบสำเร็จ! License Key ของคุณถูกต้องและใช้งานได้")
            else:
                print(f"สถานะ License Key: {data['status']}. ข้อความ: {data.get('message', 'ไม่มีข้อความ')}")
        elif validate_response.status_code == 403:
            data = validate_response.json()
            print(f"เข้าสู่ระบบไม่สำเร็จ: License Key ของคุณ {data['status']}. ข้อความ: {data.get('message', 'ไม่มีข้อความ')}")
        elif validate_response.status_code == 404:
            data = validate_response.json()
            print(f"เข้าสู่ระบบไม่สำเร็จ: ไม่พบ License Key นี้ในระบบ. ข้อความ: {data.get('message', 'ไม่มีข้อความ')}")
        else:
            print(f"เกิดข้อผิดพลาดในการตรวจสอบ License Key (Status: {validate_response.status_code}): {validate_response.text}")

    except requests.exceptions.ConnectionError:
        print("ข้อผิดพลาด: ไม่สามารถเชื่อมต่อกับ License API ได้ กรุณาตรวจสอบว่า API กำลังทำงานอยู่")
    except Exception as e:
        print(f"เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")

if __name__ == "__main__":
    login_with_license_key()