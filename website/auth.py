from flask import Blueprint, render_template, request, redirect, url_for, flash
from .models import User
from . import db
from flask_login import login_user, logout_user, login_required
from .reset_email import send_reset_email
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')


        if not email or not password:
            flash("Please enter both email and password.", category='error')
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()

        if user:
            now = datetime.utcnow()

            # Check if user is locked out
            if user.lockout_until and now < user.lockout_until:
                remaining = int((user.lockout_until - now).total_seconds() // 60) + 1
                flash(f'Too many failed attempts. Try again in {remaining} minute(s).', 'warning')
                return render_template("login.html")

            # Password check
            if user.check_password(password):
                # Reset lockout counters
                user.failed_attempts = 0
                user.lockout_until = None
                db.session.commit()

                login_user(user)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                # Wrong password
                user.failed_attempts += 1

                if user.failed_attempts >= 3:
                    user.lockout_until = now + timedelta(minutes=5)
                    flash("Too many failed attempts. Your account is locked for 5 minutes.", category='danger')
                else:
                    flash("Incorrect password. Please try again.", category='error')

                db.session.commit()
                return render_template("login.html")
        else:
            flash("No account found with that email.", category='error')
            return render_template("login.html")

    return render_template("login.html")



@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Check if passwords match
        if password1 != password2:
            flash('Passwords do not match.', category='error')
            return render_template("sign_up.html")

        # Check if a user with that username or email already exists
        user_by_email = User.query.filter_by(email=email).first()
        user_by_username = User.query.filter_by(username=username).first()

        if user_by_email:
            flash('Email already exists.', category='error')
            return render_template("sign_up.html")
        if user_by_username:
            flash('Username already exists.', category='error')
            return render_template("sign_up.html")

        # Create a new user
        new_user = User(email=email, username=username)
        new_user.set_password(password1)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the account.', category='error')
            return render_template("sign_up.html")

        login_user(new_user)
        flash('Account created successfully!', category='success')
        return redirect(url_for('views.home'))

    return render_template("sign_up.html")


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', category='info')
    return redirect(url_for('auth.login'))


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'error')
        return redirect(url_for('auth.reset_request'))

    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_token', token=token))
        user.set_password(password)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_token.html', token=token)




@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
 if request.method == 'POST':
     email = request.form.get('email')
     user = User.query.filter_by(email=email).first()
     if user:
         send_reset_email(user)
         flash('An email has been sent with instructions to reset your password.', 'info')
         return redirect(url_for('auth.login'))
     else:
         flash('No account found with that email.', 'error')
 return render_template('reset_request.html')