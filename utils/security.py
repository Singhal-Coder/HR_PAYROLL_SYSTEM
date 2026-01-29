import bcrypt

def hash_password(plain_password_text):
    """
    Plain text password ko hash mein convert karta hai.
    Returns: Bytes (DB mein save karne ke liye)
    """
    # Password ko bytes mein convert karna padta hai
    bytes_password = plain_password_text.encode('utf-8')
    
    # Salt generate karke hash banata hai
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes_password, salt)
    
    return hashed_password

def verify_password(plain_password_text, stored_hash):
    """
    Login ke waqt check karta hai ki password sahi hai ya nahi.
    """
    # Stored hash agar string hai DB se, toh use bytes mein convert karein
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
        
    bytes_password = plain_password_text.encode('utf-8')
    
    return bcrypt.checkpw(bytes_password, stored_hash)