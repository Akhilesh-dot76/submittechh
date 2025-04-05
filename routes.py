from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
def url_parse(url):
    return urlparse(url)
from datetime import datetime
from app import db
from app.models import User, Medication
from app.forms import LoginForm, RegistrationForm, MedicationForm

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.home')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# In app/routes.py, update your registration route:
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            app.logger.error(f'Registration error: {str(e)}')
    return render_template('register.html', title='Register', form=form)
    return render_template('register.html', title='Register', form=form)

@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html')

@main.route('/medications', methods=['GET'])
@login_required
def medications():
    status_filter = request.args.get('status')
    sort_by = request.args.get('sort', 'name')  # Default sort by name
    
    query = Medication.query.filter_by(user_id=current_user.id)
    
    if status_filter in ['Active', 'Discontinued']:
        query = query.filter_by(status=status_filter)
    
    if sort_by == 'name':
        medications = query.order_by(Medication.name).all()
    elif sort_by == 'date':
        medications = query.order_by(Medication.start_date).all()
    else:
        medications = query.all()
    
    active_count = Medication.query.filter_by(
        user_id=current_user.id, status='Active').count()
    discontinued_count = Medication.query.filter_by(
        user_id=current_user.id, status='Discontinued').count()
    
    return render_template(
        'medications.html',
        medications=medications,
        active_count=active_count,
        discontinued_count=discontinued_count,
        current_filter=status_filter,
        current_sort=sort_by
    )

@main.route('/medication/<int:id>')
@login_required
def medication(id):
    med = Medication.query.get_or_404(id)
    if med.user_id != current_user.id:
        abort(403)
    return render_template('medication.html', medication=med)

@main.route('/add_medication', methods=['GET', 'POST'])
@login_required
def add_medication():
    form = MedicationForm()
    if form.validate_on_submit():
        med = Medication(
            name=form.name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            start_date=form.start_date.data,
            notes=form.notes.data,
            status=form.status.data,
            user_id=current_user.id
        )
        db.session.add(med)
        db.session.commit()
        flash('Medication added successfully!')
        return redirect(url_for('main.medications'))
    return render_template('add_medication.html', title='Add Medication', form=form)

@main.route('/edit_medication/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_medication(id):
    med = Medication.query.get_or_404(id)
    if med.user_id != current_user.id:
        abort(403)
    form = MedicationForm(obj=med)
    if form.validate_on_submit():
        med.name = form.name.data
        med.dosage = form.dosage.data
        med.frequency = form.frequency.data
        med.start_date = form.start_date.data
        med.notes = form.notes.data
        med.status = form.status.data
        db.session.commit()
        flash('Medication updated successfully!')
        return redirect(url_for('main.medication', id=med.id))
    return render_template('edit_medication.html', title='Edit Medication', form=form)

@main.route('/delete_medication/<int:id>', methods=['POST'])
@login_required
def delete_medication(id):
    med = Medication.query.get_or_404(id)
    if med.user_id != current_user.id:
        abort(403)
    db.session.delete(med)
    db.session.commit()
    flash('Medication deleted successfully!')
    return redirect(url_for('main.medications'))