print "Running Tweet request parse script"

def rss2record(entry):
    myd = {}

    myd['link'] = entry['link']	 # url for the entry
    myd['author'] = entry['author']
    myd['tweet'] = entry['title']
    year = entry.updated_parsed[0]
    month = entry.updated_parsed[1]
    day = entry.updated_parsed[2]
    hour = entry.updated_parsed[3]
    minute = entry.updated_parsed[4]
    myd['updated'] = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    # The twitter id is NOT stored in the ID field, you have to
    # extract if from the end of the link
    myd['ttt_id'] = entry['link'].split('/')[-1]
    #myd['ttt_id'] = ":".join(entry['id'].split(':')[-2:])

    return myd

def tweet_to_request(tweet_dict, tweet_id):

    d = rms_req_source_type
    request_dict = {}
    request_dict["timestamp"  ] = tweet_dict["updated"]
    request_dict["message"    ] = tweet_dict["tweet"]
    request_dict["source_id"  ] = tweet_id
    request_dict["source_type"] = d.keys()[d.values().index("Tweet")]
    return request_dict

import datetime
import gluon.contrib.feedparser as feedparser
url_base = "http://epic.cs.colorado.edu:9090/tweets.atom"

N = 100
start = 0
done = False
while done == False:
    
    print "Extracting RSS Entries: %6i through %6i" % (start, start+N-1)
    url = url_base + "?limit=" + str(start) + "," + str(N)
    d = feedparser.parse(url)

    for entry in d.entries:
        rec = rss2record(entry)
        
        # Make sure there are no duplicate entries before we add it:
        if db(db.rms_tweet_request.ttt_id == rec['ttt_id']).count() == 0:
            tweet_id = db.rms_tweet_request.insert(**rec)
            db.rms_req.insert(**tweet_to_request(rec, tweet_id))
        #else:
        #    done = True
        #    break

    start += N
    if len(d.entries) == 0:
        done = True

db.commit()
