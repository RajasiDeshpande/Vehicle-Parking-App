# Vehicle Parking App

A Flask-based web application for managing vehicle parking spaces. This application allows users to book parking spots and administrators to manage parking lots.

## Features

- **User Features**:
  - Account creation and authentication
  - Booking available parking spots 
  - Viewing active bookings
  - Releasing parking spots
  - Viewing booking history with costs

- **Admin Features**:
  - Dashboard for managing parking lots
  - Adding, editing, and removing parking lots
  - Viewing parking spot status in real-time
  - Viewing registered users
  - Access to usage statistics and charts

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **ORM**: SQLAlchemy
- **Frontend**: Bootstrap, HTML, Jinja2 templates
- **Charting**: Chart.js

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/vehicle-parking-app.git
   cd vehicle-parking-app
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file:
   ```
   # Security
   SECRET_KEY=your-very-secure-secret-key

   # Flask Configuration
   FLASK_APP=app.py
   FLASK_ENV=development
   DEBUG=True

   # Database
   DATABASE_URL=sqlite:///parking_app.db
   ```

5. Initialize the database:
   ```
   python init_db.py
   ```

6. Run the application:
   ```
   python app.py
   ```

7. Access the application at `http://127.0.0.1:5000`

## Default Admin Credentials

- Username: `admin`
- Password: `admin`

## Project Structure

```
Vehicle-Parking-App/
├── app.py             # Main application entry point
├── config.py          # Configuration settings
├── models.py          # Database models
├── init_db.py         # Database initialization script
├── requirements.txt   # Dependencies
├── template/          # HTML templates
│   ├── base.html      # Base template with common elements
│   ├── index.html     # Homepage template
│   └── ...            # Other templates
└── static/            # Static files (CSS, JS, images)
```

## Database Schema

The application uses the following database models:

- **User**: Regular users who book parking spots
- **Admin**: Administrative users who manage the system
- **ParkingLot**: Represents a parking location with multiple spots
- **ParkingSpot**: Individual parking spaces within a lot
- **Booking**: Records of spot reservations

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- Your Name <your.email@example.com>