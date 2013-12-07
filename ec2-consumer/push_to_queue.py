from boto import sqs, s3
from sys import stdin
import json, uuid
from boto.sqs.jsonmessage import JSONMessage
from boto.sqs.message import RawMessage

queue = sqs.connect_to_region("eu-west-1")
q = queue.get_queue('video-converter-sqs')

'''
Asa trebuie puse mesajele in coada
Acesta este un exemplu
'''

vals = {
	'path' : 'videos/test2.mkv',
	'width' : 432,
	'height' : 320,
	'gray' : False
}

m = JSONMessage()
m.set_body(vals)
q.write(m)