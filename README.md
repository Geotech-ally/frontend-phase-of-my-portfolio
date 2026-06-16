# Geoffrey Akoo Portfolio - Backend API

A professional Flask-based REST API for Geoffrey Akoo's portfolio website with project management, blog, contact handling, and authentication.

## Features

- **Project Management** - Create, read, update projects with categories and technologies
- **Blog System** - Full blog CMS with automatic reading time calculation
- **Contact Form** - Contact submissions with email notifications and auto-replies
- **Newsletter** - Email subscription management
- **Admin Dashboard** - Authenticated admin routes for content management
- **File Upload** - Secure file upload with type validation
- **Database** - SQLAlchemy ORM with SQLite (development) or PostgreSQL (production)
- **Security** - JWT authentication, password hashing with bcrypt, input validation
- **Email** - Email notifications via Flask-Mail (Gmail, SendGrid, etc.)
- **CORS** - Cross-origin resource sharing for frontend integration

## Requirements

- Python 3.8+
- pip (Python package manager)

## Installation

### 1. Clone/Download the Project

```bash
cd "C:\Users\sudo\Documents\business website"
```

### 2. Install Dependencies

**Option A: Using requirements.txt (Recommended)**

```bash
pip install -r requirements.txt
```

**Option B: Individual Installation**

```bash
pip install Flask==2.3.3
pip install Flask-SQLAlchemy==3.0.5
pip install Flask-Bcrypt==1.0.1
pip install Flask-Mail==0.9.1
pip install Flask-CORS==4.0.0
pip install python-dotenv==1.0.0
pip install PyJWT==2.8.1
pip install Werkzeug==2.3.7
```

### 3. Environment Configuration

Copy `.env.example` to `.env` and update with your settings:

```bash
copy .env.example .env
```

**Edit `.env` file:**

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///portfolio.db
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
DEFAULT_ADMIN_PASSWORD=change-this-password
```

### 4. Initialize Database

The database is automatically created on first run. Default admin user is created with credentials from `.env`:

- Username: `admin` (or `DEFAULT_ADMIN_USERNAME`)
- Password: `admin123` (or `DEFAULT_ADMIN_PASSWORD`)

## Running the Application

### Option 1: Using PowerShell Script (Windows)

```powershell
.\run.ps1
```

### Option 2: Using Batch Script (Windows)

```cmd
run.bat
```

### Option 3: Manual Execution

```bash
python app.py
```

The API will start on `http://localhost:5000`

## API Documentation

### Health & Status

- `GET /` - API info and version
- `GET /health` - Database health check
- `GET /api/v1/stats` - Portfolio statistics

### Contact Management

- `POST /api/v1/contact` - Submit contact form
- `GET /api/v1/admin/contacts` (Protected) - Get all contact messages
- `PUT /api/v1/admin/contacts/<id>` (Protected) - Update contact status
- `DELETE /api/v1/admin/contacts/<id>` (Protected) - Delete contact

### Projects

- `GET /api/v1/projects` - Get published projects (paginated)
- `GET /api/v1/projects/<slug>` - Get single project
- `POST /api/v1/admin/projects` (Protected) - Create project
- `PUT /api/v1/admin/projects/<id>` (Protected) - Update project

### Blog

- `GET /api/v1/blog/posts` - Get published posts (paginated)
- `GET /api/v1/blog/posts/<slug>` - Get single post
- `POST /api/v1/admin/blog/posts` (Protected) - Create blog post
- `PUT /api/v1/admin/blog/posts/<id>` (Protected) - Update blog post
- `POST /api/v1/blog/subscribe` - Subscribe to newsletter

### File Upload

- `POST /api/v1/upload` - Upload file (returns URL)

### Authentication

- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/admin/users` (Protected) - Get all users

## Protected Routes

Protected routes require JWT authentication. Include token in request header:

```
Authorization: Bearer <your-jwt-token>
```

Example using curl:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:5000/api/v1/admin/contacts
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Flask environment |
| SECRET_KEY | dev-secret-key | JWT signing key |
| DATABASE_URL | sqlite:///portfolio.db | Database connection |
| MAIL_SERVER | smtp.gmail.com | Email server |
| MAIL_PORT | 587 | Email server port |
| MAIL_USERNAME | - | Email account username |
| MAIL_PASSWORD | - | Email account password |
| MAIL_DEFAULT_SENDER | noreply@geoffreyakoo.com | Sender email |
| DEFAULT_ADMIN_USERNAME | admin | Initial admin username |
| DEFAULT_ADMIN_EMAIL | admin@geoffreyakoo.com | Initial admin email |
| DEFAULT_ADMIN_PASSWORD | admin123 | Initial admin password |
| PORT | 5000 | Server port |
| CORS_ORIGINS | localhost, geoffreyakoo.com | Allowed origins |

## Email Configuration

### Using Gmail

1. Enable 2-factor authentication on your Google account
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Add to `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Using SendGrid

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
```

## Database Models

### ContactMessage
- id, name, email, phone, service, message, status, ip_address, user_agent
- Timestamps: created_at, updated_at

### Project
- id, title, slug, description, full_description, category, technologies
- featured_image, live_url, github_url, client, completion_date
- status, featured, views
- Relations: images (ProjectImage)

### ProjectImage
- id, project_id, image_url, caption, is_primary, order

### BlogPost
- id, title, slug, excerpt, content, featured_image, category, tags
- author, status, featured, views, reading_time
- Timestamps: created_at, updated_at

### Subscriber
- id, email, name, active, subscribed_at

### User
- id, username, email, password_hash, role, active, last_login

## Logging

Logs are written to `portfolio.log` and console output. Log level is INFO by default.

## Static Files

Uploaded files are stored in `static/uploads/` with secure filenames and timestamp prefixes.

## Troubleshooting

### ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### Database Lock Error

Delete `portfolio.db` and restart:

```bash
rm portfolio.db
python app.py
```

### Port Already in Use

Change PORT in `.env`:

```env
PORT=5001
```

### Email Not Sending

- Verify `.env` credentials
- Check logs in `portfolio.log`
- Ensure less secure app access is enabled (if using Gmail)

## Production Deployment

For production:

1. Set `FLASK_ENV=production`
2. Use strong `SECRET_KEY` (generate with `python -c "import os; print(os.urandom(24).hex())"`)
3. Switch to PostgreSQL: `DATABASE_URL=postgresql://...`
4. Use gunicorn: `pip install gunicorn && gunicorn app:app`
5. Set up SSL/TLS with nginx or Apache
6. Configure proper email credentials
7. Update CORS_ORIGINS with production domain
8. Keep `.env` secure (never commit to git)

## Development

### Creating Migrations

If using Alembic for database migrations:

```bash
pip install Flask-Migrate
flask db init
flask db migrate -m "description"
flask db upgrade
```

### Running Tests

```bash
pip install pytest pytest-flask
pytest
```

## Support

For issues or feature requests, contact Geoffrey Akoo or check the GitHub repository.

## License

© 2024 Geoffrey Akoo. All rights reserved.
