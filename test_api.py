import requests
import unittest
import uuid

# กำหนด URL ของ API
API_BASE_URL = "http://127.0.0.1:5000"

def get_unique_id():
    """
    สร้าง ID ที่ไม่ซ้ำกันสำหรับใช้ในการทดสอบ
    """
    return str(uuid.uuid4())

class TestLicenseSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n=== เริ่มการทดสอบระบบ License ===")
        print("ตรวจสอบการเชื่อมต่อกับ API...")
        try:
            response = requests.get(API_BASE_URL)
            if response.status_code == 200:
                print("เชื่อมต่อกับ API สำเร็จ")
            else:
                print("ไม่สามารถเชื่อมต่อกับ API ได้")
                exit(1)
        except requests.exceptions.ConnectionError:
            print("ไม่สามารถเชื่อมต่อกับ API ได้ กรุณาตรวจสอบว่า API กำลังทำงานอยู่")
            exit(1)

    def setUp(self):
        """
        เตรียมข้อมูลสำหรับการทดสอบแต่ละครั้ง
        """
        self.test_machine_id = get_unique_id()
        print(f"\n--- เริ่มการทดสอบ: {self._testMethodName} ---")
        print(f"Machine ID สำหรับการทดสอบ: {self.test_machine_id}")

    def test_1_admin_create_license(self):
        """ทดสอบการสร้าง License Key โดยแอดมิน"""
        print("\nทดสอบการสร้าง License Key")
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("license_keys", data)
        self.assertEqual(len(data["license_keys"]), 1)
        self.test_license_key = data["license_keys"][0]
        print(f"สร้าง License Key สำเร็จ: {self.test_license_key}")

    def test_2_register_license(self):
        """ทดสอบการลงทะเบียน License Key"""
        # สร้าง License Key ก่อน
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        license_key = response.json()["license_keys"][0]
        
        print("\nทดสอบการลงทะเบียน License Key")
        response = requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "machine_id": self.test_machine_id
        })
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"ลงทะเบียน License Key สำเร็จ: {license_key}")

    def test_3_validate_license(self):
        """ทดสอบการตรวจสอบ License Key"""
        # สร้างและลงทะเบียน License Key ก่อน
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        license_key = response.json()["license_keys"][0]
        requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "machine_id": self.test_machine_id
        })
        
        print("\nทดสอบการตรวจสอบ License Key")
        response = requests.post(f"{API_BASE_URL}/validate", json={
            "key": license_key,
            "machine_id": self.test_machine_id
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "valid")
        print(f"ตรวจสอบ License Key สำเร็จ: {license_key}")

    def test_4_register_invalid_key(self):
        """ทดสอบการลงทะเบียน License Key ที่ไม่มีอยู่"""
        print("\nทดสอบการลงทะเบียน License Key ที่ไม่มีอยู่")
        invalid_key = "INVALID-KEY-12345"
        response = requests.post(f"{API_BASE_URL}/register", json={
            "key": invalid_key,
            "machine_id": self.test_machine_id
        })
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], "not_found")
        print("ทดสอบสำเร็จ: ระบบแจ้งเตือนว่าไม่พบ License Key")

    def test_5_register_used_key(self):
        """ทดสอบการลงทะเบียน License Key ที่ถูกใช้งานแล้ว"""
        # สร้างและลงทะเบียน License Key กับเครื่องอื่น
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        license_key = response.json()["license_keys"][0]
        other_machine_id = get_unique_id()
        requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "machine_id": other_machine_id
        })
        
        print("\nทดสอบการลงทะเบียน License Key ที่ถูกใช้งานแล้ว")
        response = requests.post(f"{API_BASE_URL}/register", json={
            "key": license_key,
            "machine_id": self.test_machine_id
        })
        self.assertEqual(response.status_code, 409)
        data = response.json()
        self.assertEqual(data["status"], "conflict")
        print("ทดสอบสำเร็จ: ระบบแจ้งเตือนว่า License Key ถูกใช้งานแล้ว")

    def test_6_admin_toggle_license(self):
        """ทดสอบการเปิด/ปิดการใช้งาน License Key โดยแอดมิน"""
        # สร้าง License Key ก่อน
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        license_key = response.json()["license_keys"][0]
        
        print("\nทดสอบการปิดการใช้งาน License Key")
        response = requests.post(f"{API_BASE_URL}/admin/toggle_key_status", json={
            "key": license_key,
            "action": "deactivate"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "inactive")
        print(f"ปิดการใช้งาน License Key สำเร็จ: {license_key}")
        
        print("\nทดสอบการเปิดการใช้งาน License Key")
        response = requests.post(f"{API_BASE_URL}/admin/toggle_key_status", json={
            "key": license_key,
            "action": "activate"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")
        print(f"เปิดการใช้งาน License Key สำเร็จ: {license_key}")

    def test_7_validate_inactive_license(self):
        """ทดสอบการตรวจสอบ License Key ที่ถูกปิดการใช้งาน"""
        # สร้าง License Key และปิดการใช้งาน
        response = requests.post(f"{API_BASE_URL}/admin/add_key", json={"num_keys": 1})
        license_key = response.json()["license_keys"][0]
        requests.post(f"{API_BASE_URL}/admin/toggle_key_status", json={
            "key": license_key,
            "action": "deactivate"
        })
        
        print("\nทดสอบการตรวจสอบ License Key ที่ถูกปิดการใช้งาน")
        response = requests.post(f"{API_BASE_URL}/validate", json={
            "key": license_key,
            "machine_id": self.test_machine_id
        })
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertEqual(data["status"], "inactive")
        print("ทดสอบสำเร็จ: ระบบแจ้งเตือนว่า License Key ถูกปิดการใช้งาน")

if __name__ == '__main__':
    unittest.main(verbosity=2) 