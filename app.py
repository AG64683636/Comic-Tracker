import os
from collections import defaultdict
from flask import Flask, render_template, redirect, request
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import logging

from database import db
from models import Comic
from import_data import import_comics
from utils import get_comics_by_sorting

# Load environment variables
load_dotenv()

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///comics.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WTForms Upload Form
class UploadForm(FlaskForm):
    file = FileField('Upload CSV', validators=[DataRequired()])
    submit = SubmitField('Upload')

def is_database_empty():
    """
    Check if the database exists and contains any comics.
    Returns:
        bool: True if the database is empty, False otherwise.
    """
    return os.path.exists(os.path.join(app.root_path, 'comics.db')) or Comic.query.count() == 0

# Routes
@app.route('/comics')
@app.route('/')
def show_comics():
    """
    Display comics based on the selected sorting option.

    Args:
        None directly, but accepts 'sort' as a query parameter to determine sorting behavior.
        Options:
            - 'storyline': Group comics by storyline (default).
            - 'id': Sort comics by ID.
            - 'year': Sort comics by publication year.

    Returns:
        Rendered HTML page displaying comics grouped or sorted based on the selected option.
    """
    
    if is_database_empty():
         return render_template('comics.html', database_empty=True)

    # Retrieve sorting option from query parameters
    sort_option = request.args.get('sort', 'storyline')
    comics_by_storyline = get_comics_by_sorting(sort_option)
    return render_template('comics.html', comics_by_storyline=comics_by_storyline, sort_option=sort_option)

@app.route('/update_status/<int:comic_id>', methods=['POST'])
def update_status(comic_id):
    """
    Toggle the read/unread status of a comic.

    Args:
        comic_id (int): The ID of the comic whose status is to be toggled.

    Returns:
        JSON response:
            - {"success": True, "status": "Read" or "Unread"} (on success).
            - {"success": False, "error": "Error message"} (on failure).
    """
    try:
        comic = Comic.query.get(comic_id)
        if not comic:
            return {"success": False, "error": "Comic not found"}, 404

        # Toggle status
        comic.status = "Read" if comic.status == "Unread" else "Unread"
        db.session.commit()
        return {"success": True, "status": comic.status}, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}, 500


@app.route('/upload', methods=['GET', 'POST'])
def upload_comics():
    """
    Handle file uploads for importing comics into the database.

    Processes uploaded CSV files to add or update comics in the database.

    Args:
        None directly, but expects a POST request with a CSV file.

    Returns:
        Rendered HTML page:
            - Redirect to '/' on success.
            - Error message on invalid file format or upload failure.
    """
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if not file.filename.endswith('.csv'):
            return "Invalid file format. Please upload a CSV.", 400

        filepath = os.path.join(app.root_path, 'uploads', file.filename)
        try:
            file.save(filepath)
            import_comics(filepath)
            return redirect('/')
        except Exception as e:
            logger.error(f"Error during file upload or import: {e}")
            return "An error occurred during file upload or import.", 500

    return render_template('upload.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Application startup
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database initialized.")
    app.run(debug=True)
