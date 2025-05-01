# Customer Feedback Form

A Streamlit application for collecting customer feedback with MySQL database storage.

## Project Structure

```
├── frontend/           # Streamlit frontend application
│   └── app.py         # Main Streamlit app (UI only)
├── backend/           # Backend logic and form handling
│   ├── feedback_service.py  # Database operations for feedback
│   ├── form_handler.py      # Form page rendering and navigation
│   └── ui_components.py     # UI component definitions and text
├── database/          # Database schema and connection
│   ├── connection.py  # Database connection setup
│   └── models.py      # SQLAlchemy ORM models
├── config/            # Configuration files
│   └── settings.py    # Global application settings
├── utils/             # Utility functions
│   ├── validators.py  # Form validation utilities
│   └── image_utils.py # Image handling utilities
├── static/            # Static assets
│   ├── images/        # Image assets
│   ├── css/           # CSS files
│   └── js/            # JavaScript files
└── run.py             # Entry point script to run the application
```

## Setup Instructions

### 1. Install Dependencies

Install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Database Configuration

1. Copy the `.env.example` file to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your MySQL database credentials (this will be used if not using Streamlit Cloud):
   ```
   DB_USERNAME=your_database_username
   DB_PASSWORD=your_database_password
   DB_HOST=your_database_host
   DB_PORT=3306
   DB_NAME=your_database_name
   ```

3. For Streamlit Cloud deployment, configure the same settings in the Streamlit secrets management.

### 3. Run the Application

```bash
# Option 1: Use the run.py script
python run.py

# Option 2: Run directly with Streamlit
streamlit run frontend/app.py
```

## Features

- Mobile-responsive customer feedback form
- Multi-language support (English and Arabic)
- Clean separation of frontend and backend logic
- Modular architecture for maintainability
- MySQL database integration
- NPS (Net Promoter Score) implementation
- Form validation
- Thank-you page with incentives for first-time visitors

## Tech Stack

- Frontend: Streamlit
- Backend: Python, SQLAlchemy
- Database: MySQL

## Development

The codebase follows a modular architecture with:

- Frontend: Only UI rendering with Streamlit
- Backend: Business logic and form handling
- Database: ORM models and connection management
- Config: Application settings
- Utils: Helper functions and utilities
