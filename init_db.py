from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create all tables
    db.create_all()
    
    # Create admin user if not exists
    if not Admin.query.first():
        admin = Admin(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()
        print("Admin user created with username: 'admin' and password: 'admin'")
    
    print("Database initialized successfully!")