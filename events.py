from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from os import listdir

def create_eventdictionary(filename, hometeam, folder = ''):
	edictionary = {} # the dictionary to return; keys will be timestamps
	preamble, allrows = get_rows(filename, folder) # make the total list of rows -- each is a string
	print(allrows[len(allrows) - 1])
	eventfcns = [get_event1, get_event2, get_event3, get_event4, get_event5] # the functions that will populate the events columns
	for i in range(len(allrows)):
		# set edictionary to be a dictionary with just SUB IN, SUB OUT, TIMEOUT keys and empty strings
		if (not get_time(allrows[i], period=True) in edictionary.keys()):
			edictionary[get_time(allrows[i], period=True)] = {'SUB IN ':'', 'SUB OUT':'', 'TIMEOUT':''}
		counter = 0 # will keep track of which A (as in eventA)
		event = None
		if (not '(DEADBALL)' in allrows[i]): # don't even go in to populate if (DEADBALL) in row
			for eventfcn in eventfcns:
				counter = counter+1
				# set up the before and after rows, don't include anything with '(DEADBALL)' or 'SUB ' or 'TIMEOUT'
				ind_len = min(3, i)
				back_indices = []
				for j in range(ind_len):
					back_indices.append(i-1-j)
				# change from backwards order to correct order
				indices = back_indices[::-1]
				done = False
				while (not done):
					changed = False
					for j in range(len(indices)):
						if (any(['(DEADBALL)' in allrows[indices[j]], 'SUB ' in allrows[indices[j]], 'TIMEOUT' in allrows[indices[j]]])):
							indices[j] = max(indices[j] - 1, 0)
							changed = True
					if (len(indices) > 0):
						if (any([not changed, min(indices) == 0])):
							done = True
					else:
						done = True
				before_stuff = []
				for j in range(3 - len(indices)):
					before_stuff.append('0-20:00')
				for j in range(len(indices)):
					before_stuff.append(allrows[indices[j]])
				# this has created a list of length 3 containing the 3 previous rows (if none of them have (DEADBALL), SUB, TIMEOUT and there are 3 previous rows)
				# if some of those things don't hold then it puts the string 0-20:00 in the spot in the list
				if (i < len(allrows)-2):
					indices = [i+1,i+2]
				elif (i < len(allrows)-1):
					indices = [i+1]
				else:
					indices = []
				done = False
				while (not done):
					changed = False
					for j in range(len(indices)):
						try:
							if (any(['(DEADBALL)' in allrows[indices[j]], 'SUB ' in allrows[indices[j]], 'TIMEOUT' in allrows[indices[j]]])):
								indices[j] = min(indices[j] + 1, len(allrows)-1)
								changed = True
						except IndexError:
							print(indices)

					if (not changed):
						done = True
					elif (len(indices)>0):
						if (max(indices)==len(allrows)-1):
							done =True
				if (len(indices)==0):
					after_stuff = ['0-00:00','0-00:00']
				else:
					try:
						after_stuff = [allrows[indices[0]],allrows[indices[1]]]
					except IndexError:
						after_stuff = [allrows[indices[0]],'0-00:00']
				# the same, but with the 3 rows after current row
				# checks that the return value is not None (which would happen if eventfcn==get_event1 but allrows[i] doesn't have event1, for example)
				if(eventfcn(allrows[i], before_stuff, after_stuff)): 
					# populate the eventA column for this row (with key == the timestamp); output is string like 'MISSED LAYUP' or 'FOUL'
					event = eventfcn(allrows[i], before_stuff, after_stuff)
					if (any([all(['REBOUND' in event, 'BLOCK' in before_stuff[-1]]), all([event == 'STEAL', 'TURNOVR' in before_stuff[-1]])])):
						edictionary[get_time(before_stuff[-1], period=True)]['event' + str(counter)] = event # adjust for REBOUND (DEF) and (OFF) after BLOCK and STEAL after TURNOVR
						# populate the playerA column for this row
						edictionary[get_time(before_stuff[-1], period=True)]['player' + str(counter)] = get_player(allrows[i], event) 
					else:
						edictionary[get_time(allrows[i], period=True)]['event' + str(counter)] = event
						# populate the playerA column for this row
						edictionary[get_time(allrows[i], period=True)]['player' + str(counter)] = get_player(allrows[i], event)
		for inout in ['IN ','OUT']: # Note: 'IN ' has space at end because of where the colon is placed in play-by-play html files
			edictionary[get_time(allrows[i], period=True)]['SUB ' + inout] = edictionary[get_time(allrows[i], period=True)]['SUB ' + inout] + get_subs(allrows[i], inout)
		if 'TIMEOUT' in allrows[i]:
			edictionary[get_time(allrows[i], period=True)]['TIMEOUT'] = get_timeout(allrows[i])
		# record in two columns the number of points scored in this event, for each side
		if (event):
			if ('ptsTU' in edictionary[get_time(allrows[i], period=True)].keys()):
				if (hometeam == 'TU'):
					edictionary[get_time(allrows[i], period=True)]['ptsTU'] = edictionary[get_time(allrows[i], period=True)]['ptsTU'] + get_pts(allrows[i], event, 'home') # use the side in get_pts (home is always on a particular side)
					edictionary[get_time(allrows[i], period=True)]['ptsOpp'] = edictionary[get_time(allrows[i], period=True)]['ptsOpp'] + get_pts(allrows[i], event, 'visitor')
				else:
					edictionary[get_time(allrows[i], period=True)]['ptsTU'] = edictionary[get_time(allrows[i], period=True)]['ptsTU'] + get_pts(allrows[i], event, 'visitor')
					edictionary[get_time(allrows[i], period=True)]['ptsOpp'] = edictionary[get_time(allrows[i], period=True)]['ptsOpp'] + get_pts(allrows[i], event, 'home')
			else:
				if (hometeam == 'TU'):
					edictionary[get_time(allrows[i], period=True)]['ptsTU'] = get_pts(allrows[i], event, 'home') # use the side in get_pts (home is always on a particular side)
					edictionary[get_time(allrows[i], period=True)]['ptsOpp'] = get_pts(allrows[i], event, 'visitor')
				else:
					edictionary[get_time(allrows[i], period=True)]['ptsTU'] = get_pts(allrows[i], event, 'visitor')
					edictionary[get_time(allrows[i], period=True)]['ptsOpp'] = get_pts(allrows[i], event, 'home')
	# at this point, program has gone through every row and filled in events, players, subs, and points
		for j in range(5):
			if (not 'event' + str(j+1) in edictionary[get_time(allrows[i], period=True)].keys()):
				edictionary[get_time(allrows[i], period=True)]['event' + str(j+1)] = ''
			if (not 'player' + str(j+1) in edictionary[get_time(allrows[i], period=True)].keys()):
				edictionary[get_time(allrows[i], period=True)]['player' + str(j+1)] = ''
	# setofplayers is the list of all players that were recorded as being involved in a play throughout the whole game
	setofplayers = []
	for time in edictionary.keys():
		for i in range(3):
			if(edictionary[time]['player' + str(i+1)] != '' and not edictionary[time]['player' + str(i+1)] in setofplayers):
				setofplayers.append(edictionary[time]['player' + str(i+1)])
	# make a column for each player in game (before), put a 1 in this row if they are in, a 0 otherwise
	for playername in setofplayers:
		edictionary = add_playtimes(edictionary, playername, preamble) # puts the zeros and ones (i.e., 'off the court' and 'on the court') into a column for that player

	return edictionary

def get_rows(filename, folder = ''):
	'''
	generates the rows of the play-by-play data
	'''
	with open(folder + filename + '.html') as file:
		soup = BeautifulSoup(file, "lxml")
	# the following is for the format used in 2017-2018
	preamble = str(soup.find_all('pre')[0])
	table = soup.find_all('font', {'size':'-1'})
	split_table = re.split('------------------------------------------------------------------------------------------------',str(table))
	# Danger: some versions of Python may need something besides '\\n' here...
	periods = [re.split('\\n', split_table[1:][i]) for i in range(len(split_table[1:]))]
	# get rid of summary info after period of play
	end_indices = [-1, -1 , -1]
	for i in range(len(periods)):
		for j in range(len(periods[i])):
			if (periods[i][j] == '<hr/>'):
				end_indices[i] = j
				break
	trimmed_periods = [add_period(periods[i][ :end_indices[i]], i+1) for i in range(len(periods))]  # This is a list of each period of play, with each period of play being a list of lines in play-by-play
	for i in range(len(trimmed_periods)):
		try:
			table_rows = table_rows + trimmed_periods[i]
		except:
			if (i == 0):
				table_rows = trimmed_periods[i]
	return preamble, table_rows

def get_subs(row, inout):
	'''
	grabs players subbed in and subbed out of the game
	'''
	output = ''
	if ('SUB ' + inout in row):
		for s in row.split(':'):
			s_index = row.index(s)
			opp_inout = ''
			if (inout == 'IN '):
				opp_inout = 'OUT'
			else:
				opp_inout = 'IN '
			if (all([',' in s, not('SUB ' + opp_inout in row[max(s_index-8, 0):s_index])])):
				output = output + s.split(',')[0] + '!' # This should be the last name of the SUB, followed by '!'
	return output

def get_timeout(row):
	'''
	grabs timeout type
	'''
	to_type = ''
	to_flags = ['30sec', 'media', 'MEDIA', 'TEAM']
	timeout = row.split('TIMEOUT ')[1]
	for t in to_flags:
		if t in timeout:
			to_type = t
	return to_type

def add_period(row_list, num_period):
	'''
	adds a number and a hyphen (e.g., '1-') in front of each timestamp to distinguish times that happen in different periods 
	'''
	p = str(num_period) + '-'
	newlist = []
	for row in row_list:
		try:
			newlist.append( row.split(get_time(row))[0] + p + get_time(row) + row.split(get_time(row))[1] )
		except IndexError:
			print('Possible empty row')
			continue
	return newlist

def get_time(row, **kwargs):
	'''
	grabs the time in a row
	'''
	if (len(row)==0):
		return None
	else:
		z1=''
		z2=''
		period = ''
		try:
			minute = int(re.split(':',row)[0][-2:])
			second = int(re.split(':',row)[1][:2])
			if ('period' in kwargs.keys()):
				if (kwargs['period']):
					period = re.split(':',row)[0][-4] + '-'
		except ValueError:
			minute = int(re.split(':',row)[1][-2:])
			second = int(re.split(':',row)[2][:2])
			if ('period' in kwargs.keys()):
				if (kwargs['period']):
					period = re.split(':',row)[1][-4] + '-'
		if (minute < 10):
			z1 = '0'
		if (second < 10):
			z2 = '0'
		return period + z1 + str(minute) + ':' + z2 + str(second)

def timestamp_to_seconds(periodandtime):
	'''
	converts timestamps (type str) to seconds (type int)
	'''
	triple = re.split('-|:',periodandtime)
	try:
		return (int(triple[0])-1)*20*60 + (19 - int(triple[1]))*60 + (60 - int(triple[2])) ## this, if first half is 1-, second half 2-, etc. If first half is 0-, second half 1-, etc, then just use int(triple[0]) instead of int(triple[0])-1.
		# also, this presumes that nothing ever gets recorded at time 20:00
	except IndexError:
		print('Error in the time format')
		return None

def seconds_to_timestamp(secs):
	'''
	converts seconds (type int) into timestamps (type str)
	'''
	period = int(secs/(20*60))+1
	minutes = 19 - int((secs - (period-1)*20*60)/60)
	seconds = secs - (period-1)*20*60 - (19 - minutes)*60
	if (seconds == 0):
		minutes = minutes + 1
		seconds = 60
	if (minutes == 20):
		period = period - 1
		minutes = 0
	if (minutes < 10):
		str_minutes = '0' + str(minutes)
	else:
		str_minutes = str(minutes)
	if (60 - seconds < 10):
		str_seconds = '0' + str(60 - seconds)
	else:
		str_seconds = str(60 - seconds)
	return str(period) + '-' + str_minutes + ':' + str_seconds

def add_playtimes(edict, pname, preamb):
	tmp_dict = edict.copy()
	is_in = False
	# put in something that catches if the player is a starter; sets is_in to True
	rows_of_preamble = re.split('\\n', preamb)
	for row in rows_of_preamble:
		if (all([pname in row, any(['. f' in row, '. g' in row])])):
			is_in = True
	ordered_keys = np.sort([timestamp_to_seconds(tstamp) for tstamp in edict.keys()])
	for k in ordered_keys:
		if (pname in edict[seconds_to_timestamp(k)]['SUB IN ']):
			is_in = True
		if (pname in edict[seconds_to_timestamp(k)]['SUB OUT']):
			is_in = False
		# after having decided whether the player has been subbed in or out at this moment and changing is_in accordingly...
		tmp_dict[seconds_to_timestamp(k)][pname] = int(is_in)
	return tmp_dict

# the following functions (get_event1, get_event2, ..., get_event6) grab events in each play row-by-row and categorizes them in the order in which they occur
# they all have the same structure: first goes through the eventAflags list, then goes through alt_eventAflags list
# to populate edictionary with elements in alt_eventAflags, each get_event function goes through a series of conditionals
# there can be as few as 1 event in a play (e.g., MISSED 3 PTR)
# there can be as many as 6 events in a play (e.g., MISSED 3 PTR, FOUL, GOOD!/MISSED FT SHOT (x2), MISSED FT SHOT, REBOUND)

def get_event1(row, rows_before, rows_after):
	useit = False # a Boolean that says whether we have found a primary event in this row or not
	foundflag = '' # a string that contains the keyword that told us we found the primary event (and that begins the string that identifies the event)
	event1flags = ['GOOD!', 'MISSED', 'STEAL'] # possible candidates for the variable foundflag
	alt_event1flags = ['FOUL', 'TURNOVR'] # conditional candidates for foundflag; these events are not always primary
	for flag in event1flags:
		if (flag in row):
			if (not 'FT SHOT' in row):
				useit = True
				foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0] ## assumes that the flag appears just once in the row
	else:
		for flag in alt_event1flags:
			if (all([get_time(row) != get_time(rows_before[-1]), flag in row])):
				if all([flag == 'FOUL', any([all([not 'GOOD!' in row, not 'MISSED' in row]), any(['GOOD! FT SHOT' in row, 'MISSED FT SHOT' in row]) ]) ]):
				#	personal = row.split('(P')[1].split('T')[0]
				#	team = personal.split('T')[1].split(')')[0]
				#	p_counter = 'Personal Foul No. ' + personal
				#	t_counter = 'Team Foul No. ' + team
					useit = True
					foundflag = flag
				elif all([flag == 'TURNOVR', not 'STEAL' in row]):
					if any([timestamp_to_seconds(get_time(rows_after[0], period = True)) - timestamp_to_seconds(get_time(row, period = True)) > 1, not 'STEAL' in rows_after[0]]): 
						useit = True
						foundflag = flag
		if (useit):
			return (foundflag + row.split(foundflag)[1]).split(' by')[0]
		else:
			return None

def get_event2(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event2flags = ['ASSIST', 'BLOCK']
	alt_event2flags = ['FOUL', 'REBOUND', 'TURNOVR', 'FT SHOT']
	for flag in event2flags:
		if (flag in row):
			useit = True
			foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0] # assumes that the flag appears just once in the row
	else:
		for flag in alt_event2flags:
			if (flag in row):
				if (get_time(row) == get_time(rows_before[-1])): # everything in this block has at least one row above w/ matching time
					if all([flag == 'FT SHOT', 'FOUL' in rows_before[-1]]):
						useit = True
						if ('GOOD! FT SHOT' in row):
							foundflag = 'GOOD! ' + flag
						else:
							foundflag = 'MISSED ' + flag
					if all([flag == 'FOUL', any(['GOOD!' in rows_before[-1], 'MISSED' in rows_before[-1], 'TURNOVR' in rows_before[-1]])]):
					#	personal = row.split('(P')[1].split('T')[0]
					#	team = personal.split('T')[1].split(')')[0]
					#	p_counter = 'Personal Foul No. ' + personal
					#	t_counter = 'Team Foul No. ' + team
						useit = True
						foundflag = flag
					elif all([flag == 'REBOUND', not 'MISSED FT SHOT' in rows_before[-1], not 'MISSED FT SHOT' in row]):
						reb_type = row.split('(')[1].split(')')[0]
						useit = True
						foundflag = flag + ' (' + reb_type + ')'
					elif all([flag == 'TURNOVR', 'STEAL' in row]):
						useit = True
						foundflag = flag
				elif all([flag == 'TURNOVR', 'STEAL' in rows_after[0], timestamp_to_seconds(get_time(rows_after[0], period = True)) - timestamp_to_seconds(get_time(row, period = True)) == 1]):
					useit = True
					foundflag = flag
				elif all([any([flag == 'FT SHOT', flag == 'REBOUND', all([flag=='FOUL', ('GOOD!' in row or 'MISSED' in row)])]), timestamp_to_seconds(get_time(rows_before[-1], period = True)) != timestamp_to_seconds(get_time(row, period = True))]): 
					useit = True
					if (flag == 'FT SHOT'):
						if ('GOOD! FT SHOT' in row):
							foundflag = 'GOOD! ' + flag
						else:
							foundflag = 'MISSED ' + flag
					else:
						foundflag = flag
		if (useit):
			return (foundflag + row.split(foundflag)[1]).split(' by')[0]
		else:
			return None

def get_event3(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event3flags = ['FT SHOT', 'REBOUND', 'FOUL']
	for flag in event3flags:
		if (flag in row):
			if (get_time(row) == get_time(rows_before[-1])):
				if (flag == 'FT SHOT'):
					if ('FOUL' in rows_before[-2]):
						useit = True
						if ('GOOD! FT SHOT' in row):
							foundflag = 'GOOD! ' + flag
						else:
							foundflag = 'MISSED ' + flag
					elif all(['FOUL' in row, any(['GOOD!' in rows_before[-1], 'MISSED' in rows_before[-1]]), not 'FT SHOT' in rows_before[-1]]): 
						useit = True
						if ('GOOD! FT SHOT' in row):
							foundflag = 'GOOD! ' + flag
						else:
							foundflag = 'MISSED ' + flag
					elif all(['MISSED FT SHOT' in rows_before[-2], get_time(row) == get_time(rows_before[-2]), get_time(row) != get_time(rows_before[-3])]):
						useit = True
						if ('GOOD! FT SHOT' in row):
							foundflag = 'GOOD! ' + flag
						else:
							foundflag = 'MISSED ' + flag
				elif (flag == 'REBOUND'):
					if all(['FOUL' in rows_before[-1], 'MISSED FT SHOT' in rows_before[-1], get_time(rows_before[-2],period=True) != get_time(rows_before[-1],period=True)]):
						# for some reason, each rebound after a blocked shot is recorded as happening 2 seconds after the initial shot
						reb_type = row.split('(')[1].split(')')[0]
						useit = True
						foundflag = flag + ' (' + reb_type + ')'
				elif (flag == 'FOUL'):
					if any(['ASSIST' in rows_before[-1], all(['TURNOVR' in rows_before[-1], 'STEAL' in rows_before[-1]]), ('TURNOVR' in rows_before[-2]) and ('STEAL' in rows_before[-1])]):
						useit = True
						foundflag = flag
			if all([(flag == 'FT SHOT'), get_time(row) == get_time(rows_before[-1]), ('FOUL' in rows_before[-1] and 'GOOD! FT SHOT' in rows_before[-1]), (get_time(row,period=True) != get_time(rows_before[-2],period=True))]):
				useit = True
				if ('GOOD! FT SHOT' in row):
					foundflag = 'GOOD! ' + flag
				else:
					foundflag = 'MISSED ' + flag
			if all([(flag == 'REBOUND'), ('BLOCK' in rows_before[-1]), (timestamp_to_seconds(get_time(row, period = True)) - timestamp_to_seconds(get_time(rows_before[-1], period = True)) < 3)]): ## !!! add this check outside of the current if block (also for steals + turnovers)
			# for some reason, each rebound after a blocked shot is recorded as happening 2 seconds after the initial shot
				reb_type = row.split('REBOUND (')[1].split(')')[0]
				useit = True
				foundflag = flag + ' (' + reb_type + ')'
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_event4(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event4flags = ['GOOD! FT SHOT', 'MISSED FT SHOT', 'REBOUND']
	for flag in event4flags:
		if (flag in row) and (get_time(row) == get_time(rows_before[-1])):
			if (flag == 'GOOD! FT SHOT'):
				if (all(['FOUL' in row, 'ASSIST' in rows_before[-1]])):
					useit=True
					foundflag = flag
			elif (flag == 'MISSED FT SHOT'):
				if (all(['FOUL' in row, 'ASSIST' in rows_before[-1]])):
					useit = True
					foundflag = flag
			elif (flag == 'REBOUND'):
				if all([('MISSED FT SHOT' in row), ('FOUL' in rows_before[-1])]):
					reb_type = row.split('REBOUND (')[1].split(')')[0]
					useit = True
					foundflag = flag + ' (' + reb_type + ')'
				elif all([('MISSED FT SHOT' in rows_before[-1]), ('FOUL' in rows_before[-2])]):
					reb_type = row.split('REBOUND (')[1].split(')')[0]
					useit = True
					foundflag = flag + ' (' + reb_type + ')'
				elif all([('MISSED FT SHOT' in rows_before[-1]), ('FOUL' in rows_before[-1]), ('GOOD!' in rows_before[-2])]):
					reb_type = row.split('REBOUND (')[1].split(')')[0]
					useit = True
					foundflag = flag + ' (' + reb_type + ')'
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_event5(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event5flags = ['REBOUND']
	for flag in event5flags:
		if (flag in row) and (get_time(row) == get_time(rows_before[-1])):
			# add missed fouled 3 PTR
			if all(['MISSED FT SHOT' in rows_before[-1], 'FOUL' in rows_before[-1], 'ASSIST' in rows_before[-2]]):
				reb_type = row.split('(')[1].split(')')
				useit= True
				foundflag = flag
			elif all(['MISSED FT SHOT' in row, 'FT SHOT' in rows_before[-1], 'MISSED' in rows_before[-2]]):
				reb_type = row.split('(')[1].split(')')
				useit= True
				foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None
def get_event6(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event5flags = ['REBOUND']
	for flag in event5flags:
		if (flag in row) and (get_time(row) == get_time(rows_before[-1])):
			# add missed fouled 3 PTR
			if all(['MISSED FT SHOT' in rows_before[-1], 'FT SHOT' in rows_before[-2], 'FT SHOT' in rows_before[-3]]):
				reb_type = row.split('(')[1].split(')')
				useit= True
				foundflag = flag
			elif all(['MISSED FT SHOT' in row, 'FT SHOT' in rows_before[-1], 'FT SHOT' in rows_before[-2], 'FOUL' in rows_before[-3], 'MISSED 3 PTR' in rows_before[-3]]):
				reb_type = row.split('(')[1].split(')')
				useit= True
				foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_player(row, event):
	'''
	grabs the last name of a player
	'''
	player = row.split(event + ' by ')[1]
	if ('(TEAM)' in player):
		last_name = '(TEAM)'
	else:
		last_name = player.split(',')[0]
	return last_name

def get_pts(row, thisrow_event, homevisitor):
	'''
	counts points a team scores in a play
	'''
	pts = 0
	if ('GOOD!' in thisrow_event): # is a made basket
		if ('3 PTR' in thisrow_event):
			pts = 3
		elif ('FT SHOT' in thisrow_event):
			pts = 1
		else:
			pts = 2
	which_gets_points = ''
	if (pts > 0):
		split_row = row.split(get_time(row))
		if (thisrow_event in split_row[0]):
			which_gets_points = 'home' # home team is recorded on the left
		else:
			which_gets_points = 'visitor'
	if (homevisitor == which_gets_points):
		return pts
	else:
		return 0


class FourFactors:
	def __init__(self, filename):
		self.name = filename
		self.event_dictionary = create_eventdictionary(filename, 'TU')
		self.home_roster, self.away_roster = self.create_rosters(filename)
		self.total_poss = self.possessions('1-20:00', '2-00:00')
		self.ff = print(self.four_factors('1-20:00', '2-00:00', 'Starr'))
	def helper(self, s, play):
		'''
		finds the integer after 'event' keys where event occurs (e.g., if 'GOOD! 3 PTR' is passed in and appears in the key 'event1', this function returns 1)
		'''
		found = False
		for k in play.keys():
			if 'event' in k:
				if (s in play[k]):
					found = True
		return found
	def create_rosters(self, filename):
		'''
		creates home and away rosters
		'''
		team_summaries = re.split('\\n\\n\\n',get_rows(filename)[0])[:2]
		for ts in team_summaries:
			'''
			need to determine whether we want to keep this as home/away rosters or change it to TU/opponent rosters?
			'''
		    if 'VISITORS' in ts:
		        away_roster = []
		        lines = re.split('\\n', ts)
		        for l in lines:
		            try:
		                int(l[:2])
		                if (l[2] ==' '):
		                    away_roster.append(re.split(',',l)[0][3:])
		            except ValueError:
		                pass
		    if 'HOME TEAM' in ts:
		        home_roster = []
		        lines = re.split('\\n', ts)
		        for l in lines:
		            try:
		                int(l[:2])
		                if (l[2] ==' '):
		                    home_roster.append(re.split(',',l)[0][3:])
		            except ValueError:
		                pass
		return home_roster, away_roster
	def get_event_player(self, name, play):
		'''
		finds the integer after 'player' keys where player appears (e.g., if SMITH is passed in and appears in keys 'player2' and 'player3', this function returns [2, 3])
		'''
		found = []
		name_list = []
		for k in play.keys():
			if 'player' in k:
				if (name in play[k]):
					found.append(int(k[-1]))
		return found
	def possessions(self, begin_time, end_time, playername = ''):
		'''
		counts possessions in a time interval
		'''
		poss_count = 0
		start = timestamp_to_seconds(begin_time)
		finish = timestamp_to_seconds(end_time)
		for time in range(start, finish + 1):
			current_time = seconds_to_timestamp(time)
			try:
				if (len(playername) > 0):
					if (self.event_dictionary[current_time][playername]):
						if any([(self.helper('TURNOVR', self.event_dictionary[current_time])), (self.helper('REBOUND (DEF)', self.event_dictionary[current_time]))]):
							poss_count += 1
						elif self.helper('GOOD!', self.event_dictionary[current_time]):
							if self.helper('FT SHOT', self.event_dictionary[current_time]) == False:
								poss_count += 1 
							elif all([self.helper('FT SHOT', self.event_dictionary[current_time]), self.helper('REBOUND (OFF)', self.event_dictionary[current_time]) == False]): # !!!
								poss_count += 1
					else:
						pass
				else:
					if any([(self.helper('TURNOVR', self.event_dictionary[current_time])), (self.helper('REBOUND (DEF)', self.event_dictionary[current_time]))]):
						poss_count += 1
					elif self.helper('GOOD!', self.event_dictionary[current_time]):
						if self.helper('FT SHOT', self.event_dictionary[current_time]) == False:
							poss_count += 1 
						elif all([self.helper('FT SHOT', self.event_dictionary[current_time]), self.helper('REBOUND (OFF)', self.event_dictionary[current_time]) == False]): # !!!
							poss_count += 1
			except KeyError:
				# handles situation when timestamp doesn't exist
				continue
		return poss_count

	def four_factors(self, begin_time, end_time, last_name):
		# computes 'four' factors for each player in a time interval; output is a numpy array that is like a vector in 6-dimensional space
		start = timestamp_to_seconds(begin_time)
		finish = timestamp_to_seconds(end_time)
		factor_list = []
		fga = 0
		fgm = 0
		to_counter = 0
		reb_counter = 0
		oreb_counter = 0 # offensive rebounds are seen as a negative factor bc total offensive rebounds are correlated with missed shots
		foul_counter = 0
		fta = 0
		ftm = 0
		pm = 0
		avg_pm = 0
		for time in range(start, finish + 1):
			current_time = seconds_to_timestamp(time)
			try:
				if all([self.event_dictionary[current_time][last_name] == 1, last_name in create_rosters(self, filename)[0]]):
				'''
				creates plus/minus rating for a player
				'''
					pm += self.event_dictionary[current_time][ptsTU]
					pm -= self.event_dictionary[current_time][ptsOpp]
				elif all([self.event_dictionary[current_time][last_name] == 1, last_name in create_rosters(self, filename)[1]]):
					pm += self.event_dictionary[current_time][ptsOpp]
					pm -= self.event_dictionary[current_time][ptsTU]
				n_list = self.get_event_player(last_name, self.event_dictionary[current_time])
				to_freethrow_line = False
				for n in n_list:
					if 'TURNOVR' in (self.event_dictionary[current_time]['event' + str(n)]):
						'''
						counts turnovers
						'''
						to_counter += 1
					elif 'REBOUND' in (self.event_dictionary[current_time]['event' + str(n)]):
						'''
						counts rebounds and off rebound %
						'''
						reb_counter += 1
						if '(OFF)' in (self.event_dictionary[current_time]['event' + str(n)]):
							oreb_counter += 1
					elif not 'FT SHOT' in (self.event_dictionary[current_time]['event' + str(n)]):
						'''
						counts field goals and field goal %
						'''
						if 'GOOD!' in (self.event_dictionary[current_time]['event' + str(n)]):
							fga += 1
							fgm += 1
						elif 'MISSED' in (self.event_dictionary[current_time]['event' + str(n)]):
							fga += 1
					elif 'FT SHOT' in (self.event_dictionary[current_time]['event' + str(n)]):
						'''
						counts number of trips to free-throw line and ft shot %
						'''
						fta += 1
						if (to_freethrow_line == False):
							foul_counter += 1
							to_freethrow_line = True
						if 'GOOD!' in (self.event_dictionary[current_time]['event' + str(n)]):
							ftm += 1
			except KeyError:
				continue
		if fga != 0:
			fg_pct = fgm/fga
		else:
			fg_pct = 0
		if reb_counter != 0:
			oreb_pct = oreb_counter/reb_counter
		else:
			oreb_pct = 0
		if fta != 0:
			ft_pct = ftm/fta
		else:
			ft_pct = 0
		if pm != 0:
			avg_pm = pm/self.possessions(begin_time, end_time, last_name)
		else:
			avg_pm = 0
		if (self.possessions(begin_time, end_time, playername = last_name) > 0):
			'''
			creates four factors for a player
			'''
			factor_list.extend([fga, fg_pct, to_counter/(self.possessions(begin_time, end_time, playername = last_name)/2), oreb_pct, foul_counter, ft_pct])
		else:
			factor_list.extend([fga, fg_pct, 0, oreb_pct, foul_counter, ft_pct])
		factor_array = np.array(factor_list)
		return factor_array
		