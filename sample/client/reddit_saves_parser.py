#
# A simple Evernote API demo script that lists all notebooks in the user's
# account and creates a simple test note in the default notebook.
#
# Before running this sample, you must fill in your Evernote developer token.
#
# To run (Unix):
#   export PYTHONPATH=../../lib; python EDAMTest.py
#

import hashlib
import binascii
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types

from evernote.api.client import EvernoteClient

import requests
from requests.exceptions import HTTPError
from PIL import Image
from io import BytesIO
import urllib2, cStringIO
from urllib2 import urlopen
import base64



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

auth_token = "your devloper token"

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
    "Evernote EDAMTest (Python)",
    UserStoreConstants.EDAM_VERSION_MAJOR,
    UserStoreConstants.EDAM_VERSION_MINOR
)
print "Is my Evernote API version up to date? ", str(version_ok)
print ""
if not version_ok:
    exit(1)

note_store = client.get_note_store()

# List all of the notebooks in the user's account
notebooks = note_store.listNotebooks()
print "Found ", len(notebooks), " notebooks:"
for notebook in notebooks:
    print "  * ", notebook.name

print
print "Creating a new note in the default notebook"
print


with open("ALL REDDIT SAVES.txt", "r") as f:
    fileList = list(f.readlines())
    print len(fileList)

    # parse out dud reddit links (generic url or subreddit)
    with open('./generics removed.txt', 'w') as f2:
        with open('./generics clean.txt', 'w') as f3:

            for link in fileList:
                if "reddit" in link and len(link.split('/'))<=6:
                    f2.write(link)
                else:
                    f3.write(link)

with open("./generics clean.txt", "r") as f4:
    with open("./generics clean extracted comments.txt", "w") as f5:
        genList = list(f4.readlines())
        for link2 in range(0, len(genList)):
            # if it's a comment link
            if "reddit" in genList[link2] and len(genList[link2].split('/'))==10:
                f5.write(genList[link2])
                
posts=[]
comments=[]
with open("ALL REDDIT SAVES.txt", "r") as f6:
    fileList2 = list(f6.readlines())
    print len(fileList2)

    for link3 in fileList2:
        if "reddit" in link3 and len(link3.split('/'))==9:
            posts.append(link3)
        elif "reddit" in link and len(link3.split('/'))==10:
            posts.pop()
            comments.append(link3)
    print len(posts)
    print len(comments)

for p in range(0, 5):
    try:
        req = requests.get('https://api.reddit.com/api/info/?id=t3_'+posts[p].split('/')[6], headers = {'User-agent': 'redditEvernoteBot'})

        # If the response was successful, no Exception will be raised
        req.raise_for_status()
    except HTTPError as http_err:
        print(http_err)  # Python 3.6
    except Exception as err:
        print(err)  # Python 3.6
    else:
        print('Success!')
        # comment body
        reqData=req.json()
        note = Types.Note()
        note.title = reqData['data']['children'][0]['data']['title']
        note.tagNames=[reqData['data']['children'][0]['data']['subreddit'], 'reddit', 'reddit_saves_bot']
        selftext=reqData['data']['children'][0]['data']['selftext'] or None
        cUrl=reqData['data']['children'][0]['data']['url']
        contentUrl=cUrl if ("reddit" not in cUrl) else None
        thumbnailUrl=reqData['data']['children'][0]['data']['thumbnail'] or None
        postUrl='https://reddit.com'+reqData['data']['children'][0]['data']['permalink']


        # To include an attachment such as an image in a note, first create a Resource
        # for the attachment. At a minimum, the Resource contains the binary attachment
        # data, an MD5 hash of the binary data, and the attachment MIME type.
        # It can also include attributes such as filename and location.
        print thumbnailUrl
        if (thumbnailUrl is not None) and (not thumbnailUrl == 'self') and (not thumbnailUrl == 'spoiler'):

            # thumbnailReq=requests.get(thumbnailUrl)
            # image = Image.open(BytesIO(thumbnailReq.content))
            # image = Image.open(thumbnailReq.raw)

            # file3 = cStringIO.StringIO(urllib2.urlopen(thumbnailUrl).read())
            # image = Image.open(file3).tobytes()
            # x=urllib2.urlopen(thumbnailUrl)
            # with x as url:
            #     with open('temp.jpg', 'wb') as f:
            #         f.write(url.read())

            # image = Image.open('temp.jpg')
            image = urllib2.urlopen(thumbnailUrl).read()

            # image = base64.b64encode(contents)
            # print image


        else:
            image = open('enlogo.png', 'rb').read()


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
            note.content += '<h5>'+selftext+'YERTTTT'+'</h5><br/>'
        if contentUrl is not None:
            note.content += '<a href="'+contentUrl+'">'+contentUrl+'</a><br/>'
        note.content += '<a href="'+postUrl+'">'+postUrl+'</a><br/>'
        note.content += '<en-media width="300" height="225" type="image/png" hash="' + hash_hex + '"/>'
        note.content += '</en-note>'

        # Finally, send the new note to Evernote using the createNote method
        # The new Note object that is returned will contain server-generated
        # attributes such as the new note's unique GUID.
        created_note = note_store.createNote(note)


