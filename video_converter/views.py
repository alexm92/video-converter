from django.http import HttpResponse
from django.template import RequestContext, loader
from django.conf import settings
import time, os, json, base64, urllib, hmac, sha

def home(request):
    return_dict = {}
    t = loader.get_template('index.html')
    c = RequestContext(request, return_dict)
    return HttpResponse(t.render(c))

def upload(request):
    return_dict = {}

    if request.GET:
        AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY_ID
        AWS_SECRET_KEY = settings.AWS_SECRET_ACCESS_KEY
        S3_BUCKET = settings.AWS_STORAGE_BUCKET_NAME

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

    return HttpResponse(json.dumps(return_dict), content_type="application/json")

