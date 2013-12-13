from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import time, os, json, base64, urllib, hmac, sha, hashlib
import ec2_consumer.video_converter_api as api

def sign(key, msg):
  return hmac.new(key, msg.encode('utf-8'), sha).digest()

def blankIE9(request):
    return HttpResponse()

def home(request):
    return_dict = {}
    t = loader.get_template('index.html')
    c = RequestContext(request, return_dict)
    return HttpResponse(t.render(c))

@csrf_exempt
def upload(request):
    return_dict = {}
    AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY_ID
    AWS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
    S3_BUCKET = settings.AWS_STORAGE_BUCKET_NAME

    if request.GET:
        object_name = 'videos/%s-%s' % (request.GET.get('s3_object_name'), time.time())
        mime_type = request.GET.get('s3_object_type')

        expires = int(time.time() + 60)
        amz_headers = "x-amz-acl:public-read"

        put_request = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, S3_BUCKET, object_name)

        signature = base64.encodestring(hmac.new(AWS_SECRET_KEY,put_request, sha).digest())
        signature = urllib.quote_plus(signature.strip())

        url = 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, object_name)

        return_dict['signed_request'] = '%s?AWSAccessKeyId=%s&Expires=%d&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature)
        return_dict['url'] = url
    
    if request.method == 'POST':
        policy = base64.b64encode(request.body)
        signature = sign(AWS_SECRET_KEY, policy)
        return_dict['policy'] = policy
        return_dict['signature'] = base64.b64encode(signature)
        print return_dict
    
    return HttpResponse(json.dumps(return_dict), content_type="application/json")

     
        

## Init convert
def convert(request):
    return_dict = {}
    if request.GET:
        path = '/'.join(request.GET.get('path', '').split('/')[-2 : ])
        width = int(request.GET.get('width', '0'))
        height = int(request.GET.get('height', '0'))
        gray = request.GET.get('gray', 'false') == 'true'

        # SQS push
        api.push_to_queue(path, width, height, gray)
        return_dict['success'] = True
    return HttpResponse(json.dumps(return_dict), content_type="application/json")

## Returns for an S3 path the convertion percent
def progress(request):
    return_dict = {'progress': 0}
    if request.GET:
        path = '/'.join(request.GET.get('path', '').split('/')[-2 : ])

        return_dict['progress'] = api.check_progress(path)
    return HttpResponse(json.dumps(return_dict), content_type="application/json")

## Returns for an S3 path the URL of the converted video
def get_url(request):
    return_dict = {'url' : ''}
    if request.GET:
        path = '/'.join(request.GET.get('path', '').split('/')[-2 : ])
        return_dict['url'] = api.get_url(path)
    return HttpResponse(json.dumps(return_dict), content_type="application/json")
