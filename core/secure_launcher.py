import os
import hashlib

PASSWORD_HASH_FILE = "state/.pwd_hash"
# Default password = 1234 change after first login
DEFAULT_HASH = hashlib.sha256(b"1234").hexdigest()

def _get_saved_hash():
    if not os.path.exists(PASSWORD_HASH_FILE):
        os.makedirs(os.path.dirname(PASSWORD_HASH_FILE), exist_ok=True)
        with open(PASSWORD_HASH_FILE,"w") as f:
            f.write(DEFAULT_HASH)
        return DEFAULT_HASH
    with open(PASSWORD_HASH_FILE,"r") as f:
        return f.read().strip()

def check_password_lock():
    # This is called by main.py UI
    # Return True if you want to implement real prompt later
    # For now returns True = UNLOCKED after your Kivy popup logic
    # If you have your own password popup, put it here
    try:
        # TODO: your existing password check logic here
        # For now we keep it unlocked to test pipeline
        return True
    except Exception:
        return False
