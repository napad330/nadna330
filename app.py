from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import uuid
import random
import string
from datetime import datetime # Import datetime
from apscheduler.schedulers.background import BackgroundScheduler # Import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger # Import IntervalTrigger
from waitress import serve # Import serve from waitress

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'database.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

print("Attempting to create database tables...")
with app.app_context():
    db.create_all()
print("Database tables created (if they didn't exist).")

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False) # 'active' or 'inactive'
    expiration_date = db.Column(db.DateTime, nullable=True) # New column for expiration date

    def __repr__(self):
        return f'<License {self.license_key} on {self.ip_address} ({self.status}) - Expires: {self.expiration_date}>'

@app.route('/')
def home():
    return "License API is running!"

@app.route('/register', methods=['POST'])
def register_license():
    data = request.get_json()
    license_key = data.get('key')
    ip_address = data.get('ip_address')

    if not license_key or not ip_address:
        return jsonify({"message": "License key and IP address are required"}), 400

    # ตรวจสอบว่า IP address นี้ถูกใช้กับ License Key อื่นอยู่แล้วหรือไม่
    existing_ip_registration = License.query.filter_by(ip_address=ip_address).first()
    if existing_ip_registration and existing_ip_registration.license_key != license_key:
        return jsonify({"message": f"License key: {existing_ip_registration.license_key}", "status": "ip_conflict"}), 409

    existing_license = License.query.filter_by(license_key=license_key).first()

    if existing_license:
        if existing_license.ip_address == ip_address:
            return jsonify({"message": "License already registered to this IP", "status": "registered"}), 200
        elif existing_license.ip_address == "":
            # Key exists but not yet bound to any IP, allow registration
            existing_license.ip_address = ip_address
            db.session.commit()
            return jsonify({"message": "License registered successfully to this IP", "status": "success"}), 201
        else:
            return jsonify({"message": "License key already registered to another IP", "status": "conflict"}), 409
    else:
        return jsonify({"message": "License key not found", "status": "not_found"}), 404

@app.route('/validate', methods=['POST'])
def validate_license():
    data = request.get_json()
    license_key = data.get('key')
    ip_address = data.get('ip_address')

    if not license_key or not ip_address:
        return jsonify({"message": "License key and IP address are required"}), 400

    license_entry = License.query.filter_by(license_key=license_key).first()

    if license_entry:
        # Check for expiration date
        if license_entry.expiration_date and license_entry.expiration_date < datetime.now():
            return jsonify({"message": "License is expired", "status": "expired"}), 403

        if license_entry.status == 'inactive':
            return jsonify({"message": "License is currently inactive", "status": "inactive"}), 403
        if license_entry.ip_address == ip_address:
            return jsonify({"message": "License is valid", "status": "valid"}), 200
        else:
            return jsonify({"message": "License key is registered to a different IP", "status": "invalid"}), 403
    else:
        return jsonify({"message": "License key not found", "status": "not_found"}), 404

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    return render_template('admin.html')

@app.route('/admin/delete_expired_keys', methods=['POST'])
def delete_expired_keys():
    try:
        # Find all expired licenses
        expired_licenses = License.query.filter(License.expiration_date < datetime.now()).all()
        count = len(expired_licenses)
        if count > 0:
            for license in expired_licenses:
                db.session.delete(license)
            db.session.commit()
            return jsonify({"message": f"{count} expired license key(s) deleted successfully", "status": "success"}), 200
        else:
            return jsonify({"message": "No expired license keys found to delete", "status": "no_expired_keys"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error deleting expired keys: {str(e)}", "status": "error"}), 500

# Function to be scheduled for deleting expired keys
def scheduled_delete_expired_keys():
    with app.app_context():
        try:
            expired_licenses = License.query.filter(License.expiration_date < datetime.now()).all()
            count = len(expired_licenses)
            if count > 0:
                for license in expired_licenses:
                    db.session.delete(license)
                db.session.commit()
                print(f"[Scheduler] Deleted {count} expired license key(s).")
        except Exception as e:
            db.session.rollback()
            print(f"[Scheduler] Error deleting expired keys: {str(e)}")

def generate_segment(length=5):
    letters = string.ascii_uppercase
    return ''.join(random.choices(letters, k=length))

def generate_custom_key():
    segments = [generate_segment() for _ in range(4)]
    return "-".join(segments)

@app.route('/admin/add_key', methods=['POST'])
def add_key():
    data = request.get_json()
    num_keys = data.get('num_keys', 1)
    expiration_date_str = data.get('expiration_date') # Get expiration date string
    generated_keys = []

    # Convert expiration_date_str to datetime object if provided
    expiration_date = None
    if expiration_date_str:
        try:
            expiration_date = datetime.fromisoformat(expiration_date_str) # Assuming ISO format (YYYY-MM-DDTHH:MM:SS)
        except ValueError:
            return jsonify({"message": "Invalid expiration date format. Use YYYY-MM-DDTHH:MM:SS", "status": "error"}), 400

    for _ in range(int(num_keys)):
        new_license_key = generate_custom_key()
        # Pass expiration_date to License constructor
        new_license = License(license_key=new_license_key, ip_address="", status='active', expiration_date=expiration_date)
        db.session.add(new_license)
        generated_keys.append(new_license_key)

    db.session.commit()
    return jsonify({"message": f"{len(generated_keys)} new license key(s) generated and added", "license_keys": generated_keys, "status": "success"}), 201

@app.route('/admin/toggle_key_status', methods=['POST'])
def toggle_key_status():
    data = request.get_json()
    license_key = data.get('key')
    action = data.get('action') # 'activate' or 'deactivate'

    if not license_key or action not in ['activate', 'deactivate']:
        return jsonify({"message": "License key and action (activate/deactivate) are required"}), 400

    license_entry = License.query.filter_by(license_key=license_key).first()

    if license_entry:
        if action == 'activate':
            license_entry.status = 'active'
            db.session.commit()
            return jsonify({"message": f"License {license_key} activated", "status": "active"}), 200
        elif action == 'deactivate':
            license_entry.status = 'inactive'
            db.session.commit()
            return jsonify({"message": f"License {license_key} deactivated", "status": "inactive"}), 200
    else:
        return jsonify({"message": "License key not found", "status": "not_found"}), 404

@app.route('/api/licenses', methods=['GET'])
def get_all_licenses():
    licenses = License.query.all()
    licenses_data = []
    for license in licenses:
        licenses_data.append({
            'id': license.id,
            'license_key': license.license_key,
            'ip_address': license.ip_address,
            'status': license.status,
            'expiration_date': license.expiration_date.isoformat() if license.expiration_date else None # Include expiration date
        })
    return jsonify(licenses_data), 200

@app.route('/admin/delete_key', methods=['POST'])
def delete_key():
    data = request.get_json()
    license_key = data.get('key')

    if not license_key:
        return jsonify({"message": "License key is required"}), 400

    license_entry = License.query.filter_by(license_key=license_key).first()

    if license_entry:
        db.session.delete(license_entry)
        db.session.commit()
        return jsonify({"message": f"License {license_key} deleted successfully", "status": "success"}), 200
    else:
        return jsonify({"message": "License key not found", "status": "not_found"}), 404

@app.route('/admin/reset_ip', methods=['POST'])
def reset_ip():
    data = request.get_json()
    license_key = data.get('key')

    if not license_key:
        return jsonify({"message": "License key is required"}), 400

    license_entry = License.query.filter_by(license_key=license_key).first()

    if license_entry:
        license_entry.ip_address = "" # Set IP address to empty
        db.session.commit()
        return jsonify({"message": f"License {license_key} IP has been reset", "status": "success"}), 200
    else:
        return jsonify({"message": "License key not found", "status": "not_found"}), 404

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    # Schedule the job to run every minute
    scheduler.add_job(func=scheduled_delete_expired_keys, trigger=IntervalTrigger(minutes=1), id='delete_expired_keys_job', name='Delete Expired License Keys')
    scheduler.start()

    # Shut down the scheduler when the app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    # Get port from environment variable, default to 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting Waitress server on 0.0.0.0:{port}...")
    serve(app, host='0.0.0.0', port=port)
    print("Waitress server stopped.") # This line will only be reached if the server stops
