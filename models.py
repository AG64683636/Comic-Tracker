from database import db

class Comic(db.Model):
    """
    Represents a comic issue in the database.

    This class defines the schema for the `comics` table and provides fields 
    to store information about individual comic issues, including their 
    publication details, storyline information, availability, and status.

    Attributes:
        id (int): Primary key for the comic record.
        issue (str): Full name of the comic series (e.g., "Action Comics").
        issue_number (str): The issue number within the series.
        issue_title (str): Title of the issue, fetched from the Comic Vine API.
        series_start_year (int): The year the comic series began publication.
        issue_published_year (int): The year the specific issue was published.
        tbp (str): Trade Paperback (TPB) where the issue can be found.
        availability (str): Information on where the TPB is available (e.g., library, store).
        storyline (str): The storyline to which this issue belongs, used for grouping comics.
        story_order (int): The reading order of the issue within its storyline.
        status (str): Read/unread status of the comic. Defaults to "Unread".
        cover_image_url (str): URL of the issue's cover image, fetched from the Comic Vine API.

    Table:
        __tablename__ = 'comics'

    Notes:
        - The `issue_title` and `cover_image_url` fields are populated using 
          the Comic Vine API if the information is missing during CSV import.
        - The `storyline` and `story_order` fields are optional but useful for 
          grouping and sequencing comics in a reading order.
        - The `status` field allows tracking of whether the comic has been read.

    Example:
        To create a new comic record:
        new_comic = Comic(
             issue="Action Comics",
             issue_number="1",
             series_start_year=1938,
             issue_published_year=1938,
             tbp="Superman: A Celebration of 75 Years",
             availability="Library",
             storyline="Superman Origins",
             story_order=1,
             status="Unread",
             cover_image_url="http://example.com/cover.jpg"
         )
         db.session.add(new_comic)
         db.session.commit()
    """
    __tablename__ = 'comics'

    id = db.Column(db.Integer, primary_key=True)
    issue = db.Column(db.String(255), nullable=False) 
    issue_number = db.Column(db.String(50), nullable=False)
    issue_title = db.Column(db.String(255), nullable=True) 
    series_start_year = db.Column(db.Integer, nullable=False)
    issue_published_year = db.Column(db.Integer, nullable=True)
    tbp = db.Column(db.String(255), nullable=True)
    availability = db.Column(db.String(255), nullable=True)
    storyline = db.Column(db.String(255), nullable=True)
    story_order = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(255), default='Unread')
    cover_image_url = db.Column(db.String(255), nullable=True)