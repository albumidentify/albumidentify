import lastfm
import traceback
import tag

# Based loosely on lastfm tagger plugin for picard by rifraf

major_genres  = ["audiobooks", "blues", "classic rock", "classical", "country",
"dance", "electronica", "folk", "hip-hop", "indie", "jazz", "kids", "metal",
"pop", "punk", "reggae", "rock", "soul", "trance" ]

minor_genres = ['2 tone', 'a cappella', 'abstract hip-hop', 'acid', 
'acid jazz', 'acid rock', 'acoustic', 'acoustic guitar', 'acoustic rock', 
'adult alternative', 'adult contemporary', 'alternative', 'alternative country',
'alternative folk', 'alternative metal', 'alternative pop', 'alternative rock',
'ambient', 'anti-folk', 'art rock', 'atmospheric', 'aussie hip-hop',
'avant-garde', 'ballads', 'baroque', 'beach', 'beats', 'bebop', 'big band',
'blaxploitation', 'blue-eyed soul', 'bluegrass', 'blues rock', 'boogie rock',
'boogie woogie', 'bossa nova', 'breakbeat', 'breaks', 'brit pop', 'brit rock',
'british invasion', 'broadway', 'bubblegum pop', 'cabaret', 'calypso', 
'cha cha', 'choral', 'christian rock', 'classic country', 'classical guitar',
'club', 'college rock', 'composers', 'contemporary country', 
'contemporary folk', 'country folk', 'country pop', 'country rock', 'crossover', 'dance pop', 'dancehall', 'dark ambient', 'darkwave', 'delta blues', 
'dirty south', 'disco', 'doo wop', 'doom metal', 'downtempo', 'dream pop',
'drum and bass', 'dub', 'dub reggae', 'dubstep', 'east coast rap', 
'easy listening', 'electric blues', 'electro', 'electro pop', 'elevator music', 
'emo', 'emocore', 'ethnic', 'eurodance', 'europop', 'experimental', 
'fingerstyle', 'folk jazz', 'folk pop', 'folk punk', 'folk rock', 'folksongs', 
'free jazz', 'french rap', 'funk', 'funk metal', 'funk rock', 'fusion', 
'g-funk', 'gaelic', 'gangsta rap', 'garage', 'garage rock', 'glam rock', 
'goa trance', 'gospel', 'gothic', 'gothic metal', 'gothic rock', 'gregorian', 
'groove', 'grunge', 'guitar', 'happy hardcore', 'hard rock', 'hardcore', 
'hardcore punk', 'hardcore rap', 'hardstyle', 'heavy metal', 'honky tonk', 
'horror punk', 'house', 'humour', 'hymn', 'idm', 'indie folk', 'indie pop', 
'indie rock', 'industrial', 'industrial metal', 'industrial rock', 
'instrumental', 'instrumental hip-hop', 'instrumental rock', 'j-pop', 
'j-rock', 'jangle pop', 'jazz fusion', 'jazz vocal', 'jungle', 'latin', 
'latin jazz', 'latin pop', 'lounge', 'lovers rock', 'lullaby', 'madchester',
 'mambo', 'medieval', 'melodic rock', 'minimal', 'modern country', 
'modern rock', 'mood music', 'motown', 'neo-soul', 'new age', 'new romantic', 
'new wave', 'noise', 'northern soul', 'nu metal', 'old school rap', 'opera', 
'orchestral', 'philly soul', 'piano', 'political reggae', 'polka', 'pop life',
 'pop punk', 'pop rock', 'pop soul', 'post punk', 'post rock', 'power pop',
 'progressive', 'progressive rock', 'psychedelic', 'psychedelic folk', 
'psychedelic punk', 'psychedelic rock', 'psychobilly', 'psytrance', 'punk rock',
'quiet storm', 'r&b', 'ragga', 'rap', 'rap metal', 'reggae pop', 'reggae rock',
'rock and roll', 'rock opera', 'rockabilly', 'rocksteady', 'roots', 
'roots reggae', 'rumba', 'salsa', 'samba', 'screamo', 'shock rock', 
'shoegaze', 'ska', 'ska punk', 'smooth jazz', 'soft rock', 'southern rock',
'space rock', 'spoken word', 'standards', 'stoner rock', 'surf rock', 
'swamp rock', 'swing', 'symphonic metal', 'symphonic rock', 'synth pop', 
'tango', 'techno', 'teen pop', 'thrash metal', 'traditional country', 
'traditional folk', 'tribal', 'trip-hop', 'turntablism', 'underground', 
'underground hip-hop', 'underground rap', 'urban', 'vocal trance', 'waltz', 
'west coast rap', 'western swing', 'world', 'world fusion']

countries = ["african", "american", "arabic", "australian", "austrian", 
"belgian", "brazilian", "british", "canadian", "caribbean", "celtic", "chinese",
"cuban", "danish", "dutch", "eastern europe", "egyptian", "estonian", 
"european", "finnish", "french", "german", "greek", "hawaiian", "ibiza", 
"icelandic", "indian", "iranian", "irish", "island", "israeli", "italian", 
"jamaican", "japanese", "korean", "mexican", "middle eastern", "new zealand", 
"norwegian", "oriental", "polish", "portuguese", "russian", "scandinavian", 
"scottish", "southern", "spanish", "swedish", "swiss", "thai", "third world", 
"turkish", "welsh", "western"]

cities = ["acapulco", "adelaide", "amsterdam", "athens", "atlanta", 
"atlantic city", "auckland", "austin", "bakersfield", "bali", "baltimore", 
"bangalore", "bangkok", "barcelona", "barrie", "beijing", "belfast", "berlin", 
"birmingham", "bogota", "bombay", "boston", "brasilia", "brisbane", "bristol", 
"brooklyn", "brussels", "bucharest", "budapest", "buenos aires", "buffalo", 
"calcutta", "calgary", "california", "cancun", "caracas", "charlotte", 
"chicago", "cincinnati", "cleveland", "copenhagen", "dallas", "delhi", 
"denver", "detroit", "dublin", "east coast", "edmonton", "frankfurt", "geneva",
"glasgow", "grand rapids", "guadalajara", "halifax", "hamburg", "hamilton", 
"helsinki", "hong kong", "houston", "illinois", "indianapolis", "istanbul", 
"jacksonville", "kansas city", "kiev", "las vegas", "leeds", "lisbon", 
"liverpool", "london", "los angeles", "louisville", "madrid", "manchester", 
"manila", "marseille", "mazatlan", "melbourne", "memphis", "mexico city", 
"miami", "michigan", "milan", "minneapolis", "minnesota", "mississippi", 
"monterrey", "montreal", "munich", "myrtle beach", "nashville", "new jersey", 
"new orleans", "new york", "new york city", "niagara falls", "omaha", "orlando",
"oslo", "ottawa", "palm springs", "paris", "pennsylvania", "perth", 
"philadelphia", "phoenix", "phuket", "pittsburgh", "portland", "puebla", 
"raleigh", "reno", "richmond", "rio de janeiro", "rome", "sacramento", 
"salt lake city", "san antonio", "san diego", "san francisco", "san jose", 
"santiago", "sao paulo", "seattle", "seoul", "shanghai", "sheffield", "spokane",
"stockholm", "sydney", "taipei", "tampa", "texas", "tijuana", "tokyo", "toledo",
"toronto", "tucson", "tulsa", "vancouver", "victoria", "vienna", "warsaw", 
"wellington", "westcoast", "windsor", "winnipeg", "zurich"]
mood = ["angry", "bewildered", "bouncy", "calm", "cheerful", "chill", "cold", "complacent", "crazy", "crushed", "cynical", "depressed", "dramatic", "dreamy", "drunk", "eclectic", "emotional", "energetic", "envious", "feel good", "flirty", "funky", "groovy", "happy", "haunting", "healing", "high", "hopeful", "hot", "humorous", "inspiring", "intense", "irritated", "laidback", "lonely", "lovesongs", "meditation", "melancholic", "melancholy", "mellow", "moody", "morose", "passionate", "peace", "peaceful", "playful", "pleased", "positive", "quirky", "reflective", "rejected", "relaxed", "retro", "sad", "sentimental", "sexy", "silly", "smooth", "soulful", "spiritual", "suicidal", "surprised", "sympathetic", "trippy", "upbeat", "uplifting", "weird", "wild", "yearning"]
decade = [str(x)+"s" for x in range(1800,2010,10)]
year = [str(x) for x in range(1801,2010)]
occasion = ["background", "birthday", "breakup", "carnival", "chillout", "christmas", "death", "dinner", "drinking", "driving", "graduation", "halloween", "hanging out", "heartache", "holiday", "late night", "love", "new year", "party", "protest", "rain", "rave", "romantic", "sleep", "spring", "summer", "sunny", "twilight", "valentine", "wake up", "wedding", "winter", "work"]

def find_genres(genre_list, tag_list):
	ret=set()
	for tag in tag_list:
		if tag.lower() in genre_list:
			ret.add(tag)
	return list(ret)

def get_tags(tags,mbtrack,artistname):
	print "Looking up lastfm"
	artist_tags = lastfm.get_artist_toptags(artistname)
	track_tags =  lastfm.get_track_toptags(artistname,mbtrack.title)
	taglist = [
		i["name"][0]
		for i in 
		artist_tags['tag'] + track_tags['tag']
		if int(i["count"][0])>1
		]
	major=find_genres(major_genres, taglist)
	minor=find_genres(minor_genres, taglist)
	mmood=find_genres(mood, tags)
	moccasion=find_genres(occasion, taglist)
	mcountry=find_genres(countries, taglist)
	mdecade=find_genres(decade, taglist)
	#tags[tag.GENRE] = ",".join(major)
	#print "genre=",major,minor
	#print "mood=",mmood
	#print "occasion=",moccasion
	#print "decade=",mdecade
	#print "country=",mcountry

	tags[tag.MOOD] = ",".join(mmood)
	tags[tag.GENRE] = ",".join(set(major).union(set(minor)))
