from flask import Blueprint, request, render_template, session, redirect
from app.models import *
from app.crypto import encrypt, decrypt
from app.email.email_utils import send_email, generate_coupon
from app.email.templates import *
from app import db, limiter, bcrypt
from datetime import datetime, timedelta
import hashlib, secrets, os


main = Blueprint("main", __name__)
admin = Blueprint("admin", __name__)

# --- User Process Backend ---
@main.route("/", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        email = request.form["email"]

        user = User.query.filter_by(email_enc=encrypt(email)).first()
        if not user:
            user = User(email_ec=email)
            db.session.add(user)
            db.session.commit()

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        login_token = LoginToken(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )

        db.session.add(login_token)
        db.session.commit()

    return render_template("login.html")

@main.route("/auth/<token>")
def auth(token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    login_token = LoginToken.query.filter_by(token_hash=token_hash).first()

    if not login_token or login_token.expires_at < datetime.utcnow():
        return "Invalid or expired token"
    
    return render_template("appointment.html")

@main.route("/appointment", methods=["POST"])
@limiter.limit("3 per hour")
def appointment():
    user_email = request.form["email"]
    msg = encrypt(request.form["message"])
    appt = Appointment(message_enc=msg,
                       scheduled_at=datetime.utcnow(),
                       status="scheduled"
                       )

    db.session.add(appt)

    code, expires = generate_coupon()
    coupon = Coupon(code=code, expires_at=expires)
    db.session.add(coupon)
    db.session.commit()


    send_email(
        "New Appoinment",
        f"Coupon: {code}",
        os.getenv("ADMIN_EMAIL")
    )

    send_email(
        "Appointment Confirmed!",
        appointment_email(appt.scheduled_at, cancel_link="", reschedule_link=""),
        {user_email}
    )
    return "Appoinment submitted"


from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

def log_action(admin_id, action, target_type, target_id):
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip_address=request.remote_addr
    )

    db.session.add(log)
    db.session.commit()



# --- Admin Process Backend ---
@admin.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin_user = Admin.query.filter_by(username=username).first()
        if admin_user and bcrypt.check_password_hash(admin_user.password_hash, password):
            session["admin_id"] = admin_user.id
            log_action(admin_user.id, "ADMIN_LOGIN", "admin", admin_user.id)
            return redirect("/admin/dashboard")

    return render_template("admin/login.html")

@admin.route("/logout")
@admin_required
def admin_logout():
    admin_id = session["admin_id"]
    session.clear()
    log_action(admin_id, "ADMIN_LOGOUT", "admin", admin_id)
    return redirect("/admin/login")


@admin.route("/dashboard")
@admin_required
def admin_dashboard():
    appointments = Appointment.query.order_by(Appointment.scheduled_at).all()
    coupons = Coupon.query.order_by(Coupon.expires_at).all()
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(20)

    return render_template(
        "admin/dashboard.html",
        appointments=appointments,
        coupons=coupons,
        logs=logs
    )

@admin.route("/appointments")
@admin_required
def admin_appointments():
    appts = Appointment.query.all()
    return render_template("admin/appointments.html", appointments=appts)


@admin.route("/appointments/<int:id>/cancel", methods=["POST"])
@admin_required
def cancel_appt(id):
    appt = Appointment.query.get_or_404(id)
    appt.status = "cancelled"

    log_action(
        session["admin_id"],
        "CANCEL_APPOINTMENT",
        "appointment",
        appt.id
    )

    db.session.commit()
    return redirect("/admin/appointments")


@admin.route("/coupons")
@admin_required
def admin_coupons():
    coupons = Coupon.query.all()
    return render_template("admin/coupons.html", coupons=coupons)


@admin.route("/coupons/<int:id>/void", methods=["POST"])
@admin_required
def void_coupon(id):
    coupon = Coupon.query.get_or_404(id)
    coupon.is_used = True

    log_action(
        session["admin_id"],
        "VOID_COUPON",
        "coupon",
        coupon.id
    )

    db.session.commit()
    return redirect("/admin/coupons")
