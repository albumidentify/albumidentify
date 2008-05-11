#
# Functions for accessing the new Amazon Web Services 4.0
# Stole unmarshal() from amazon.py - a webservices 3.0 library.
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

import urllib
from xml.dom import minidom

class Bag: pass

def unmarshal(element):
    rc = Bag()
    if isinstance(element, minidom.Element) and (element.tagName == 'Details'):
        rc.URL = element.attributes["url"].value
    childElements = [e for e in element.childNodes if isinstance(e, minidom.Element)]
    if childElements:
        for child in childElements:
            key = child.tagName
            if hasattr(rc, key):
                if type(getattr(rc, key)) <> type([]):
                    setattr(rc, key, [getattr(rc, key)])
                setattr(rc, key, getattr(rc, key) + [unmarshal(child)])
            elif isinstance(child, minidom.Element) and (child.tagName == 'Details'):
                # make the first Details element a key
                setattr(rc,key,[unmarshal(child)])
                #dbg: because otherwise 'hasattr' only tests
                #dbg: on the second occurence: if there's a
                #dbg: single return to a query, it's not a
                #dbg: list. This module should always
                #dbg: return a list of Details objects.
            else:
                setattr(rc, key, unmarshal(child))
    else:
        rc = "".join([e.data for e in element.childNodes if isinstance(e, minidom.Text)])
        if element.tagName == 'SalesRank':
            rc = rc.replace('.', '')
            rc = rc.replace(',', '')
            rc = int(rc)
    return rc

def build_url(marketplace, license_key, operation, asin, version='2007-01-15', response_group=None):
	if marketplace != ".co.uk" and marketplace != ".com":
		mp = ".com"
	else:
		mp = marketplace
	url = "http://webservices.amazon" + mp + "/onca/xml?Service=AWSECommerceService"
	url += "&AWSAccessKeyId=" + license_key
	url += "&Operation=" + operation
	url += "&Version=" + version
	url += "&ItemId=" + asin
	if response_group is not None:
		url = url + "&ResponseGroup=" + response_group
		
	return url

def search_by_asin(marketplace, asin, license_key, response_group="", http_proxies=None):
	url = build_url(marketplace = marketplace, license_key = license_key, operation="ItemLookup", 
					asin = asin, response_group="Images")
	u = urllib.FancyURLopener(http_proxies)
	usock = u.open(url)
	xmldoc = minidom.parse(usock)
	usock.close()

	data = unmarshal(xmldoc)

	if data.ItemLookupResponse.Items.Request.IsValid == 'False':
		raise Exception("Item lookup failed")

	return data.ItemLookupResponse.Items.Item



