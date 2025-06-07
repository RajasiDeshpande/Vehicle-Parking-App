from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from config import Config
from models import db, User, Admin, ParkingLot, ParkingSpot, Booking

# Initialize Flask app
app = Flask(__name__, template_folder='template')
app.config.from_object(Config)

# Initialize database
db.init_app(app)


# Routes
@app.route('/')
def index():
    return render_template('index.html')

# User routes
@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('user_register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('user_login'))
    
    return render_template('user_register.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = 'user'
            flash('Login successful!')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('unauthorized'))
    
    user = User.query.get(session['user_id'])
    lots = ParkingLot.query.all()
    
    # Check if user has an active booking
    active_booking = Booking.query.filter_by(
        user_id=session['user_id'], 
        leaving_timestamp=None
    ).join(ParkingLot).add_columns(
        ParkingLot.prime_location_name.label('lot_name')
    ).first()
    
    if active_booking:
        active_booking_data = {
            'lot_name': active_booking.lot_name,
            'spot_id': active_booking[0].spot_id,
            'parking_timestamp': active_booking[0].parking_timestamp.strftime('%d %b %Y, %H:%M')
        }
    else:
        active_booking_data = None
    
    return render_template('user_dashboard.html', user=user, lots=lots, active_booking=active_booking_data)

@app.route('/user/book', methods=['POST'])
def user_book():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('unauthorized'))
    
    lot_id = request.form['lot_id']
    user_id = session['user_id']
    
    # Check if user already has an active booking
    existing_booking = Booking.query.filter_by(user_id=user_id, leaving_timestamp=None).first()
    if existing_booking:
        flash('You already have an active booking')
        return redirect(url_for('user_dashboard'))
    
    # Find available parking spot
    available_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    
    if not available_spot:
        flash('No parking spots available in this lot')
        return redirect(url_for('user_dashboard'))
    
    # Get parking lot price
    lot = ParkingLot.query.get(lot_id)
    
    # Create booking
    new_booking = Booking(
        user_id=user_id,
        spot_id=available_spot.id,
        lot_id=lot_id,
        parking_timestamp=datetime.now(),
        parking_cost=lot.price
    )
    
    # Update spot status
    available_spot.status = 'O'
    available_spot.current_booking_id = new_booking.id
    
    db.session.add(new_booking)
    db.session.commit()
    
    flash('Parking spot booked successfully')
    return redirect(url_for('user_dashboard'))

@app.route('/user/release', methods=['POST'])
def user_release():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('unauthorized'))
    
    # Find active booking
    booking = Booking.query.filter_by(user_id=session['user_id'], leaving_timestamp=None).first()
    
    if not booking:
        flash('No active booking found')
        return redirect(url_for('user_dashboard'))
    
    # Calculate total cost
    time_now = datetime.now()
    hours_parked = (time_now - booking.parking_timestamp).total_seconds() / 3600
    total_cost = hours_parked * booking.parking_cost
    
    # Update booking
    booking.leaving_timestamp = time_now
    booking.total_cost = round(total_cost, 2)
    
    # Update spot status
    spot = ParkingSpot.query.get(booking.spot_id)
    spot.status = 'A'
    spot.current_booking_id = None
    
    db.session.commit()
    
    flash(f'Spot released. Total cost: ₹{booking.total_cost}')
    return redirect(url_for('user_dashboard'))

@app.route('/user/bookings')
def user_booking_history():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('unauthorized'))
    
    # Get user's booking history
    bookings = Booking.query.filter_by(user_id=session['user_id']).join(
        ParkingLot).add_columns(ParkingLot.prime_location_name.label('lot_name')).all()
    
    booking_history = []
    for booking_item in bookings:
        booking = booking_item[0]
        lot_name = booking_item.lot_name
        booking_data = {
            'spot_id': booking.spot_id,
            'lot_name': lot_name,
            'parking_timestamp': booking.parking_timestamp.strftime('%d %b %Y, %H:%M'),
            'leaving_timestamp': booking.leaving_timestamp.strftime('%d %b %Y, %H:%M') if booking.leaving_timestamp else None,
            'total_cost': booking.total_cost
        }
        booking_history.append(booking_data)
    
    return render_template('user_booking_history.html', bookings=booking_history)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['role'] = 'admin'
            flash('Admin login successful!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    lots = ParkingLot.query.all()
    return render_template('admin_dashboard.html', lots=lots)

@app.route('/admin/lot/create', methods=['GET', 'POST'])
def lot_create():
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    if request.method == 'POST':
        name = request.form['prime_location_name']
        address = request.form['address']
        pincode = request.form['pincode']
        price = request.form['price']
        max_spots = request.form['maximum_number_of_spots']
        
        new_lot = ParkingLot(
            prime_location_name=name,
            address=address,
            pincode=pincode,
            price=price,
            maximum_number_of_spots=max_spots
        )
        
        db.session.add(new_lot)
        db.session.commit()
        
        # Create parking spots for this lot
        for i in range(1, int(max_spots) + 1):
            spot = ParkingSpot(lot_id=new_lot.id, status='A')
            db.session.add(spot)
        
        db.session.commit()
        
        flash('Parking lot created successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('lot_create.html')

@app.route('/admin/lot/<int:lot_id>')
def lot_detail(lot_id):
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    lot = ParkingLot.query.get(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    
    return render_template('lot_detail.html', lot=lot, spots=spots)

@app.route('/admin/lot/edit/<int:lot_id>', methods=['GET', 'POST'])
def lot_edit(lot_id):
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    lot = ParkingLot.query.get(lot_id)
    
    if request.method == 'POST':
        lot.prime_location_name = request.form['prime_location_name']
        lot.address = request.form['address']
        lot.pincode = request.form['pincode']
        lot.price = request.form['price']
        
        # Handle changing the number of spots
        new_max_spots = int(request.form['maximum_number_of_spots'])
        current_spots_count = ParkingSpot.query.filter_by(lot_id=lot_id).count()
        
        if new_max_spots > current_spots_count:
            # Add new spots
            for i in range(current_spots_count + 1, new_max_spots + 1):
                spot = ParkingSpot(lot_id=lot_id, status='A')
                db.session.add(spot)
        
        lot.maximum_number_of_spots = new_max_spots
        db.session.commit()
        
        flash('Parking lot updated successfully')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('lot_edit.html', lot=lot)

@app.route('/admin/lot/delete/<int:lot_id>')
def lot_delete(lot_id):
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    lot = ParkingLot.query.get(lot_id)
    
    # Check if there are active bookings
    has_active_bookings = db.session.query(Booking).join(
        ParkingSpot).filter(
            ParkingSpot.lot_id == lot_id,
            Booking.leaving_timestamp == None
        ).count() > 0
    
    if has_active_bookings:
        flash('Cannot delete lot with active bookings')
        return redirect(url_for('admin_dashboard'))
    
    # Delete associated spots and bookings
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    for spot in spots:
        Booking.query.filter_by(spot_id=spot.id).delete()
        db.session.delete(spot)
    
    db.session.delete(lot)
    db.session.commit()
    
    flash('Parking lot deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
def user_list():
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/admin/booking/<int:booking_id>')
def booking_detail(booking_id):
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    booking_data = Booking.query.join(User).join(
        ParkingLot).add_columns(
            User.name.label('username'),
            ParkingLot.prime_location_name.label('lot_name')
        ).filter(Booking.id == booking_id).first()
    
    if not booking_data:
        return redirect(url_for('admin_dashboard'))
    
    booking = booking_data[0]
    booking_info = {
        'username': booking_data.username,
        'lot_name': booking_data.lot_name,
        'spot_id': booking.spot_id,
        'parking_timestamp': booking.parking_timestamp.strftime('%d %b %Y, %H:%M'),
        'leaving_timestamp': booking.leaving_timestamp.strftime('%d %b %Y, %H:%M') if booking.leaving_timestamp else None,
        'parking_cost': booking.parking_cost,
        'total_cost': booking.total_cost
    }
    
    return render_template('booking_detail.html', booking=booking_info)

@app.route('/admin/charts')
def charts():
    if 'admin_id' not in session or session['role'] != 'admin':
        return redirect(url_for('unauthorized'))
    
    lots = ParkingLot.query.all()
    
    labels = []
    available_data = []
    occupied_data = []
    
    for lot in lots:
        labels.append(lot.prime_location_name)
        
        # Count available spots
        available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        available_data.append(available)
        
        # Count occupied spots
        occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        occupied_data.append(occupied)
    
    return render_template('charts.html', labels=labels, available_data=available_data, occupied_data=occupied_data)

# Utility routes
@app.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        # Check if admin exists, if not create one
        if not Admin.query.first():
            admin = Admin(username='admin', password=generate_password_hash('admin'))
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)