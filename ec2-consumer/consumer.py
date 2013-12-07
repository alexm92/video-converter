#!/usr/bin/python -u 

from boto import sqs, s3, dynamodb2
from boto.dynamodb2.table import Table
from sys import stdin, stdout
from time import time, sleep
from subprocess import call
import simplejson
import json
import os, pexpect

def make_check(current_message):
    return current_message is not None

def get_file_name(file_key):
    return file_key.split('/')[-1]

def get_file_dir(file_key):
    return '/'.join(file_key.split('/')[:-1])

def try_to_possess(file_key):
    #Creeaza o noua intrare in baza de date
    #Daca exista deja intoarce False
    try:
        db.put_item(data = {
            'initial_path' : file_key,
            'progress' : 0,
            'final_path' : ''
            })
        return True
    except:
        return False

def update_progress(file_key, new_value):
    # modifica progresul in baza de date pentru video-ul curent
    entry = db.get_item(initial_path=file_key)
    if new_value != entry['progress']:
        entry['progress'] = new_value
        print (entry['progress'])
        entry.partial_save()

def db_set_final_path(file_key, final_path):
    # seteaza link-ul catre fisierul convertit 
    # ar trebui setat dupa ce acest fisier a fost urcat in s3
    entry = db.get_item(initial_path=file_key)
    entry['final_path'] = final_path
    entry.partial_save()

def convert(command):
    thread = pexpect.spawn(command)
    #print ("started %s" % cmd)
    cpl = thread.compile_pattern_list([
        pexpect.EOF,
        'time=([^ ]+)'
    ])
    seconds = 0
    while True:
        if seconds == 0:
            i = thread.expect([pexpect.EOF, 'Duration:([^,]+)'])
            if i == 0: # EOF
                #print ("the sub process exited")
                break
            elif i == 1:
                duration_text = thread.match.group(1)[1:]
                #print(duration_text)
                ar_of_dur = duration_text.split('.')[0][-8:].split(':')
                #print(ar_of_dur)
                seconds = int(ar_of_dur[2]) + 60*int(ar_of_dur[1]) + 3600*int(ar_of_dur[0])
                #print ("0%")
        else:
            i = thread.expect_list(cpl, timeout=None)
            if i == 0: # EOF
                #print ("the sub process exited")
                break
            elif i == 1:
                time_text = thread.match.group(1)
                #print(time_text)
                ar_of_dur = time_text.split('.')[0][-8:].split(':')
                #print(ar_of_dur)
                passed = int(ar_of_dur[2]) + 60*int(ar_of_dur[1]) + 3600*int(ar_of_dur[0])
                #print ("processing {0} of {1} seconds".format(passed,seconds))
                percent = passed * 80 / seconds + 10
                #print '{0}'.format(percent)
                update_progress(file_key, percent)
    thread.close()

region_queue = sqs.connect_to_region('eu-west-1')
queue = region_queue.get_queue('video-converter-sqs')
region_s3 = s3.connect_to_region('eu-west-1')
s3 = region_s3.get_bucket('video-converter-s3')
region_db = dynamodb2.connect_to_region("eu-west-1") 
db = Table("video-converter", connection=region_db)

while True:
    sleep(0.5)

    current_message = queue.read()
    if make_check(current_message):
        print('Message read')
        print(current_message.get_body())
        file_data = simplejson.loads(current_message.get_body())

        file_key = file_data['path']
        file_name = get_file_name(file_key)
        file_dir = get_file_dir(file_key)
        print(file_key)
        if try_to_possess(file_key):
            if not os.path.exists('{0}/{1}'.format(os.getcwd(), file_name)):
                print('Preparing to download the file')
                start_time = time()
                s3.get_key(file_key).get_contents_to_filename('{0}/{1}'.format(os.getcwd(), file_name))
                elapsed_time = time() - start_time
                print('Download complete. It took {0}'.format(elapsed_time))
                update_progress(file_key, 10)
                queue.delete_message(current_message)

                cmd_rez_width = str(file_data['width'])
                cmd_red_height = str(file_data['height'])
                cmd_gray = file_data['gray']

                if cmd_gray == 'false':
                    cmd_str = '-y -i ' + file_name + ' -s ' + cmd_rez_width + 'x' + cmd_red_height + ' -vcodec h264 changed_' + file_name
                else:
                    cmd_str = '-y -i ' + file_name + ' -s ' + cmd_rez_width + 'x' + cmd_red_height + ' -vf format=gray -vcodec h264 changed_' + file_name

                #print('Preparing to run ffmpef {0}\n\n\n\n\n'.format(cmd_str))
                start_time = time()
                convert('ffmpeg {0}'.format(cmd_str))
                elapsed_time = time() - start_time
                print('FFMPEG complete. It took {0}'.format(elapsed_time))
                print('Now uploading')
                start_time = time()
                upload_key = s3.new_key('{0}/changed_{1}'.format(file_dir, file_name))
                upload_key.set_contents_from_filename('changed_{0}'.format(file_name))
                upload_key.make_public()
                elapsed_time = time() - start_time
                print('Upload complete. It took {0}'.format(elapsed_time))
                update_progress(file_key, 100)
                db_set_final_path(file_key, '{0}/changed_{1}'.format(file_dir, file_name))
                
                os.remove('changed_{0}'.format(file_name))
                os.remove('{0}'.format(file_name))
    else:
        print('No message to read :(')
