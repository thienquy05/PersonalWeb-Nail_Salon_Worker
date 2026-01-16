from flask import Blueprint, request, render_template, session, redirect, url_for, flash
from app.models import *
from app.crypto import encrypt, decrypt
from app.email.email_utils import send_email, generate_coupon
from app.email.templates import *
from app import db, limiter, bcrypt
from datetime import datetime, timedelta
import hashlib, secrets, os
from functools import wraps

main = Blueprint("main", __name__)
admin = Blueprint("admin", __name__)

# --- Unified Login Route ---
@main.route("/", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def index():
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "").strip()

        # 1. Attempt Admin Login (Requires Password)
        if password:
            admin_user = Admin.query.filter_by(username=identity).first()
            if admin_user and bcrypt.check_password_hash(admin_user.password_hash, password):
                session["admin_id"] = admin_user.id
                return redirect("/admin/dashboard")
            else:
                flash("Incorrect username or password.", "error")
                return redirect("/")

        # 2. Attempt User Login (Email Only -> Magic Link)
        elif "@" in identity:
            # Create user if not exists
            user = User.query.filter_by(email_enc=encrypt(identity)).first()
            if not user:
                user = User(email_enc=encrypt(identity))
                db.session.add(user)
                db.session.commit()

            # Generate Magic Link
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            login_token = LoginToken(
                token_hash=token_hash, 
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(minutes=15)
            )
            db.session.add(login_token)
            db.session.commit()

            # Generate Link (In production, email this)
            link = url_for('main.auth', token=token, _external=True)
            print(f"DEBUG MAGIC LINK: {link}") # Check console for link
            
            # Simulate email sending
            # send_email("Login Link", f"Click here: {link}", identity)
            
            return render_template("login_sent.html", email=identity)
        
        else:
            flash("Please enter a valid email address.", "error")

    return render_template("login.html")

# --- User Features ---

@main.route("/auth/<token>")
def auth(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    login_token = LoginToken.query.filter_by(token_hash=token_hash).first()

    if not login_token or login_token.expires_at < datetime.utcnow():
        flash("This link has expired. Please try again.", "error")
        return redirect("/")
    
    # Retrieve user email
    user = User.query.get(login_token.user_id)
    real_email = decrypt(user.email_enc)
    
    return render_template("appointment.html", email=real_email)

@main.route("/appointment", methods=["POST"])
@limiter.limit("3 per hour")
def appointment():
    user_email = request.form["email"]
    msg_raw = request.form["message"]
    date_str = request.form["scheduled_at"]
    
    try:
        scheduled_at = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        scheduled_at = datetime.utcnow() + timedelta(days=1)

    appt = Appointment(
        email_enc=encrypt(user_email),
        message_enc=encrypt(msg_raw),
        scheduled_at=scheduled_at,
        status="scheduled"
    )

    db.session.add(appt)
    db.session.commit()

    # Generate Management Links
    base_url = request.host_url.rstrip('/')
    cancel_link = f"{base_url}/appt/{appt.id}/cancel"
    
    # Send Email (Commented out if no mail server configured)
    # send_email("Appointment Confirmed", appointment_email(scheduled_at, cancel_link, ""), user_email)

    return render_template("success.html", email=user_email)

@main.route("/appt/<int:id>/cancel", methods=["GET", "POST"])
def cancel_appt_user(id):
    appt = Appointment.query.get_or_404(id)
    if request.method == "POST":
        appt.status = "cancelled"
        db.session.commit()
        return render_template("base.html", content="<h2>Appointment Cancelled.</h2><a href='/' class='btn'>Home</a>")
    
    return render_template("cancel_confirm.html", appt=appt)

@main.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        rating = int(request.form["rating"])
        comment = request.form["comment"]
        fb = Feedback(rating=rating, comment_enc=encrypt(comment))
        db.session.add(fb)
        db.session.commit()
        return render_template("base.html", content="<h2>Thank you for your feedback!</h2><a href='/' class='btn'>Home</a>")
    return render_template("feedback.html")

# --- Admin Section ---

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated

@admin.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@admin.route("/dashboard")
@admin_required
def dashboard():
    # --- 1. Appointments (Fetch & Decrypt Email) ---
    appointments = Appointment.query.order_by(Appointment.scheduled_at.desc()).all()
    for a in appointments:
        try:
            # We decrypt the email so the admin can see who booked
            a.client_email = decrypt(a.email_enc)
        except:
            a.client_email = "Unknown (Decryption Error)"

    # --- 2. Coupons ---
    coupons = Coupon.query.all()
    
    # --- 3. Feedback (The Missing Part) ---
    raw_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    feedbacks = []
    for f in raw_feedback:
        try:
            # Decrypt the comment
            txt = decrypt(f.comment_enc)
        except:
            txt = "[Error Decrypting]"
        
        # Create a dictionary for the template
        feedbacks.append({
            'rating': f.rating, 
            'comment': txt, 
            'date': f.created_at
        })

    return render_template("admin/dashboard.html", 
                         appointments=appointments, 
                         coupons=coupons, 
                         feedbacks=feedbacks)

@admin.route("/appt/<int:id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_appt(id):
    appt = Appointment.query.get_or_404(id)
    appt.status = "cancelled"
    db.session.commit()
    return redirect("/admin/dashboard")

@admin.route("/coupon/<int:id>/void", methods=["POST"])
@admin_required
def void_coupon(id):
    coupon = Coupon.query.get_or_404(id)
    coupon.is_used = True
    db.session.commit()
    return redirect("/admin/dashboard")