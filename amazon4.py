#
# Functions for accessing the new Amazon Web Services 4.0
# Stole unmarshal() from amazon.py - a webservices 3.0 library.
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

import urllib
import urlparse
from xml.dom import minidom

aws_endpoints = { 'com' : 'webservices.amazon.com',
				  'uk' : 'webservices.amazon.co.uk',
				  'jp' : 'webservices.amazon.jp',
				  'fr' : 'webservices.amazon.fr',
				  'de' : 'webservices.amazon.de',
				  'ca' : 'webservices.amazon.ca' }
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

def __get_asin(asin):
	""" Given either a full URL or a straight ASIN, return the ASIN. """
	if len(asin) == 10:
		return asin
	elif asin[len(asin)-1] == '/':
		# sometimes the asin url may have a / at the end.
		return asin.split('/')[-2]
	else:
		return asin.split('/')[-1]

def __get_aws_endpoint(asin):
	""" Given an ASIN, return the AWS endpoing. 
	For example, if an ASIN of the form 'http://www.amazon.co.uk/...' is passed
	to this function it will return 'webservices.amazon.co.uk'.
	If an ASIN of the form "B00005NB28" is passed in, this function will default to
	returning 'webservices.amazon.com'
	"""
	if len(asin) == 10:
		return aws_endpoints['com']
	domain = urlparse.urlparse(asin).netloc
	return aws_endpoints[domain.split('.')[-1]]

def build_url(license_key, operation, asin, version='2007-01-15', response_group=None):
	params = {'Service' : 'AWSECommerceService',
			  'AWSAccessKeyId' : license_key,
			  'Operation' : operation,
			  'Version' : version,
			  'ItemId' : __get_asin(asin)}

	if response_group is not None:
		params['ResponseGroup'] = response_group

	return urlparse.urlunparse(('http',
						 __get_aws_endpoint(asin),
						 '/onca/xml',
						 '',
						 urllib.urlencode(params),
						 ''
						 ))

def search_by_asin(asin, license_key, response_group="Images", http_proxies=None):
	url = build_url(license_key = license_key, operation="ItemLookup", 
					asin = asin, response_group=response_group)
	u = urllib.FancyURLopener(http_proxies)
	usock = u.open(url)
	xmldoc = minidom.parse(usock)
	usock.close()

	data = unmarshal(xmldoc)
	print "ASIN:",asin,"url:",url

	if data.ItemLookupResponse.Items.Request.IsValid == 'False':
		raise Exception("Item lookup failed")

	return data.ItemLookupResponse.Items.Item



