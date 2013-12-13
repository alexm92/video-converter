#!/usr/bin/python -u 

from boto import sqs, s3, dynamodb2
from boto.dynamodb2.table import Table
from sys import stdin, stdout
from time import time, sleep
from subprocess import call
import simplejson
import json
import os, pexpect

def update_progress_on_download(done, total):
    value = done * 10 / total
    update_progress(global_file_key, value)

def update_progress_on_upload(done, total):
    value = done * 10 / total + 90
    update_progress(global_file_key, value)

def make_check(current_message):
    return current_message is not None

def get_file_name(file_key):
    #return file_key.split('/')[-1]
    return file_key

def get_file_dir(file_key):
    #return '/'.join(file_key.split('/')[:-1])
    return ""

def try_to_possess(file_key):
    #Creeaza o noua intrare in baza de date
    #Daca exista deja intoarce False
    try:
        db.put_item(data = {
            'initial_path' : file_key,
            'progress' : 0,
            'final_path' : '',
            'url' : ''
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

def db_delete_progress(file_key):
    #inlatura din baza de date ce am facut pana acum
    entry = db.get_item(initial_path=file_key)
    entry.delete()

def db_set_final_path(file_key, final_path):
    # seteaza link-ul catre fisierul convertit 
    # ar trebui setat dupa ce acest fisier a fost urcat in s3
    entry = db.get_item(initial_path=file_key)
    entry['final_path'] = final_path
    entry.partial_save()

def db_s3_set_url(file_key, upload_key):
    # obtine de la s3 un url pentru fisierul respectiv
    # pune acel url in baza de date la campul url
    entry = db.get_item(initial_path=file_key)
    entry['url'] = upload_key.generate_url(expires_in=0, query_auth=False)
    entry.partial_save()


def convert(command):
    thread = pexpect.spawn(command)
    #print ("started %s" % cmd)
    cpl = thread.compile_pattern_list([
        pexpect.EOF,
        'time=([^\.]+)'
    ])
    seconds = 0
    while True:
        if seconds == 0:
            try:
                i = thread.expect([pexpect.EOF, 'Duration:.+([0123456789:]{8})\.'])
                if i == 0: # EOF
                    #print ("the sub process exited")
                    break
                elif i == 1:
                    duration_text = thread.match.group(1)
                    ar_of_dur = duration_text.split(':')
                    print(ar_of_dur)
                    seconds = int(ar_of_dur[2]) + 60*int(ar_of_dur[1]) + 3600*int(ar_of_dur[0])
            except Exception,e:
                print("ceva naspa cu secundele; incerc iar")
                print(e)
        else:
            i = thread.expect_list(cpl, timeout=None)
            if i == 0: # EOF
                #print ("the sub process exited")
                break
            elif i == 1:
                time_text = thread.match.group(1)
                ar_of_dur = time_text.split(':')
                passed = int(ar_of_dur[2]) + 60*int(ar_of_dur[1]) + 3600*int(ar_of_dur[0])
                percent = passed * 80 / seconds + 10
                update_progress(file_key, percent)
    thread.close()

region_queue = sqs.connect_to_region('eu-west-1')
queue = region_queue.get_queue('video-converter-sqs')
region_s3 = s3.connect_to_region('eu-west-1')
s3 = region_s3.get_bucket('video-converter-s3')
region_db = dynamodb2.connect_to_region("eu-west-1") 
db = Table("video-converter", connection=region_db)

machine_start_time = time()
machine_no_messages = 0
last_processing_time = time()

while True:
    sleep(0.5)

    current_message = queue.read()
    if make_check(current_message):
        print('Message read')
        print(current_message.get_body())
        file_data = simplejson.loads(current_message.get_body())

        file_key = file_data['path']
        global_file_key = file_key
        file_name = get_file_name(file_key)
        file_dir = get_file_dir(file_key)
        print(file_key)
        if not os.path.exists('{0}/{1}'.format(os.getcwd(), file_name)):
            if try_to_possess(file_key):
                try:
                    print('Preparing to download the file')
                    start_time = time()
                    queue.delete_message(current_message)
                    s3.get_key(file_key).get_contents_to_filename('{0}/{1}'.format(os.getcwd(), file_name), cb = update_progress_on_download)
                    elapsed_time = time() - start_time
                    print('Download complete. It took {0}'.format(elapsed_time))
                    update_progress(file_key, 10)

                    cmd_rez_width = str(file_data['width'])
                    cmd_red_height = str(file_data['height'])
                    cmd_gray = file_data['gray']
                    print (cmd_gray)
                    if not cmd_gray:
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
                    #upload_key = s3.new_key('{0}/changed_{1}'.format(file_dir, file_name))
                    upload_key = s3.new_key('{0}'.format(file_name))
                    upload_key.set_contents_from_filename('changed_{0}'.format(file_name), cb=update_progress_on_upload)
                    upload_key.make_public()
                    elapsed_time = time() - start_time
                    print('Upload complete. It took {0}'.format(elapsed_time))
                    #db_set_final_path(file_key, '{0}/changed_{1}'.format(file_dir, file_name))
                    db_set_final_path(file_key, 'changed_{0}'.format(file_name))
                    db_s3_set_url(file_key, upload_key)
                    update_progress(file_key, 100)
                    last_processing_time = time()
                except:
                    print("S-a intamplat ceva de cacao")
                    db_delete_progress(file_key)

            else:
                print("Someone else is taking care of this")
        else:
            print("Fisierele deja exista")
        try:
            os.remove('{0}'.format(file_name))        
            os.remove('changed_{0}'.format(file_name))
        except:
            pass
    else:
        machine_duration = time() - machine_start_time
        stand_by_duration = time() - last_processing_time
        if 3300 < (machine_duration + 120) % 3600 and stand_by_duration > 600 :
            break
        print('No message to read :(')

