def welcome_email():
    return f"""
Welcome to Nancy's ✨

Thank you so much for choosing me.

We believe getting your nails done should be the most relaxing part of your week. Our team of pros is here to make sure your experience is safe, clean, and absolutely lovely from start to finish.
As a little "thank you" for being here, we love sending our clients special discounts and seasonal surprises.
We look forward to seeing you soon! 💅
 
Best, Nancy
"""

def appointment_email(time, cancel_link, reschedule_link):
    return f"""
You’re All Booked! 

We are so excited to see you! We have your spot reserved and our team is ready to give you a relaxing, top-quality experience.

Your Appointment: 
• When: {time}

Change of plans? Life happens! If you need to adjust your time, just let us know: 
Reschedule: {reschedule_link} | Cancel {cancel_link}

We can’t wait to pamper you ✨
See you soon, Nancy
"""

def coupon_email(code, expires_at):
    return f"""
A Special Gift Just for You 🎁

As a thank you for choosing our salon,
we're excited to offer you an exclusive discount.

🎟 Coupon Code: {code}
⏳ Valid Until: {expires_at}

Enjoy premium nail care provided by licensed professionals
in a clean, relaxing environment.

This coupon is valid for one-time use and expires in 7 days,
so don't miss your chance to treat yourself!

We look forward to seeing you 💅✨

Nancy
"""
