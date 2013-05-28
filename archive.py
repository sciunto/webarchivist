#!/usr/bin/env python
# -*- coding: utf-8 -*-
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>

""" Functions dealing with the archive"""

import os
import datetime
import logging
logger = logging.getLogger('zimarchivist.archive')


#HTTP
import urllib.parse as urlparse
from urllib.request import urlopen, urlretrieve
import urllib.error
import socket # for exceptions
import http.client
import mimetypes
from bs4 import BeautifulSoup as bs


import subprocess

class URLError(Exception):
    def __init__(self):
        Exception.__init__(self)



import threading
import uuid
from queue import Queue

class ThreadImg(threading.Thread):
    """
    Download img with threads
    """
    def __init__(self, lock, uuid, imgs, parsed, htmlpath):
        """
        Constructor

        """
        threading.Thread.__init__(self)
        self.lock = lock
        self.queue = imgs
        self.uuid = uuid
        self.parsed = parsed
        self.htmlpath = htmlpath

    def run(self):
        """
        One job...

        """
        #TODO deals with URLError
        #TODO deals with IOError (connection down?)
        while True:
            img = self.queue.get()

            number = uuid.uuid4()
            try:
                original_filename = img["src"].split("/")[-1].split('?')[0]
            except KeyError:
                print('KeyError img["src"]. Ignoring...')
                continue
            new_filename = str(number) + str(os.path.splitext(original_filename)[1])

            print('thread: ' + '--> ' + original_filename + '--' + str(number))
            #Directory for pictures
            pic_dir = os.path.join(self.htmlpath, str(self.uuid))
            self.lock.acquire()
            if not os.path.exists(pic_dir):
                os.mkdir(pic_dir)
            self.lock.release()
            outpath = os.path.join(pic_dir, new_filename)

            try:
                #if src start with http...
                if img["src"].lower().startswith("http"):
                    urlretrieve(img["src"], outpath) #too simple, just fetch it!
                else:
                        #We add the relative path
                        #ex: http://toto.org/dir/page.html which contains 'picture.png'
                        #-> the path is dir/picture.png
                        import copy
                        current_parsed = copy.copy(self.parsed)
                        current_parsed[2] = os.path.join(os.path.split(self.parsed[2])[0], img["src"])
                        urlretrieve(urlparse.urlunparse(current_parsed), outpath)
            except ValueError as e:
                #Normally OK, but...
                #Some links can raise ValueError
                print('ValueError Fetchlink ' + str(e))
            except IOError as e:
                print('IOError Fetchlink ' + str(e))
                #print(current_parsed)
            #img["src"] = os.path.relpath(outpath, self.htmlpath) # rel path
            #img["src"] = os.path.relpath(new_filename, self.htmlpath) # rel path
            img["src"] = new_filename
            #end...
            self.queue.task_done()


def make_archive_thread(file_dir, uuid, url):
    """
    Download the url in file_dir
    and everything is tagged with uuid.
    If url is text/html, pictures are saved in a subdir
    Otherwise, the bin file is saved.

    file_dir : directory where the archive is written
    uuid : Archive ID
    url : URL to archive

    raise URLError if url is invalid or not accessible

    return : extension of the main file
    """
    logger.debug('get ' + url)

    mimetype, encoding = mimetypes.guess_type(url)
    logger.debug('mimetype: ' + str(mimetype) )

    timeout = 15

    if mimetype is None:
        #Try to guess with urrllib if mimetype failed
        try:
            fp = urlopen(url, timeout=timeout)
        except urllib.error.HTTPError:
            print('could not open ' + str(url))
            # raise an error to do not add internal link in zim notes
            raise URLError
        except urllib.error.URLError:
            print('could not open ' + str(url))
            # raise an error to do not add internal link in zim notes
            raise URLError
        except socket.timeout:
            print('Time Out')
            raise URLError

        a = fp.info()
        mimetype = a.get_content_type()
        logger.debug('mimetype guess with urllib: ' + str(mimetype) )

    if mimetype == 'text/html' or mimetype is None:
        logger.debug('Download as text/html')
        file_extension = '.html'
        #Open the url
        try:
            soup = bs(urlopen(url, timeout=timeout))
        except urllib.error.HTTPError:
            print('could not open ' + str(url))
            # raise an error to do not add internal link in zim notes
            raise URLError
        except urllib.error.URLError:
            print('could not open ' + str(url))
            # raise an error to do not add internal link in zim notes
            raise URLError
        except socket.timeout:
            print('Time Out')
            raise URLError
        #Parsed url
        parsed = list(urlparse.urlparse(url))

        img_queue = Queue()
        number_of_threads = 4
        lock = threading.Lock()

        #Set up threads
        for thread in range(number_of_threads):
            worker = ThreadImg(lock, uuid, img_queue, parsed, file_dir)
            worker.setDaemon(True)
            worker.start()

        #Download images
        for img in soup.findAll("img"):
            img_queue.put(img)

        #wait all the threads...
        print('waiting')
        img_queue.join()
        print('done')
        html_file = os.path.join(file_dir, str(uuid) + file_extension)
        with open(html_file, 'w') as htmlfile:
            htmlfile.write(soup.prettify())
        file_title = soup.title.string
    else:
        logger.debug('Download as a bin file')
        file_extension  = mimetypes.guess_extension(mimetype)
        outpath = os.path.join(file_dir, str(uuid) + str(file_extension) )
        try:
            urlretrieve(url, outpath) #too simple, just fetch it!
        except ValueError as e:
            #Normally OK, but...
            #Some links can raise ValueError
            print('ValueError Fetchlink ' + str(e))
        except:
            print('Exception ')
        file_title = '' # TODO
    return (file_extension, file_title)


def archive_to_markdown(dest_dir, name, url):
    """
    Download the url in dest_dir
    and everything is tagged with name.
    If url is text/html,
     * pictures are saved in a subdir
     * html is converted to mdwn
    Otherwise, the bin file is saved.

    dest_dir : directory where the archive is written
    name : Archive ID
    url : URL to archive

    return : title

    raise URLError if url is invalid or not accessible
    """
    (extension, title) = make_archive_thread(dest_dir, name, url)

    if extension == '.html':
        htmlfile = os.path.join(dest_dir, str(name) + extension)
        command = ['pandoc', '-f', 'html', '-t', 'markdown', htmlfile]
        process = subprocess.Popen(command, bufsize=4096, stdout=subprocess.PIPE)
        stdout, stderr = process.communicate()
        markdown_file = os.path.join(dest_dir, str(name) + '.mdwn')
        with open(markdown_file, 'w') as out:
            # Write header
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            out.write('* Source: <' + url + '>\n')
            out.write('* Date: ' + date + '\n')
            out.write('---------------------------------------\n\n')
            # Write data
            out.write(stdout.decode('utf-8'))

    else:
        print('not html')

    return title

if __name__ == '__main__':
    pass
