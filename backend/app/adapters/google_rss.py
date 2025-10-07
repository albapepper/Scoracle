# Transitional adapter: re-export legacy service functions
from app.services.google_rss import (
	get_entity_mentions,
	get_related_links,
	format_search_term,
	parse_rss_feed,
)  # type: ignore

__all__ = [
	'get_entity_mentions',
	'get_related_links',
	'format_search_term',
	'parse_rss_feed',
]
