from app import db
from datetime import datetime

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer)
    action = db.Column(db.String(100))
    target_type = db.Column(db.String(100))
    target_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_enc = db.Column(db.Text, nullable=False)

class LoginToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    expires_at = db.Column(db.DateTime)

# app/models.py

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_enc = db.Column(db.Text, nullable=False) 
    scheduled_at = db.Column(db.DateTime, nullable=False) 
    message_enc = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="scheduled")

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    comment_enc = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)    

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50))
    expires_at = db.Column(db.DateTime)
    is_used = db.Column(db.Boolean, default=False)

    