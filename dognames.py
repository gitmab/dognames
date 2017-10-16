import random, string, glob, os, datetime
import pandas as pd

# list of valid names/IDs of future dogowners to rate names
validnames = ['M','C']

# if new instantiation of dognames, start with full dognames file
inputfile = 'dognames.txt'

# else get most recently modified namedata txt file in dir
latestmodtime = 0
for file in glob.glob('namedata*.txt'):
	modtime = os.stat(file).st_mtime
	if modtime > latestmodtime:
		latestmodtime = modtime
		inputfile = file
		
# check for / create lock file 
if inputfile=='inuse.txt':
	raise SystemExit('Currently in use')
else:
	tempFile = open('inuse.txt','w')

print 'Processing file {FN}...'.format(FN=inputfile)
print ''

# process inFile into dict
# FORMAT: name:[[vals for rater 1],[vals for rater 2], ..., [notes]]
# vals as strings here
with open(inputfile,'r') as inFile:
	nameDict = {}
	for line in inFile:
		if '#' in line:
			continue
		line = line.split('\t')
		if len(line[0]) < 1:
			continue
		nameDict[str.upper(line[0].strip('\n'))] = []
		if len(line) > 1:
			for i in range(1,len(line)):
				if len(string.strip(line[i],'\n')) > 0:
					nameDict[str.upper(line[0].strip('\n'))].append(string.strip(line[i],'\n').split(','))
				else:
					nameDict[str.upper(line[0].strip('\n'))].append([])
		else:
			for i in range(len(validnames)+1):
				nameDict[line[0].strip('\n')].append([])

# get init values (who is rating = where in dict val to write ratings)
username = ''
while username not in validnames:
	username = str.upper(raw_input('Who is rating (' + ','.join(map(str, validnames)) + '): '))
rateindex = validnames.index(username)
		
# MAIN LOOP
try:
        proceed = True
        while proceed:

                # info header
                print ''
                print '###########################################################################'
                print 'To save & quit: type SAVE'
                print 'To remove name from consideration: enter 0 or DEL <name>'
                print 'To rate name: enter value from 1-10'
                print 'To add new name: enter ADD <name>'
                print 'To get current top rated names: enter TOP <num> {' + ','.join(map(str, validnames)) + '} (e.g. TOP 10 ' + validnames[0] + ')'
                print 'To get current ratings for specific name: enter GET RATINGS <name>'
                print 'To add note for a name: enter NOTE <name> <note>'
                print 'To exit without saving: type QUIT'
                print 'Enter anything else to get new name without entering rating'
                print '###########################################################################'
                print ''
                
                # get random name
                name = random.choice(nameDict.keys())
                
                # get & process entry from user
                entry = raw_input(name.title() + ': ')

                # save
                if string.upper(str(entry)) == 'SAVE':
                        proceed = False

                # quit without saving
                elif string.upper(str(entry)) == 'QUIT':
                        raise SystemExit(0)

                # add new entry to db
                elif string.upper(str(entry))[0:3] == 'ADD':
                        newname = string.upper(str(entry)[4:])
                        if newname not in nameDict.keys():
                                nameDict[newname] = [[],[]]

                # print top N for one user or average of all users
                elif string.upper(str(entry))[0:3] == 'TOP':
                        topnum = int(string.split(str(entry),' ')[1])
                        topcol = str.upper(string.split(str(entry),' ')[2])
                        # convert dict to dataframe
                        namesDF = pd.DataFrame({
                                'NAME' : nameDict.keys(), 
                                validnames[0] : map(lambda x: round(sum([float(y) for y in x[0]])/len([int(y) for y in x[0]]),3) if len([int(y) for y in x[0]])>0 else 0, nameDict.values()), 
                                validnames[1] : map(lambda x: round(sum([float(y) for y in x[1]])/len([int(y) for y in x[1]]),3) if len([int(y) for y in x[1]])>0 else 0, nameDict.values()),
                                'NOTES' : map(lambda x: string.lower(string.join(x[-1], sep=', ')) if len(x) > len(validnames) else '', nameDict.values())
                                })
                        namesDF['ALL'] = (namesDF[validnames[0]] + namesDF[validnames[1]])/2
                        # get topnum names
                        print namesDF.sort(topcol,ascending=False)[0:topnum]

                # get ratings for a particular name
                elif 'GET RATINGS' in string.upper(str(entry)):
                        newname = string.upper(str(entry)[12:])
                        print ''
                        print 'ratings for {NAME}:'.format(NAME=string.upper(newname))
                        if newname in nameDict.keys():
                                for i in range(len(validnames)):
                                        print '{USER}: {RATES} (mean: {MEAN})'.format(USER=validnames[i], RATES=string.join(map(str,nameDict[newname][i]),sep=',') if len(nameDict[newname][i])>0 else 'none', MEAN=str(round(sum(map(float,nameDict[newname][i]))/len(nameDict[newname][i]), 3)) if len(nameDict[newname][i])>0 else 'na')
                                if len(nameDict[newname]) > len(validnames):
                                        print 'NOTES: {NOTES}'.format(NOTES=string.lower(string.join(nameDict[newname][-1], sep=', ')))
                        else:
                                print 'name {NAME} not found'.format(NAME=string.upper(newname))

                # add a note to a name
                elif string.upper(str(entry))[0:4] == 'NOTE':
                        notestrings = string.split(string.upper(str(entry)),sep=' ')
                        if string.upper(notestrings[1]) in nameDict.keys():
                                if len(nameDict[string.upper(notestrings[1])]) > len(validnames)+1:
                                        nameDict[string.upper(notestrings[1])][-1].append(string.join(notestrings[2:],sep=' '))
                                else:
                                        nameDict[string.upper(notestrings[1])].append([string.join(notestrings[2:],sep=' ')])
                        else:
                                print 'name {NAME} not found'.format(NAME=notestrings[1])

                # delete an entry (either thru DEL or thru zero rating)
                elif string.upper(str(entry))[0:3]=='DEL':
                        del nameDict[string.upper(str(entry)[4:])]
                elif str(entry)=='0':
                        del nameDict[name]

                # add a 1-10 numeric rating to the user's name ratings
                elif str(entry).isdigit() and (len(str(entry))==1 or str(entry)=='10'):
                        nameDict[name][rateindex].append(entry)
                        # if all users rate as mean of 2 or below, delete name
                        if min([len(x) for x in nameDict[name]]) > 0:
                                if max([sum(map(float,x))/len(map(float,x)) for x in nameDict[name] if str(x[0]).isdigit()]) <= 2:
                                        print 'Deleted by consensus'
                                        del nameDict[name]
                        
        # save (write dict to new txt file) & quit
        outputfile = datetime.datetime.now().strftime("namedata_%Y%m%d_%H%M%S.txt")
        with open(outputfile,'w') as outFile:
                outFile.write(string.join(['# name'] + validnames, sep='\t') + '\n') #header
                for name in nameDict.keys():
                        vals = [string.join(map(str,x),sep=',') for x in nameDict[name]] # list of each user's comma-separated ratings
                        outFile.write(string.join([string.strip(name,'\n')] + vals, sep='\t') + '\n')
        print 'File {FN} generated.'.format(FN=outputfile)

except:
	pass

# remove lock file
tempFile.close()
os.remove('inuse.txt')
