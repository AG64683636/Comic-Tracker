from models import Comic
from collections import defaultdict

def get_comics_by_sorting(sort_option):
    """
    Retrieve comics sorted or grouped based on the provided sorting option.

    Args:
        sort_option (str): The sorting option to apply. Supported values:
            - 'id': Sort comics by their ID in ascending order.
            - Any other value (default): Group comics by storyline and sort by 
              story order, then by ID within each group.

    Returns:
        dict: A dictionary where the keys are storyline names (or 'All Comics' 
              for 'id' sorting) and the values are lists of `Comic` objects.

    Example:
        >>> get_comics_by_sorting('id')
        {'All Comics': [Comic(id=1, ...), Comic(id=2, ...)]}

        >>> get_comics_by_sorting('storyline')
        {
            'Storyline A': [Comic(id=1, ...), Comic(id=3, ...)],
            'Storyline B': [Comic(id=2, ...)]
        }

    Raises:
        None: This function does not raise exceptions but assumes the database 
        and the `Comic` model are properly configured.
    """
    if sort_option == 'id':
        comics = Comic.query.order_by(Comic.id).all()
        return {'All Comics': comics}
    else:
        comics = Comic.query.order_by(Comic.storyline, Comic.story_order, Comic.id).all()
        comics_by_storyline = defaultdict(list)
        storyline_order = {}
        for comic in comics:
            comics_by_storyline[comic.storyline].append(comic)
            if comic.storyline not in storyline_order or comic.id < storyline_order[comic.storyline]:
                storyline_order[comic.storyline] = comic.id
        return dict(sorted(comics_by_storyline.items(), key=lambda x: storyline_order[x[0]]))