from flask_mail import Message
from flask import url_for, current_app
from . import mail


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
    
{reset_url}

If you did not make this request, simply ignore this email.
'''
    try:
        mail.send(msg)
    except Exception as e:
        # Log the error or flash a message if needed
        current_app.logger.error(f"Failed to send email: {e}")

