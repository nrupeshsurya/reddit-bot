import json
import difflib
import praw                #necessary imports
import re
import time
import csv
import pandas as pd



api_key = ""                #enter your api key generated here
from apiclient.discovery import build                               #connect to youtube api
youtube = build('youtube','v3', developerKey = api_key) 

request = youtube.playlistItems().list(
        part="snippet",
        playlistId=" ",            #enter the playlistID here 
        maxResults = 50
    )
response = request.execute()


out_file = open("myfile.json", "w")  
json.dump(response, out_file, indent = 6)                       #json file dump for testing purposes 
out_file.close()


idlist = []
namelist = []

string = "https://www.youtube.com/watch?v="
for item in response['items']:
    vidid = item['snippet']['resourceId']['videoId']                    #fetch all the youtube links and names
    temp = string+vidid
    idlist.append(temp)
    namelist.append(item['snippet']['title'])
    

dict = {
    'Name' : namelist,
    'link' : idlist
}

generated = pd.DataFrame(dict)

flag = True
while(flag):
    try:
        nextpage = response['nextPageToken']
        request = youtube.playlistItems().list(
        part="snippet",
        playlistId="PL4osqbLPJ8e3lPyEjp4-VddO5Pzapze8r",
        maxResults = 50,
        pageToken = nextpage
    )
        response = request.execute()                                            #checking and adding if there are more than 50 songs because it only fetches 50 songs
        string = "https://www.youtube.com/watch?v="                             #at a time
        for item in response['items']:
            vidid = item['snippet']['resourceId']['videoId']
            temp = string+vidid
            idlist.append(temp)
            namelist.append(item['snippet']['title'])
    except:
        flag = False

dict = {
    'Name' : namelist,
    'link' : idlist
}

generated = pd.DataFrame(dict)
try:
    source = pd.read_csv('source.csv')                                                      #getting data from the source csv (this is all the songs which have already been posted)
except:
    source = pd.DataFrame(columns=['Name','link'])
newLinks = generated.merge(source, how='outer',indicator=True).loc[lambda x: x['_merge']=='left_only']   #generated - source = new links
print (newLinks)

file = open("source.csv","r+")
file.truncate(0)
file.close()

generated.to_csv('source.csv')                                                  #replace data of source to generated (matters even when file is deleted from playlist)

reddit = praw.Reddit(client_id=' ',                                             #insert relavant data here 
                     client_secret=' ',
                     password=' ',
                     user_agent='testscript by Nrupesh',           #can be any message you want it to be
                     username=' ')

reddit.validate_on_submit = True                                                #connection to reddit api


print(reddit.user.me())
subreddit = reddit.subreddit(" ")                           #add the playlist of choice (if you want multiple subreddits you can loop over in the submission part below)
errors = 0
List = newLinks['link'].tolist()
titles = newLinks['Name'].tolist()                                              #getting the names and links in the form of a list
i=0
def post():
    global subreddit
    global errors
    global i
    global List
    try:      
        subreddit.submit(titles[i],url=List[i])
        i+=1
        print("Posted a song")
        if(i == len(List)):                                                         #submitting a song 
            print("Done")
        else:
            post() 
    except praw.exceptions.RedditAPIException as e: 
        for s in e.items:
            if(s.error_type == "RATELIMIT"):
                delay = re.search("minutes?", s.message)

                if delay:
                    delay_seconds = float(int(delay.group(1))*60)                       #handling submission timeouts
                    time.sleep(delay_seconds)
                    post()
                else:
                    delay = re.search("seconds",e.message)
                    delay_seconds = float(delay.group(1))
                    time.sleep(delay_seconds)
                    post()

    except:
        errors = errors + 1
        if(errors > 5):
            print("Crashed")
            exit(1)                            
post()









