#import exifread
#from kthread import KThread
#import time
import piexif
import pymongo
from datetime import datetime
import os
import os.path

db_collection = None
thread_amount = None
time_penalty = None

'''
Contains functions for extracting and writing exif metadata from images to mongo and from database to images
'''

def get_exif_from_image(image_filename):
    with open(image_filename, 'rb') as image_file:
        tags = exifread.process_file(image_file)
    tags_keys = list(tags.keys()).copy()
    for k in tags_keys:
        if type(tags[k]) == bytes:
            tags.pop(k)
        else:
            tags[k] = str(tags[k])
    tags['filename'] = image_filename
    return tags
    
def process_image_to_db(filename):
    t = get_exif_from_image(filename)
    db_collection.insert_one(t)
    print('processed', filename)

def process_exifs_to_db(*directories, mongodb_uri='mongodb://localhost:27017/', threads=8, tp=3):
    global db_collection, thread_amount, time_penalty
    thread_amount = threads
    time_penalty = tp
    mc = pymongo.MongoClient(mongodb_uri)
    db = mc.exif
    dt = datetime.now().strftime("ts%d.%m.%Y_%H.%M")
    db_collection = db[dt]
    for d in directories:
        extract_directory(d)

def choose_collection(dbname, colname):
    mc = pymongo.MongoClient()
    global db_collection
    db_collection = mc[dbname][colname]

def extract_directory(d):
    print('processing directory', d)
    images = list(filter(lambda s: s.lower().endswith('.jpg'), os.listdir(d)))
    thread_list = [('', None, 0)]*thread_amount
    while True:
        for ti in range(thread_amount):
            if len(images) == 0: return
            t = thread_list[ti]
            t_image, t_thread, t_time = t
            cur_ti2me = time.time()
            if t_image and t_thread.isAlive():
                if (cur_time - t_time) < time_penalty: continue
                t_thread.terminate()
                print('killling thread for', t_image)
                images.append(t_image)
            cur_image = os.path.join(d, images[0])
            cur_thread = KThread(target = process_image_to_db, args=(cur_image,))
            thread_list[ti] = (cur_image, cur_thread, cur_time)
            images.pop(0)
            cur_thread.start()
            
def write_data_to_img(d):
    fn = d['filename']
    exif_bytes = piexif.dump(d)
    piexif.insert(exif_bytes, fn)

def insert_data():
    tdm = data_threading.ThreadedDataManager()
    tdm.setDataProcess(write_data_to_img)
    tdm.setTimeout(5)
    tdm.setOnSuccess(lambda d: print("inserted", d['filename']))
    for d in db_collection.find(): tdm.append(d)
    tdm.start()
