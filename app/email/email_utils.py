from flask_mail import Message
from app import mail
import secrets
from datetime import datetime, timedelta

def send_email(subject, body, recipient):
    msg = Message(subject, body, recipient)
    msg.body = body
    mail.send(msg)

def generate_coupon():
    code = f"SAVE-{secrets.token_hex(4)}"
    expires = datetime.utcnow() + timedelta(days=7)
    return code, expires



