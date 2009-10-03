#
# System to cache the return value of functions.
# 
# We use this to cache webservice calls and other very intensive operations.
#
import os
import shelve
import pickle
import atexit

memocache={}

# Make sure we write it out every so often
def _assure_memocache_open(name):
	if name not in memocache:
		if not os.path.isdir(os.path.expanduser("~/.mbcache/")):
			os.mkdir(os.path.expanduser("~/.mbcache/"))
		memocache[name]=shelve.open(os.path.expanduser("~/.mbcache/"+name),"c")

# This is a function, that returns a decorator, that returns a function,
# that caches the return value from a forth function.
def memoify(mappingfunc=lambda a,b:(a,b), cacheok=lambda arg,kwargs,ret:True):
	def memoify_decorator(func):
		def memoify_replacement(*args,**kwargs):
			_assure_memocache_open(func.__name__)
			dbkey=pickle.dumps(mappingfunc(args,kwargs))
			if dbkey not in memocache[func.__name__]:
				ret=func(*args,**kwargs)
				if cacheok(args,kwargs,ret):
					memocache[func.__name__][dbkey]=ret
					memocache[func.__name__].sync()
			else:
				ret = memocache[func.__name__][dbkey]

			return ret
		return memoify_replacement
	return memoify_decorator

# Remove an item from cache
def remove_from_cache(funcname,*args,**kwargs):
	_assure_memocache_open(funcname)
	key=pickle.dumps((args,kwargs))
	if key in memocache[funcname]:
		del memocache[funcname][key]

# Close and cleanup all the memocaches
def cleanup_memos():
	while memocache!={}:
		i=memocache.keys()[0]
		memocache[i].close()
		del memocache[i]

atexit.register(cleanup_memos)

