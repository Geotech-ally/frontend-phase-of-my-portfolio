# app.py - Main Flask Application for Geoffrey Akoo Portfolio
import os
import logging
import json
import math
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('portfolio.log'),
        logging.StreamHandler()
    ]
)

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()

# Database Models
class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContactMessage(db.Model, TimestampMixin):
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    service = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='new')
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'service': self.service,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Project(db.Model, TimestampMixin):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    full_description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    technologies = db.Column(db.Text)
    featured_image = db.Column(db.String(255))
    live_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    client = db.Column(db.String(100))
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='published')
    featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    
    images = db.relationship('ProjectImage', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'description': self.description,
            'full_description': self.full_description,
            'category': self.category,
            'technologies': json.loads(self.technologies) if self.technologies else [],
            'featured_image': self.featured_image,
            'live_url': self.live_url,
            'github_url': self.github_url,
            'client': self.client,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'status': self.status,
            'featured': self.featured,
            'views': self.views,
            'created_at': self.created_at.isoformat(),
            'images': [img.to_dict() for img in self.images]
        }

class ProjectImage(db.Model):
    __tablename__ = 'project_images'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'image_url': self.image_url,
            'caption': self.caption,
            'is_primary': self.is_primary,
            'order': self.order
        }

class BlogPost(db.Model, TimestampMixin):
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(255))
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.Text)
    author = db.Column(db.String(100), default='Geoffrey Akoo')
    status = db.Column(db.String(20), default='published')
    featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    reading_time = db.Column(db.Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'excerpt': self.excerpt,
            'content': self.content,
            'featured_image': self.featured_image,
            'category': self.category,
            'tags': json.loads(self.tags) if self.tags else [],
            'author': self.author,
            'status': self.status,
            'featured': self.featured,
            'views': self.views,
            'reading_time': self.reading_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Subscriber(db.Model, TimestampMixin):
    __tablename__ = 'subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'active': self.active,
            'subscribed_at': self.subscribed_at.isoformat()
        }

class User(db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='admin')
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

# Utility Functions
class Validators:
    @staticmethod
    def is_valid_email(email):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_valid_phone(phone):
        import re
        pattern = r'^[\+]?[0-9\s\-\(\)]{10,}$'
        return re.match(pattern, phone) is not None if phone else True
    
    @staticmethod
    def is_valid_url(url):
        from urllib.parse import urlparse
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def sanitize_input(text):
        if not text:
            return text
        return text.replace('<', '&lt;').replace('>', '&gt;')
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    @staticmethod
    def validate_contact_form(data):
        errors = {}
        
        name = data.get('name', '').strip()
        if not name or len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters long'
        
        email = data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email is required'
        elif not Validators.is_valid_email(email):
            errors['email'] = 'Please provide a valid email address'
        
        message = data.get('message', '').strip()
        if not message or len(message) < 10:
            errors['message'] = 'Message must be at least 10 characters long'
        
        phone = data.get('phone', '').strip()
        if phone and not Validators.is_valid_phone(phone):
            errors['phone'] = 'Please provide a valid phone number'
        
        return errors

class EmailService:
    @staticmethod
    def send_contact_notification(contact_message):
        try:
            subject = f"New Contact Message from {contact_message.name}"
            
            msg = Message(
                subject=subject,
                recipients=[app.config['MAIL_USERNAME']],
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.body = f"""
New contact form submission:

Name: {contact_message.name}
Email: {contact_message.email}
Phone: {contact_message.phone or 'Not provided'}
Service: {contact_message.service or 'Not specified'}

Message:
{contact_message.message}

Submitted on: {contact_message.created_at}
IP Address: {contact_message.ip_address}
            """
            
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error sending contact notification: {str(e)}")
            return False

    @staticmethod
    def send_auto_reply(contact_message):
        try:
            subject = "Thank you for contacting Geoffrey Akoo"
            
            msg = Message(
                subject=subject,
                recipients=[contact_message.email],
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.body = f"""
Dear {contact_message.name},

Thank you for reaching out to me! I have received your message and will get back to you within 24 hours.

Here's a copy of your message:
{contact_message.message}

Best regards,
Geoffrey Akoo
Web Developer & IT Specialist
            """
            
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error sending auto-reply: {str(e)}")
            return False

    @staticmethod
    def send_newsletter_confirmation(subscriber):
        try:
            subject = "Welcome to Geoffrey Akoo's Newsletter"
            
            msg = Message(
                subject=subject,
                recipients=[subscriber.email],
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            msg.body = f"""
Hi {subscriber.name or 'there'},

Thank you for subscribing to my newsletter! You'll now receive updates about:
- New projects and case studies
- Latest blog posts on web development and IT
- Technology tips and insights
- Industry news and trends

You can unsubscribe at any time by replying to this email.

Best regards,
Geoffrey Akoo
            """
            
            mail.send(msg)
            return True
        except Exception as e:
            app.logger.error(f"Error sending newsletter confirmation: {str(e)}")
            return False

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Token is missing'
            }), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user or not current_user.active:
                return jsonify({
                    'success': False,
                    'message': 'Invalid token'
                }), 401
        except Exception as e:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Create Flask application
def create_app():
    app = Flask(__name__)
    
    # Configuration
    env = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    
    # Enable CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    return app

# Configuration classes
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///portfolio.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@geoffreyakoo.com'
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5000',
        'http://localhost:8000',
        'https://geoffreyakoo.com',
        'https://www.geoffreyakoo.com'
    ]
    API_PREFIX = '/api/v1'
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Create app instance
app = create_app()

# Ensure upload directory exists
with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables and default admin
with app.app_context():
    db.create_all()
    
    # Create default admin user if none exists
    admin_exists = User.query.filter_by(role='admin').first()
    if not admin_exists:
        admin = User(
            username=os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin'),
            email=os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@geoffreyakoo.com'),
            role='admin'
        )
        admin.set_password(os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal Server Error: {str(error)}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({
        'success': False,
        'message': 'File too large'
    }), 413

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'Bad request'
    }), 400

# Routes
@app.route('/')
def home():
    return jsonify({
        'success': True,
        'message': 'Geoffrey Akoo Portfolio API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

@app.route('/api/v1/stats')
def get_stats():
    try:
        stats = {
            'projects': Project.query.filter_by(status='published').count(),
            'blog_posts': BlogPost.query.filter_by(status='published').count(),
            'total_contacts': ContactMessage.query.count(),
            'new_contacts': ContactMessage.query.filter_by(status='new').count(),
            'subscribers': Subscriber.query.filter_by(active=True).count(),
            'total_views': db.session.query(db.func.sum(Project.views)).scalar() or 0
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logging.error(f"Error fetching stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching statistics'
        }), 500

# Contact Routes
@app.route('/api/v1/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        errors = Validators.validate_contact_form(data)
        if errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        contact_message = ContactMessage(
            name=Validators.sanitize_input(data['name']),
            email=data['email'].strip().lower(),
            phone=Validators.sanitize_input(data.get('phone', '')),
            service=data.get('service', ''),
            message=Validators.sanitize_input(data['message']),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        db.session.add(contact_message)
        db.session.commit()
        
        if app.config['MAIL_USERNAME']:
            EmailService.send_contact_notification(contact_message)
            EmailService.send_auto_reply(contact_message)
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your message! I will get back to you soon.',
            'data': contact_message.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Error processing contact form: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your message. Please try again.'
        }), 500

# Project Routes
@app.route('/api/v1/projects', methods=['GET'])
def get_projects():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 9, type=int)
        category = request.args.get('category', 'all')
        featured = request.args.get('featured', type=bool)
        
        query = Project.query.filter(Project.status == 'published')
        
        if category != 'all':
            query = query.filter(Project.category == category)
        
        if featured is not None:
            query = query.filter(Project.featured == featured)
        
        projects = query.order_by(Project.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [project.to_dict() for project in projects.items],
            'pagination': {
                'page': projects.page,
                'per_page': projects.per_page,
                'total': projects.total,
                'pages': projects.pages
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching projects: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching projects'
        }), 500

@app.route('/api/v1/projects/<slug>', methods=['GET'])
def get_project(slug):
    try:
        project = Project.query.filter_by(slug=slug, status='published').first_or_404()
        
        project.views += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': project.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error fetching project: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Project not found'
        }), 404

# Blog Routes
def calculate_reading_time(content):
    words_per_minute = 200
    word_count = len(content.split())
    return math.ceil(word_count / words_per_minute)

@app.route('/api/v1/blog/posts', methods=['GET'])
def get_blog_posts():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 6, type=int)
        category = request.args.get('category', 'all')
        featured = request.args.get('featured', type=bool)
        
        query = BlogPost.query.filter(BlogPost.status == 'published')
        
        if category != 'all':
            query = query.filter(BlogPost.category == category)
        
        if featured is not None:
            query = query.filter(BlogPost.featured == featured)
        
        posts = query.order_by(BlogPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [post.to_dict() for post in posts.items],
            'pagination': {
                'page': posts.page,
                'per_page': posts.per_page,
                'total': posts.total,
                'pages': posts.pages
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching blog posts: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching blog posts'
        }), 500

@app.route('/api/v1/blog/posts/<slug>', methods=['GET'])
def get_blog_post(slug):
    try:
        post = BlogPost.query.filter_by(slug=slug, status='published').first_or_404()
        
        post.views += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': post.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error fetching blog post: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Blog post not found'
        }), 404

@app.route('/api/v1/blog/subscribe', methods=['POST'])
def subscribe_newsletter():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        if not Validators.is_valid_email(email):
            return jsonify({
                'success': False,
                'message': 'Please provide a valid email address'
            }), 400
        
        existing_subscriber = Subscriber.query.filter_by(email=email).first()
        if existing_subscriber:
            if existing_subscriber.active:
                return jsonify({
                    'success': False,
                    'message': 'This email is already subscribed'
                }), 400
            else:
                existing_subscriber.active = True
                existing_subscriber.name = name
                db.session.commit()
                subscriber = existing_subscriber
        else:
            subscriber = Subscriber(email=email, name=name)
            db.session.add(subscriber)
            db.session.commit()
        
        if app.config['MAIL_USERNAME']:
            EmailService.send_newsletter_confirmation(subscriber)
        
        return jsonify({
            'success': True,
            'message': 'Successfully subscribed to newsletter!'
        })
        
    except Exception as e:
        logging.error(f"Error subscribing to newsletter: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error subscribing to newsletter'
        }), 500

# File Upload Route
@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        if file and Validators.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            file_url = f"/static/uploads/{filename}"
            
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'data': {
                    'filename': filename,
                    'url': file_url,
                    'size': os.path.getsize(filepath)
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'File type not allowed'
            }), 400
            
    except Exception as e:
        logging.error(f"Error uploading file: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error uploading file'
        }), 500

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Authentication Routes
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        user = User.query.filter_by(username=username, active=True).first()
        
        if user and user.check_password(password):
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(days=7)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'token': token,
                    'user': user.to_dict()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login failed'
        }), 500

# Admin Routes (Protected)
@app.route('/api/v1/admin/contacts', methods=['GET'])
@token_required
def get_contact_messages(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status', 'all')
        
        query = ContactMessage.query
        
        if status != 'all':
            query = query.filter(ContactMessage.status == status)
        
        messages = query.order_by(ContactMessage.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [msg.to_dict() for msg in messages.items],
            'pagination': {
                'page': messages.page,
                'per_page': messages.per_page,
                'total': messages.total,
                'pages': messages.pages
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching contact messages: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching messages'
        }), 500

@app.route('/api/v1/admin/contacts/<int:contact_id>', methods=['PUT'])
@token_required
def update_contact_status(current_user, contact_id):
    try:
        contact = ContactMessage.query.get_or_404(contact_id)
        data = request.get_json()
        
        status = data.get('status', '').strip()
        if status not in ['new', 'read', 'responded', 'archived']:
            return jsonify({
                'success': False,
                'message': 'Invalid status value'
            }), 400
        
        contact.status = status
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact status updated',
            'data': contact.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating contact status: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error updating contact'
        }), 500

@app.route('/api/v1/admin/contacts/<int:contact_id>', methods=['DELETE'])
@token_required
def delete_contact(current_user, contact_id):
    try:
        contact = ContactMessage.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contact deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting contact: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error deleting contact'
        }), 500

@app.route('/api/v1/admin/projects', methods=['POST'])
@token_required
def create_project(current_user):
    try:
        data = request.get_json()
        
        required_fields = ['title', 'slug', 'description', 'category']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        existing = Project.query.filter_by(slug=data['slug']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Project with this slug already exists'
            }), 400
        
        project = Project(
            title=data['title'].strip(),
            slug=data['slug'].strip().lower(),
            description=data['description'].strip(),
            full_description=data.get('full_description', '').strip(),
            category=data['category'].strip(),
            technologies=json.dumps(data.get('technologies', [])) if data.get('technologies') else None,
            featured_image=data.get('featured_image', '').strip(),
            live_url=data.get('live_url', '').strip(),
            github_url=data.get('github_url', '').strip(),
            client=data.get('client', '').strip(),
            completion_date=data.get('completion_date'),
            status=data.get('status', 'draft'),
            featured=data.get('featured', False)
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'data': project.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating project: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error creating project'
        }), 500

@app.route('/api/v1/admin/projects/<int:project_id>', methods=['PUT'])
@token_required
def update_project(current_user, project_id):
    try:
        project = Project.query.get_or_404(project_id)
        data = request.get_json()
        
        if 'title' in data:
            project.title = data['title'].strip()
        if 'description' in data:
            project.description = data['description'].strip()
        if 'full_description' in data:
            project.full_description = data['full_description'].strip()
        if 'category' in data:
            project.category = data['category'].strip()
        if 'technologies' in data:
            project.technologies = json.dumps(data['technologies']) if data['technologies'] else None
        if 'featured_image' in data:
            project.featured_image = data['featured_image'].strip()
        if 'live_url' in data:
            project.live_url = data['live_url'].strip()
        if 'github_url' in data:
            project.github_url = data['github_url'].strip()
        if 'client' in data:
            project.client = data['client'].strip()
        if 'completion_date' in data:
            project.completion_date = data['completion_date']
        if 'status' in data:
            project.status = data['status'].strip()
        if 'featured' in data:
            project.featured = bool(data['featured'])
        
        project.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'data': project.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating project: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error updating project'
        }), 500

@app.route('/api/v1/admin/blog/posts', methods=['POST'])
@token_required
def create_blog_post(current_user):
    try:
        data = request.get_json()
        
        required_fields = ['title', 'slug', 'content', 'category']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400
        
        existing = BlogPost.query.filter_by(slug=data['slug']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': 'Blog post with this slug already exists'
            }), 400
        
        reading_time = calculate_reading_time(data['content'])
        
        post = BlogPost(
            title=data['title'].strip(),
            slug=data['slug'].strip().lower(),
            excerpt=data.get('excerpt', '').strip(),
            content=data['content'].strip(),
            featured_image=data.get('featured_image', '').strip(),
            category=data['category'].strip(),
            tags=json.dumps(data.get('tags', [])) if data.get('tags') else None,
            author=data.get('author', 'Geoffrey Akoo').strip(),
            status=data.get('status', 'draft'),
            featured=data.get('featured', False),
            reading_time=reading_time
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Blog post created successfully',
            'data': post.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating blog post: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error creating blog post'
        }), 500

@app.route('/api/v1/admin/blog/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_blog_post(current_user, post_id):
    try:
        post = BlogPost.query.get_or_404(post_id)
        data = request.get_json()
        
        if 'title' in data:
            post.title = data['title'].strip()
        if 'excerpt' in data:
            post.excerpt = data['excerpt'].strip()
        if 'content' in data:
            post.content = data['content'].strip()
            post.reading_time = calculate_reading_time(data['content'])
        if 'featured_image' in data:
            post.featured_image = data['featured_image'].strip()
        if 'category' in data:
            post.category = data['category'].strip()
        if 'tags' in data:
            post.tags = json.dumps(data['tags']) if data['tags'] else None
        if 'author' in data:
            post.author = data['author'].strip()
        if 'status' in data:
            post.status = data['status'].strip()
        if 'featured' in data:
            post.featured = bool(data['featured'])
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Blog post updated successfully',
            'data': post.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Error updating blog post: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Error updating blog post'
        }), 500

@app.route('/api/v1/admin/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        })
    except Exception as e:
        logging.error(f"Error fetching users: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching users'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logging.info(f"Starting Geoffrey Akoo Portfolio API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)