from boto import sqs, s3, dynamodb2
from boto.dynamodb2.table import Table
from sys import stdin
import json
from boto.sqs.jsonmessage import JSONMessage
from boto.sqs.message import RawMessage

'''
usage:
from video_converter_api import check_progress, get_url, push_to_queue
dependency: boto (pip install boto)
'''

def push_to_queue(path, width, height, gray):
	'''
	Pune mesajele in coada.
	path = path-ul din s3. ar fi bine sa fie unic
	ex: 'videos/21242312/jumbix.mp4'
	width: latimea
	height: inaltimea
	gray: True sau False, semnifica daca se vrea convertirea la B/W
	'''
	queue = sqs.connect_to_region("eu-west-1")
	q = queue.get_queue('video-converter-sqs')

	vals = {
		'path' : path,
		'width' : width,
		'height' : height,
		'gray' : gray
	}

	m = JSONMessage()
	m.set_body(vals)
	q.write(m)

def check_progress(path):
	'''
	Intoarce progresul unui anume video
	path: path-ul fisierului initial din s3
	ex: 'videos/21242312/jumbix.mp4'
	'''
	region_db = dynamodb2.connect_to_region("eu-west-1") 
	db = Table("video-converter", connection=region_db)

	entry = db.get_item(initial_path=path)

	try:
		if entry['progress'] is not None:
			return entry['progress']
		else:
			return 0
	except:
		return 0

def get_url(path):
	'''
	Intoarce url-ul unui anume video
	Are sens doar daca check_progress este 100
	Altfel va intoarce None
	path: path-ul fisierului initial din s3
	ex: 'videos/21242312/jumbix.mp4'
	'''
	if check_progress(path) < 100:
		return None
	else:
		region_db = dynamodb2.connect_to_region("eu-west-1") 
		db = Table("video-converter", connection=region_db)
		entry = db.get_item(initial_path=path)
		return entry['url']

