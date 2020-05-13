#
# A simple Evernote API demo script that lists all notebooks in the user's
# account and creates a simple test note in the default notebook.
#
# Before running this sample, you must fill in your Evernote developer token.
#
# To run (Unix):
#   export PYTHONPATH=../../lib; python EDAMTest.py
#
# -*- coding: utf-8 -*-
import hashlib
import binascii
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types

from evernote.api.client import EvernoteClient
import evernote.edam.error.ttypes as Errors

import requests
from requests.exceptions import HTTPError
from PIL import Image
from io import BytesIO
import urllib2, cStringIO
from urllib2 import urlopen
import base64
import random
import time
from datetime import datetime





# Real applications authenticate with Evernote using OAuth, but for the
# purpose of exploring the API, you can get a developer token that allows
# you to access your own Evernote account. To get a developer token, visit
# https://SERVICE_HOST/api/DeveloperToken.action
#
# There are three Evernote services:
#
# Sandbox: https://sandbox.evernote.com/
# Production (International): https://www.evernote.com/
# Production (China): https://app.yinxiang.com/
#
# For more information about Sandbox and Evernote China services, please 
# refer to https://dev.evernote.com/doc/articles/testing.php 
# and https://dev.evernote.com/doc/articles/bootstrap.php

auth_token = "your developer token"

if auth_token == "your developer token":
    print "Please fill in your developer token"
    print "To get a developer token, visit " \
        "https://sandbox.evernote.com/api/DeveloperToken.action"
    exit(1)


# To access Sandbox service, set sandbox to True 
# To access production (International) service, set both sandbox and china to False
# To access production (China) service, set sandbox to False and china to True
sandbox = True
china = False

# Initial development is performed on our sandbox server. To use the production
# service, change sandbox=False and replace your
# developer token above with a token from
# https://www.evernote.com/api/DeveloperToken.action
client = EvernoteClient(token=auth_token, sandbox=sandbox, china=china)

user_store = client.get_user_store()

version_ok = user_store.checkVersion(
    "Evernote reddit_saves_parser: converts list of reddit links to evernote notes (Python)",
    UserStoreConstants.EDAM_VERSION_MAJOR,
    UserStoreConstants.EDAM_VERSION_MINOR
)
print "Is my Evernote API version up to date? ", str(version_ok)
print ""
if not version_ok:
    exit(1)

note_store = client.get_note_store()

print
print "Creating a new note"
print

errors=[]            
posts=[]
comments=[]
with open("ALL REDDIT SAVES.txt", "r") as f6:
    fileList2 = list(f6.readlines())
    print len(fileList2)

    for idx,link3 in enumerate(fileList2):
        if "reddit" in link3 and len(link3.split('/'))==9:
            posts.append(link3)
        elif "reddit" in link3 and len(link3.split('/'))==10:
            if len(posts)>0 and idx>0 and (len(comments)==0 or (not (link3.split('/')[:7] == comments[-1].split('/')[:7])) ) :
                posts.pop()
            comments.append(link3)
    print len(posts)
    print len(comments)

for p,t in enumerate(posts):
    try:
        req = requests.get('https://api.reddit.com/api/info/?id=t3_'+posts[p].split('/')[6], headers = {'User-agent': 'redditEvernoteBot'})

        # If the response was successful, no Exception will be raised
        req.raise_for_status()
    except HTTPError as http_err:
        print(http_err)  # Python 3.6
        errors.append(posts[p])
    except Exception as err:
        print(err)  # Python 3.6
        errors.append(posts[p])
    else:
        print(str(p)+'/'+str(len(posts))+' Success! '+posts[p])
        reqData=req.json()
        note = Types.Note()
        try:
            note.tagNames=[reqData['data']['children'][0]['data']['subreddit'], 'reddit', 'reddit_saves_bot']
        except:
            print 'non standard format, skipping'
            errors.append(posts[p])
            continue
        selftext=reqData['data']['children'][0]['data']['selftext'] or None
        cUrl=reqData['data']['children'][0]['data']['url']
        contentUrl=cUrl if ("reddit" not in cUrl) else None
        thumbnailUrl=reqData['data']['children'][0]['data']['thumbnail'] or None
        postUrl='https://reddit.com'+reqData['data']['children'][0]['data']['permalink']
        postDate=datetime.utcfromtimestamp(reqData['data']['children'][0]['data']['created_utc']).strftime('%Y-%m-%d')
        postTitle=(reqData['data']['children'][0]['data']['title'])
        note.title= u' '.join([postDate, postTitle[:100]]).encode('ascii', 'ignore').decode('ascii').replace('\n', "").strip()

        image=None
        # Thumbnail can be image url or 'self', 'spoiler', 'default', etc
        if (thumbnailUrl is not None) and (thumbnailUrl[:4] == 'http'):
            try:
                image = urllib2.urlopen(thumbnailUrl).read()
            except:
                image=None

        if image is not None:
            md5 = hashlib.md5()
            md5.update(image)
            hash = md5.digest()

            data = Types.Data()
            data.size = len(image)
            data.bodyHash = hash
            data.body = image

            resource = Types.Resource()
            resource.mime = 'image/png'
            resource.data = data

            # Now, add the new Resource to the note's list of resources
            note.resources = [resource]

            # To display the Resource as part of the note's content, include an <en-media>
            # tag in the note's ENML content. The en-media tag identifies the corresponding
            # Resource using the MD5 hash.
            hash_hex = binascii.hexlify(hash)

        # The content of an Evernote note is represented using Evernote Markup Language
        # (ENML). The full ENML specification can be found in the Evernote API Overview
        # at http://dev.evernote.com/documentation/cloud/chapters/ENML.php
        note.content = '<?xml version="1.0" encoding="UTF-8"?>'
        note.content += '<!DOCTYPE en-note SYSTEM ' \
            '"http://xml.evernote.com/pub/enml2.dtd">'
        note.content += '<en-note><br/>'
        if selftext is not None:
            note.content += '<h5>'+selftext+'</h5><br/>'
        if contentUrl is not None:
            note.content += '<a href="'+contentUrl+'">'+contentUrl+'</a><br/>'
        note.content += '<a href="'+postUrl+'">'+postUrl+'</a><br/>'
        if image is not None: 
            note.content += '<en-media width="300" height="225" type="image/png" hash="' + hash_hex + '"/>'
        note.content += '</en-note>'

        # Finally, send the new note to Evernote using the createNote method
        # The new Note object that is returned will contain server-generated
        # attributes such as the new note's unique GUID.
        try:
            created_note = note_store.createNote(note)
        except Errors.EDAMSystemException, e:
            if e.errorCode == Errors.EDAMErrorCode.RATE_LIMIT_REACHED:
                print "Rate limit reached"
                print "Retry your request in %d seconds" % e.rateLimitDuration
                time.sleep(e.rateLimitDuration+1)
                try:
                    created_note = note_store.createNote(note)
                except:
                    print 'failed'
                    errors.append(posts[p])
                    continue
                    
                

    
    # wait a random amnt of time
    time.sleep(random.randint(1,3))

print 'Done! Errors: '+str(len(errors))+ ' '+str(errors) 

commentGroup = []
for p,t in enumerate(comments):
    print(t)
    commentGroup.append(t)
    if not p==(len(comments)-1) and comments[p].split('/')[:7] == comments[p+1].split('/')[:7]:
        continue
    else:
        try:
            req = requests.get('https://api.reddit.com/api/info/?id=t3_'+t.split('/')[6], headers = {'User-agent': 'redditEvernoteBot'})

            # If the response was successful, no Exception will be raised
            req.raise_for_status()
        except HTTPError as http_err:
            print(http_err)  # Python 3.6
        except Exception as err:
            print(err)  # Python 3.6
        else:
            print(str(p)+'/'+str(len(comments))+' Success! '+comments[p])
            reqData=req.json()
            note = Types.Note()
            try:
                note.tagNames=[reqData['data']['children'][0]['data']['subreddit'], 'reddit', 'reddit_saves_bot', 'reddit_comment']
            except:
                print 'non standard format, skipping'
                errors.append(posts[p])
                continue
            selftext=reqData['data']['children'][0]['data']['selftext'] or None
            cUrl=reqData['data']['children'][0]['data']['url']
            contentUrl=cUrl if ("reddit" not in cUrl) else None
            thumbnailUrl=reqData['data']['children'][0]['data']['thumbnail'] or None
            postUrl='https://reddit.com'+reqData['data']['children'][0]['data']['permalink']
            postDate=datetime.utcfromtimestamp(reqData['data']['children'][0]['data']['created_utc']).strftime('%Y-%m-%d')
            postTitle=(reqData['data']['children'][0]['data']['title'])
            note.title= u' '.join([postDate, postTitle[:100]]).encode('ascii', 'ignore').decode('ascii').replace('\n', "").strip()

            image=None
            # Thumbnail can be image url or 'self', 'spoiler', 'default', etc
            if (thumbnailUrl is not None) and (thumbnailUrl[:4] == 'http'):
                try:
                    image = urllib2.urlopen(thumbnailUrl).read()
                except:
                    image=None

            if image is not None:
                md5 = hashlib.md5()
                md5.update(image)
                hash = md5.digest()

                data = Types.Data()
                data.size = len(image)
                data.bodyHash = hash
                data.body = image

                resource = Types.Resource()
                resource.mime = 'image/png'
                resource.data = data

                # Now, add the new Resource to the note's list of resources
                note.resources = [resource]

                # To display the Resource as part of the note's content, include an <en-media>
                # tag in the note's ENML content. The en-media tag identifies the corresponding
                # Resource using the MD5 hash.
                hash_hex = binascii.hexlify(hash)

            # The content of an Evernote note is represented using Evernote Markup Language
            # (ENML). The full ENML specification can be found in the Evernote API Overview
            # at http://dev.evernote.com/documentation/cloud/chapters/ENML.php

            note.content = '<?xml version="1.0" encoding="UTF-8"?>'
            note.content += '<!DOCTYPE en-note SYSTEM ' \
                '"http://xml.evernote.com/pub/enml2.dtd">'
            note.content += '<en-note><br/>'
            if selftext is not None:
                note.content += '<h5>'+selftext+'</h5><br/>'
            if contentUrl is not None:
                note.content += '<a href="'+contentUrl+'">'+contentUrl+'</a><br/>'
            note.content += '<a href="'+postUrl+'">'+postUrl+'</a><br/>'
            if image is not None: 
                note.content += '<en-media width="300" height="225" type="image/png" hash="' + hash_hex + '"/>'
            
            print commentGroup
            for i,j in enumerate(commentGroup):
                try:
                    req = requests.get('https://api.reddit.com/api/info/?id=t1_'+commentGroup[i].split('/')[8], headers = {'User-agent': 'redditEvernoteBot'})

                    # If the response was successful, no Exception will be raised
                    req.raise_for_status()
                except HTTPError as http_err:
                    print(http_err)  # Python 3.6
                except Exception as err:
                    print(err)  # Python 3.6
                else:
                    reqData=req.json()
                    commentBody=None
                    try:
                        commentBody=reqData['data']['children'][0]['data']['body']
                    except:
                        print 'non standard format, skipping'
                        continue
                    print commentBody
                    note.content += '<br></br>Comment --- '+commentBody+'<br></br>'
            
            note.content += '</en-note>'

            # Finally, send the new note to Evernote using the createNote method
            # The new Note object that is returned will contain server-generated
            # attributes such as the new note's unique GUID.
            try:
                created_note = note_store.createNote(note)
            except Errors.EDAMSystemException, e:
                if e.errorCode == Errors.EDAMErrorCode.RATE_LIMIT_REACHED:
                    print "Rate limit reached"
                    print "Retry your request in %d seconds" % e.rateLimitDuration
                    time.sleep(e.rateLimitDuration+1)
                    try:
                        created_note = note_store.createNote(note)
                    except:
                        print 'failed'
                        continue
                        
                    

        
        # wait a random amnt of time
        time.sleep(random.randint(1,3))
        print 'Done'
        commentGroup=[]


print (len(comments))
print (len(posts))