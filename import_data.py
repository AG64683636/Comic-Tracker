"""
    Import comics from a CSV file into the database, updating or adding records as necessary.

    This function reads a CSV file containing comic data and performs the following:
        - Updates existing database records when the CSV data differs.
        - Adds new records for comics not already in the database.
        - Fetches missing details (e.g., issue title and cover image URL) from the Comic Vine API.

    The CSV file must include the following fields:

        - 'Issue': Name of the comic series (required).
        - 'Issue Number': Issue number within the series (required).
        - 'Series Start Year': Year the series started (required).

        These are required as they are used to find the correct issue in the Comic Vine API. Series start year helps find the correct volume of the issue requested.
        
        - Optional fields:
            - 'Issue Published Year'
            - 'TBP' (Trade Paperback) - Which TBPs can the issue be found in?
            - 'Availability' - Where are the TBPs available?
            - 'Storyline' - Optional, but will group series of the same storyline together. 
            - 'Story Order' - Reading order of given storyline.
            - 'Status' - Read or Unread

    Args:
        filepath (str): Path to the CSV file containing comic data.

    Returns:
        None

    Side Effects:
        - Prints updates for modified and newly added records.
        - Modifies the database by adding or updating comic records.
        - May make external API calls to fetch additional details for comics.

    Raises:
        - Exception: If the file format is invalid or another unexpected error occurs.

    Examples:
        >>> import_comics('comics.csv')
        Comics successfully imported.
"""

import csv
from database import db
from models import Comic
from api_client import get_comic_issue_details  # Your Comic Vine API logic
import logging

logger = logging.getLogger(__name__)


def import_comics(filepath):
    """
    Import comics from a CSV file into the database, updating or adding records as necessary.

    See docstring in the earlier analysis for detailed documentation.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            if not _validate_row(row):
                logger.warning(f"Skipping invalid row: {row}")
                continue

            existing_comic = _get_existing_comic(row)
            if existing_comic:
                _update_comic(existing_comic, row)
            else:
                _add_new_comic(row)

        # Commit all changes at once
        db.session.commit()
        logger.info("Comics successfully imported.")


def _validate_row(row):
    """
    Validate that a row contains the required fields.

    Args:
        row (dict): A dictionary representing a row from the CSV file.

    Returns:
        bool: True if the row is valid, False otherwise.
    """
    return all(row.get(field) for field in ['Issue', 'Issue Number', 'Series Start Year'])


def _get_existing_comic(row):
    """
    Retrieve an existing comic from the database based on CSV row data.

    Args:
        row (dict): A dictionary representing a row from the CSV file.

    Returns:
        Comic: The existing comic instance or None if not found.
    """
    return Comic.query.filter_by(
        issue=row['Issue'],
        issue_number=row['Issue Number'],
        series_start_year=int(row['Series Start Year'])
    ).first()


def _update_comic(comic, row):
    """
    Update an existing comic record with data from the CSV row.

    Args:
        comic (Comic): The comic instance to update.
        row (dict): A dictionary representing a row from the CSV file.
    """
    updated_fields = {}

    # Compare and update fields
    for field, db_field in [
        ('Issue Published Year', 'issue_published_year'),
        ('TBP', 'tbp'),
        ('Availability', 'availability'),
        ('Storyline', 'storyline'),
        ('Story Order', 'story_order'),
        ('Status', 'status'),
    ]:
        new_value = row.get(field)
        if new_value and getattr(comic, db_field) != new_value:
            setattr(comic, db_field, int(new_value) if db_field == 'issue_published_year' else new_value)
            updated_fields[db_field] = new_value

    # Fetch additional details if necessary
    _fetch_and_update_api_details(comic, row, updated_fields)

    if updated_fields:
        logger.info(f"Updated comic {comic.issue} #{comic.issue_number}: {updated_fields}")


def _add_new_comic(row):
    """
    Add a new comic record to the database based on CSV row data.

    Args:
        row (dict): A dictionary representing a row from the CSV file.
    """
    issue_details = get_comic_issue_details(
        series_name=row['Issue'],
        start_year=int(row['Series Start Year']),
        issue_number=row['Issue Number']
    )

    comic = Comic(
        issue=row['Issue'],
        issue_number=row['Issue Number'],
        issue_title=issue_details.get('name') if issue_details else None,
        series_start_year=int(row['Series Start Year']),
        issue_published_year=int(row.get('Issue Published Year') or 0),
        tbp=row.get('TBP'),
        availability=row.get('Availability'),
        storyline=row.get('Storyline'),
        story_order=int(row.get('Story Order') or 0),
        status=row.get('Status', 'Unread'),
        cover_image_url=issue_details.get('image_url') if issue_details else None
    )
    db.session.add(comic)
    logger.info(f"Added new comic: {comic.issue} #{comic.issue_number}")


def _fetch_and_update_api_details(comic, row, updated_fields):
    """
    Fetch missing details from the Comic Vine API and update the comic instance.

    Args:
        comic (Comic): The comic instance to update.
        row (dict): A dictionary representing a row from the CSV file.
        updated_fields (dict): Dictionary to track updated fields.
    """
    if not comic.cover_image_url or not comic.issue_title:
        issue_details = get_comic_issue_details(
            series_name=row['Issue'],
            start_year=int(row['Series Start Year']),
            issue_number=row['Issue Number']
        )
        if issue_details:
            if not comic.cover_image_url:
                comic.cover_image_url = issue_details.get('image_url')
                updated_fields['cover_image_url'] = issue_details.get('image_url')
            if not comic.issue_title:
                comic.issue_title = issue_details.get('name')
                updated_fields['issue_title'] = issue_details.get('name')
