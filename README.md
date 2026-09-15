# CineBookAI 🎬

> **AI-powered movie discovery and online movie ticket booking platform built with Django.**

CineBookAI is a full-stack movie ticket booking web application that combines **movie discovery, AI-powered recommendations, AI movie assistance, seat selection, online payments, digital tickets, and booking management** into one platform.

The project is designed with a modern, cinematic interface and supports responsive usage across desktop and mobile devices.

---

## 🌟 Overview

CineBookAI provides an end-to-end movie booking experience:

**Discover → Explore → Choose Showtime → Select Seats → Enter Details → Pay → Get Digital Ticket → Manage Booking**

The application combines traditional movie-booking functionality with AI-powered features to make movie discovery and decision-making easier.

---

## ✨ Features

### 🎬 Movie Discovery

- Browse currently available movies
- Search movies
- Filter movies
- View detailed movie information
- Movie posters and metadata through TMDB integration
- Movie language and genre information
- Showtime information

### 🤖 AI Features

- **AI Movie Recommendations**
  - Provides movie recommendations based on available movie information and user interaction.

- **AI Movie Assistant**
  - Conversational movie assistant for movie-related questions and discovery.

- Powered by the **Groq API**

### 🎟️ Movie Ticket Booking

Complete booking workflow:

```text
Home
  ↓
Movie Details
  ↓
Showtimes
  ↓
Seat Selection
  ↓
Your Details
  ↓
Payment
  ↓
Digital Ticket
  ↓
My Bookings
```

### 💺 Seat Selection & Pricing

CineBookAI supports multiple seat categories:

| Seat Category | Price |
|---|---:|
| Normal | ₹150 |
| Premium | ₹200 |
| Luxury / Recliner | ₹270 |

The booking total is calculated from the **individual prices of the selected seats**.

For example:

```text
Normal       ₹150
Premium      ₹200
Luxury       ₹270
------------------
Total        ₹620
```

Booked seats are protected from being selected again.

### 💳 Online Payment

- Razorpay integration
- Razorpay Test Mode
- Payment amount validation
- Booking/payment relationship
- Payment status handling
- Secure checkout flow

> Razorpay is currently configured for testing and does not process real-money transactions in the project configuration.

### 🎫 Digital Ticket

After a successful booking:

- Digital ticket is generated
- Booking information is displayed
- QR code is provided
- Movie, cinema, showtime and seat information are included
- Ticket can be accessed from the booking system

### 📋 My Bookings

Users can:

- View their bookings
- View booking details
- Access digital tickets
- Check booking status
- Cancel eligible bookings

### ❤️ Watchlist / Favorites

Users can save movies they are interested in and manage their personal movie watchlist.

### ⭐ Reviews & Ratings

Users can:

- Rate movies
- Write reviews
- View movie reviews and ratings

### 🔔 Notifications

CineBookAI includes an in-app notification system for important movie and booking-related events.

The project also includes automatic show reminders.

### 👤 User Profile

Users can manage:

- Profile information
- Account details
- Booking history
- Personal movie activity

### 🛠️ Admin

The project includes:

- Django Admin
- Custom Admin Dashboard
- Movie management
- Cinema management
- Showtime management
- Seat management
- Booking management
- User-related management
- Notification management

### 📱 Responsive Design

The interface is designed to work across:

- Desktop
- Laptop
- Tablet
- Mobile

The Home page includes dedicated responsive layout improvements for smaller screens.

---

## 🧠 Technology Stack

### Backend

- **Python 3.14.7**
- **Django 6.1.1**
- Django ORM
- Gunicorn

### Database

- **PostgreSQL**
- **Supabase** for production database hosting
- SQLite for local development

### AI

- **Groq API**

### External APIs & Services

- **TMDB API** — movie information and metadata
- **Razorpay** — payment processing
- **Supabase** — production PostgreSQL database
- **Render** — production hosting

### Frontend

- HTML5
- CSS3
- JavaScript
- Django Templates

### Python Packages

Main dependencies include:

```text
Django
Groq
Razorpay
Requests
psycopg
Gunicorn
python-dotenv
```

The complete dependency list is available in:

```text
requirements.txt
```

---

## 🏗️ Project Structure

The project follows a Django-based structure:

```text
AIMobileTicketBooking/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── ...
│
├── movies/
│   ├── migrations/
│   ├── templates/
│   │   └── movies/
│   ├── static/
│   ├── models.py
│   ├── views.py
│   ├── signals.py
│   ├── notifications.py
│   ├── tmdb_utils.py
│   └── ...
│
├── templates/
│
├── manage.py
├── requirements.txt
├── render.yaml
├── .gitignore
└── README.md
```

---

## ⚙️ Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/rohit-f-13-glitch/CineBookAI.git
cd CineBookAI
```

### 2. Create a virtual environment

Using Python:

```bash
python -m venv .venv
```

Activate it on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file and add the required environment variables.

Do **not** commit `.env` or any API keys/secrets to GitHub.

Typical configuration includes values for:

```text
SECRET_KEY
DEBUG
DATABASE_URL
TMDB_API_KEY
GROQ_API_KEY
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
```

Use the actual variable names expected by the project configuration.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

Follow the Django prompts.

### 7. Start the development server

```bash
python manage.py runserver
```

The application will normally be available at:

```text
http://127.0.0.1:8000/
```

---

## 🔐 Environment & Security

Sensitive credentials should **never** be committed to the repository.

Keep secrets in environment variables:

```text
.env
```

The following types of files should remain local and should not be uploaded to GitHub:

```text
.env
database backups
local SQLite databases
API keys
private credentials
local data/import files
```

For production, configure secrets through the hosting platform's environment-variable system.

---

## 🚀 Deployment

CineBookAI is deployed using **Render**.

The project includes:

```text
render.yaml
```

Current Render configuration uses:

```yaml
runtime: python
buildCommand: "pip install -r requirements.txt"
startCommand: "gunicorn config.wsgi:application"
```

Python version:

```text
3.14.7
```

The production database is hosted using **Supabase PostgreSQL**.

---

## 🗄️ Production Database

The production environment uses PostgreSQL through Supabase.

The application connects through the `DATABASE_URL` environment variable.

Local development can use SQLite while the deployed application uses PostgreSQL.

This allows the project to maintain a lightweight local development environment while using a hosted relational database in production.

---

## 💳 Razorpay

CineBookAI integrates Razorpay for the online payment workflow.

Current implementation uses **Razorpay Test Mode** for development and demonstration.

The payment flow is:

```text
Booking
   ↓
Payment Page
   ↓
Razorpay Checkout
   ↓
Payment Verification
   ↓
Booking Confirmation
   ↓
Digital Ticket
```

No real-money transactions should be performed using the test configuration.

---

## 🎞️ TMDB Integration

CineBookAI integrates with **The Movie Database (TMDB)** to retrieve movie-related information.

The integration is used for movie metadata such as:

- Movie title
- Poster
- Overview
- Language
- Genre
- Other movie information

The TMDB API key is stored as an environment variable and should never be exposed publicly.

---

## 🤖 AI Architecture

CineBookAI uses the Groq API for AI-powered functionality.

The AI layer supports:

```text
User
 ↓
CineBookAI Application
 ↓
AI Processing
 ↓
Groq API
 ↓
AI Response
 ↓
User
```

AI functionality is integrated into the movie experience rather than being a separate standalone chatbot application.

---

## 📊 Booking & Seat Logic

The booking system maintains relationships between:

```text
Cinema
   ↓
Screen
   ↓
Showtime
   ↓
Seats
   ↓
Booking
   ↓
Payment
```

Seats are associated with cinemas and have their own category and price.

The booking amount is calculated from the selected seats rather than simply multiplying the number of seats by a single showtime price.

This allows different seat categories to have different prices within the same booking.

---

## 🧪 Testing

Before deploying changes, the application can be checked with:

```bash
python manage.py check
```

Python package consistency can be checked with:

```bash
python -m pip check
```

For booking-related changes, the recommended manual flow is:

```text
Login
 ↓
Movie
 ↓
Showtime
 ↓
Select Seats
 ↓
Your Details
 ↓
Payment
 ↓
Digital Ticket
 ↓
My Bookings
```

For seat pricing, test a combination of:

```text
Normal + Premium + Luxury
```

and verify that the final amount equals the sum of the individual seat prices.

---

## 📱 Mobile Experience

CineBookAI includes responsive UI improvements for mobile users.

The main booking flow is designed to remain usable on smaller screens:

```text
Movie Discovery
      ↓
Movie Details
      ↓
Showtime
      ↓
Seat Selection
      ↓
Checkout
      ↓
Digital Ticket
```

The deployed application has been tested on mobile devices.

---

## 🛡️ Production Readiness

The project is being prepared beyond basic functionality with a production-readiness pass covering:

- Security configuration
- Environment variables
- Database configuration
- Payment-flow verification
- AI error handling
- Responsive UI
- Admin interface
- Code cleanup
- GitHub repository cleanup
- Deployment verification

---

## 🔮 Future Improvements

Potential future improvements include:

- Advanced AI personalization
- More sophisticated recommendation algorithms
- Real cinema/theatre integrations
- Additional payment options
- Email/SMS booking notifications
- Advanced analytics dashboard
- Automated test suite
- CI/CD pipeline
- Improved caching and performance
- Production monitoring
- More detailed booking analytics

---

## 📸 Screenshots

Screenshots can be added here to showcase the major parts of the application.

Recommended screenshots:

```text
Home Page
Movie Details
AI Recommendations
AI Movie Assistant
Seat Selection
Payment
Digital Ticket
My Bookings
Admin Dashboard
Mobile View
```

---

## 🌐 Live Application

**CineBookAI is deployed on Render.**

Live application:

```text
https://cinebookai.onrender.com/
```

---

## 👨‍💻 Developer

**Rohit Favade**

CineBookAI is a full-stack learning and portfolio project focused on combining:

- Web development
- Artificial Intelligence
- Database systems
- Payment integration
- API integration
- Cloud deployment

---

## 📄 License

This project is currently intended as a personal learning and portfolio project.

If you plan to reuse, distribute, or commercially deploy the project, add an appropriate open-source license and review the licensing requirements of the third-party services and APIs used by the application.

---

## ⭐ Project Goal

The goal of CineBookAI is to build a complete, practical AI-powered web application rather than a collection of isolated demonstrations.

It combines:

```text
Django
+
PostgreSQL
+
AI
+
TMDB
+
Razorpay
+
Responsive UI
+
Cloud Deployment
=
CineBookAI
```

**Built to make movie discovery and ticket booking smarter. 🎬**