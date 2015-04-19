import urllib2
import config

def have_internet():
    try:
        response = urllib2.urlopen(config.have_internet_url,timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False
