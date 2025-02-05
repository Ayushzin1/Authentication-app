# FastAPI Authentication and Data Integration API

## Project Structure

### Main Application (`app/main.py`)
- Entry point of the application
- Configures CORS middleware
- Initializes database
- Registers all routers (auth, users, crypto, weather)

### Database (`app/database.py`)
- SQLAlchemy configuration
- Database connection setup
- Session management

### Models (`app/models/user.py`)
- User model definition
- Database schema for user information
- Fields: email, password, profile details

### Routers

#### Authentication (`app/routers/auth.py`)
Endpoints:
- `POST /auth/register`: New user registration
- `POST /auth/login`: User login
- `POST /auth/facebook-login`: Facebook OAuth integration
- `POST /auth/logout`: User logout with token blacklisting

#### User Profile (`app/routers/users.py`)
Endpoints:
- `GET /users/profile`: Get user profile
- `PUT /users/profile`: Update profile details
- `PUT /users/profile/password`: Change password
- `POST /users/profile/photo`: Upload profile photo
- `PUT /users/profile/photo-url`: Update photo URL

#### Cryptocurrency (`app/routers/crypto.py`)
Endpoints:
- `GET /crypto/tickers`: List all cryptocurrencies
  - Supports sorting, filtering, pagination
- `GET /crypto/ticker/{symbol}`: Get specific coin details
- `GET /crypto/chart/{symbol}`: Get coin price history graph

#### Weather (`app/routers/weather.py`)
Endpoints:
- `GET /weather/temperature`: Get temperature data from stations
  - Returns location and temperature information

## API Documentation
Access the interactive API documentation at:
- Swagger UI: `http://localhost:8008/docs`
- ReDoc: `http://localhost:8008/redoc`

## Environment Setup
Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `FACEBOOK_APP_ID`: Facebook OAuth app ID
- `FACEBOOK_APP_SECRET`: Facebook OAuth secret
