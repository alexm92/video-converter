#!/usr/bin/python -u 

from boto import sqs, s3
from sys import stdin, stdout
from time import time, sleep
from subprocess import call
import simplejson
import json
import os

def make_check(current_message):
    return current_message is not None

def get_file_name(file_key):
    return file_key.split('/')[-1]

def get_file_dir(file_key):
    return '/'.join(file_key.split('/')[:-1])

region_queue = sqs.connect_to_region('eu-west-1')
queue = region_queue.get_queue('video-converter-sqs')
region_s3 = s3.connect_to_region('eu-west-1')
s3 = region_s3.get_bucket('video-converter-s3')

while True:
    sleep(0.5)

    current_message = queue.read()
    if make_check(current_message):
        print('Message read')
        file_data = simplejson.loads(current_message.get_body())

        file_key = file_data['path']
        file_name = get_file_name(file_key)
        file_dir = get_file_dir(file_key)

        if not os.path.exists('{0}/{1}'.format(os.getcwd(), file_name)):
            print('Preparing to download the file')
            start_time = time()
            s3.get_key(file_key).get_contents_to_filename('{0}/{1}'.format(os.getcwd(), file_name))
            elapsed_time = time() - start_time
            print('Download complete. It took {0}'.format(elapsed_time))
            queue.delete_message(current_message)

            cmd_rez_width = file_data['width']
            cmd_red_height = file_data['height']
            cmd_gray = file_data['gray']

            if cmd_gray == 'false':
                cmd_str = '-y -i ' + file_name + ' -s ' + cmd_rez_width + 'x' + cmd_red_height + ' -vcodec h264 changed_' + file_name
            else:
                cmd_str = '-y -i ' + file_name + ' -s ' + cmd_rez_width + 'x' + cmd_red_height + ' -vf format=gray -vcodec h264 changed_' + file_name

            print('Preparing to run ffmpef {0}\n\n\n\n\n'.format(cmd_str))
            start_time = time()
            os.system('ffmpeg {0}'.format(cmd_str))
            elapsed_time = time() - start_time
            print('FFMPEG complete. It took {0}'.format(elapsed_time))

            print('Now uploading')
            start_time = time()
            upload_key = s3.new_key('{0}/changed_{1}'.format(file_dir, file_name))
            upload_key.set_contents_from_filename('changed_{0}'.format(file_name))
            upload_key.make_public()
            elapsed_time = time() - start_time
            print('Upload complete. It took {0}'.format(elapsed_time))

            os.remove('changed_{0}'.format(file_name))
            os.remove('{0}'.format(file_name))
    else:
        print('No message to read :(')