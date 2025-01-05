import urllib.parse
import urllib.request
import urllib.error
import json
import os
from dotenv import load_dotenv
import time

api_rate_limit_reached = False

# Load the API key
load_dotenv()
COMIC_VINE_API_KEY = os.getenv("COMIC_VINE_API_KEY")
COMIC_VINE_BASE_URL = "https://comicvine.gamespot.com/api"

def make_api_call(url, params):
    """
    Make an API call using urllib.

    Args:
        url (str): The base URL for the API call.
        params (dict): The parameters for the API call.

    Returns:
        dict: The JSON response from the API or None if an error occurs.
    """
    global api_rate_limit_reached

    if api_rate_limit_reached:
        print("API rate limit reached. Skipping further API calls.")
        return None

    # Encode parameters into the URL
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"

    # Print the final API request URL
    print(f"API Request URL: {full_url}")

    try:
        with urllib.request.urlopen(full_url) as response:
            if response.status != 200:
                print(f"Error: HTTP Status {response.status}")
                return None
            data = response.read()
            return json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 420:  # Handle rate-limiting error
            print("Comic Vine API hourly limit reached. Stopping further API calls.")
            api_rate_limit_reached = True  # Set the flag to stop future calls
        else:
            print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

def get_comic_issue_details(series_name, start_year, issue_number):
    """
    Retrieve details about a specific comic issue using the Comic Vine API.

    Args:
        series_name (str): The name of the comic series.
        start_year (int): The year the series started.
        issue_number (str): The issue number to find.

    Returns:
        dict: Details about the specific comic issue or None if not found.
    """
    # Step 1: Search for the series with pagination
    series_search_url = f"{COMIC_VINE_BASE_URL}/search/"
    offset = 0
    limit = 100
    series_id = None

    while True:
        params = {
            'api_key': COMIC_VINE_API_KEY,
            'format': 'json',
            'query': series_name,
            'resources': 'volume',
            'offset': offset,
            'limit': limit
        }
        series_data = make_api_call(series_search_url, params)
        if not series_data:
            return None

        # Find the series by start year in the current page of results
        for series in series_data.get('results', []):
            if series.get('start_year') == str(start_year):
                series_id = series['id']
                break

        # If the series is found or no more results are available, break
        if series_id or len(series_data.get('results', [])) < limit:
            break

        offset += limit

    if not series_id:
        print(f"No series found for '{series_name}' starting in {start_year}.")
        return None

    # Step 2: Get issues for the series with pagination
    issues_url = f"{COMIC_VINE_BASE_URL}/issues/"
    offset = 0
    issue_id = None

    while True:
        params = {
            'api_key': COMIC_VINE_API_KEY,
            'format': 'json',
            'filter': f'volume:{series_id}',
            'offset': offset,
            'limit': limit
        }
        issues_data = make_api_call(issues_url, params)
        if not issues_data:
            return None

        # Find the issue by issue number in the current page of results
        for issue in issues_data.get('results', []):
            if issue.get('issue_number') == str(issue_number):
                issue_id = issue['id']
                break

        # If the issue is found or no more results are available, break
        if issue_id or len(issues_data.get('results', [])) < limit:
            break

        offset += limit

    if not issue_id:
        print(f"Issue #{issue_number} not found in series '{series_name}' ({start_year}).")
        return None

    # Step 3: Get details for the specific issue
    issue_url = f"{COMIC_VINE_BASE_URL}/issue/4000-{issue_id}/"
    params = {
        'api_key': COMIC_VINE_API_KEY,
        'format': 'json'
    }
    issue_details = make_api_call(issue_url, params)

    if not issue_details:
        return None

    # Extract issue image
    issue_result = issue_details.get('results', {})
    image_url = issue_result.get('image', {}).get('original_url', None)
    issue_result['image_url'] = image_url

    return issue_result




'''
# Example usage
series_name = "Superman's Pal, Jimmy Olsen #141"
start_year = 1954
issue_number = '133'

issue_details = get_comic_issue_details(series_name, start_year, issue_number)


if issue_details:
    print(f"Issue Title: {issue_details.get('name')}")
    print(f"Issue Description: {issue_details.get('description')}")
    print(f"Issue Image URL: {issue_details.get('image_url')}")
'''