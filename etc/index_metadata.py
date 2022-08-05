#!/usr/bin python3
"""
A hacky script to index EC2 metadata of an EC2 Instance into a format that is expected by
the mock metadata server included in this package
"""

import json
from urllib.request import urlopen
from urllib.error import HTTPError

METADATA_PREFIX = "http://169.254.169.254/"


def get_metadata(suffixes=[]):
	url = METADATA_PREFIX + "/".join([suffix.replace("/", "") for suffix in suffixes])
	try:
		return urlopen(url).read().rstrip("\n")
	except HTTPError as e:
		if e.code == 404 or e.code == 400:
			return None
		raise e


def is_json(data):
	try:
		json.loads(data)
		return True
	except ValueError:
		return False


def should_stop(page):
	# could probably test if the page is a key/signature of some sort
	# but this is just easier (although more brittle)
	return page.replace("/", "") in ['pkcs7', 'rsa2048', 'signature']


def recurse(page, prefixes=[]):
	# This could certainly be optimized
	metadata = get_metadata(prefixes + [page])
	if metadata is None or page == metadata:
		return None
	if is_json(metadata) or should_stop(page):
		return {page: metadata}
	data = {}
	sub_pages = metadata.split("\n")
	for sub_page in sub_pages:
		sub_data = recurse(sub_page, prefixes + [page])
		if sub_data is None:
			if len(data) == 0 and len(sub_pages) == 1:
				return {page: sub_page}
			else:
				data.update({sub_page: None})
				continue
		data.update(sub_data)
	return {page: data}


if __name__ == "__main__":
	print(json.dumps(recurse("latest"), indent=2))
