from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
from quickselect import *
import os

def create_eventdictionary(filename, hometeam, folder = ''):
	'''
	creates the dictionary that stores all events; keys of event dictionary are timestamps
	'''
	edictionary = {} # the dictionary to return; keys will be timestamps
	preamble, allrows = get_rows(filename, folder) # make the total list of rows -- each is a string
	print(allrows[len(allrows) - 1])
	eventfcns = [get_event1, get_event2, get_event3, get_event4, get_event5] # the functions that will populate the events columns
	for i in range(len(allrows)):
		# for key == (timestamp of this row), set edictionary to be a dictionary with just SUB IN, SUB OUT, TIMEOUT keys and empty strings
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
				### this has created a list of length 3 containing the 3 previous rows (if none of them have (DEADBALL), SUB, TIMEOUT and there are 3 previous rows)
				### if some of those things don't hold then it puts the string 0-20:00 in the spot in the list
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
				### the same, but with the 3 rows after current row
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
		# for to_type in ['30sec', 'MEDIA', 'media', 'TEAM']: ##!!!!! doesn't quite work the way I want it to... 
		if 'TIMEOUT' in allrows[i]:
			edictionary[get_time(allrows[i], period=True)]['TIMEOUT'] = get_timeout(allrows[i])
		# record in two columns the number of points scored in this event, for each side <-- implement this, doesn't seem to work right now
		if (event):
			if ('ptsTU' in edictionary[get_time(allrows[i], period=True)].keys()): # eventfcn is picking up each FT SHOT in 01:32 twice
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
		elif('ptsTU' in edictionary[get_time(allrows[i], period=True)].keys()):
			pass
		else:
			edictionary[get_time(allrows[i], period=True)]['ptsTU'] = 0
			edictionary[get_time(allrows[i], period=True)]['ptsOpp'] = 0
	# at this point, program has gone through every row and filled in events, players, subs, and points
		for j in range(5):
			if (not 'event' + str(j+1) in edictionary[get_time(allrows[i], period=True)].keys()):
				edictionary[get_time(allrows[i], period=True)]['event' + str(j+1)] = ''
			if (not 'player' + str(j+1) in edictionary[get_time(allrows[i], period=True)].keys()):
				edictionary[get_time(allrows[i], period=True)]['player' + str(j+1)] = ''
	
	# setofplayers is the list of all players that were recorded as being involved in a play throughout the whole game ### I THINK WE CAN SIMPLY USE THE ROSTER NOW
	# make a column for each player in game (before), put a 1 in this row if they are in, a 0 otherwise
	rosters = create_rosters(filename)
	for playername in rosters[0]:
		edictionary = add_playtimes(edictionary, playername, preamble) ## puts the zeros and ones ('not in' and 'in') into a column for that player
	for playername in rosters[1]:
		edictionary = add_playtimes(edictionary, playername, preamble)

	return edictionary

def get_rows(filename, folder = ''):
	'''
	generates teh rows of the play-by-play data
	'''
	with open(folder + filename + '.html') as file:
		soup = BeautifulSoup(file, "lxml")
	# the following is for the format used in 2017-2018
	preamble = str(soup.find_all('pre')[0])
	table = soup.find_all('font', {'size':'-1'})
	split_table = re.split('------------------------------------------------------------------------------------------------',str(table))
	## Danger: some versions of Python may need something besides '\\n' here...
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
	gets players subbed in and subbed out of the game
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
	grabs timeout type (30 second, media, team)
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
	adds the period number in front of each timestamp (e.g., timestamps with '1-' in front are timestamps in the first half)
	'''
	p = str(num_period) + '-'
	newlist = []
	for row in row_list:
		try:
			newlist.append( row.split(get_time(row))[0] + p + get_time(row) + row.split(get_time(row))[1] )
		except IndexError:
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
		return (int(triple[0])-1)*20*60 + (19 - int(triple[1]))*60 + (60 - int(triple[2])) + int(triple[0])-1 ## this, if first half is 1-, second half 2-, etc. If first half is 0-, second half 1-, etc, then just use int(triple[0]) instead of int(triple[0])-1.
	except IndexError:
		print('Error in the time format')
		return None

def seconds_to_timestamp(secs):
	'''
	converts seconds (type int) to timestamps (type str)
	'''
	if secs < 1201:
		period = 1
	elif secs < 2402:
		period = 2
	else:
		period = 3
	minutes = 19 - int((secs - (period-1)*20*60 - (period-1))/60)
	seconds = secs - (period-1)*20*60 - (period-1) - (19 - minutes)*60
	if (seconds == 0): 
		minutes = minutes + 1
		seconds = 60
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
		if (all([pname in row, any(['. f' in row, '. g' in row, '. *' in row, '. c' in row])])):
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

# the following functions (get_event1, get_event2, ..., get_event6) grab events in each play row-by-row and categorizes them...
# ...in the order in which they occur
# they all have the same structure: first goes through the eventAflags list, then goes theough alt_eventAflags list
# there can be as few as 1 event in a play (e.g., MISSED 3 PTR)
# there can be as many as 6 events in a play (e.g., MISSED 3 PTR, FOUL, GOOD!/MISSED FT SHOT (x2), MISSED FT SHOT, REBOUND)

def get_event1(row, rows_before, rows_after):
	useit = False # a Boolean that says whether we have found a primary event in this row or not
	foundflag = '' # a string that contains the keyword that told us we found the primary event (and that begins the string that identifies the event)
	event1flags = ['GOOD!', 'MISSED', 'STEAL'] ## possible candidates for the variable foundflag
	alt_event1flags = ['FOUL', 'TURNOVR'] ## conditional candidates for the variable foundflag (not always a primary event)
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
		return (foundflag + row.split(foundflag)[1]).split(' by')[0] ## assumes that the flag appears just once in the row
	else:
		for flag in alt_event2flags:
			if (flag in row):
				if (get_time(row) == get_time(rows_before[-1])):
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
					elif all([flag == 'REBOUND', not 'MISSED FT SHOT' in rows_before[-1], not 'MISSED FT SHOT' in row]): ## -- CC comment -- does this need to be all??
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
			try:
				return (foundflag + row.split(foundflag)[1]).split(' by')[0]
			except:
				# This hopefully doesn't happen
				print('Happens?')
				print((row, foundflag))
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
						## for some reason, each rebound after a blocked shot is recorded as happening 2 seconds after the initial shot
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
			if all([(flag == 'REBOUND'), ('BLOCK' in rows_before[-1]), (timestamp_to_seconds(get_time(row, period = True)) - timestamp_to_seconds(get_time(rows_before[-1], period = True)) < 3)]):
			## for some reason, each rebound after a blocked shot is recorded as happening 2 seconds after the initial shot
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
	if ' ' in last_name:
		last_name = last_name.split(' ')[0] + ' ' + last_name.split(' ')[1]
	return last_name

def get_pts(row, thisrow_event, homevisitor):
	'''
	counts the points a team scores in a play
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

def mark_conf_games(path):
	'''
	modifies file names of conference games
	'''
	caa_teams = ['Col. of Charleston', 'Delaware', 'Drexel', 'Elon', 'Hofstra', 'James Madison', 'Northeastern', 'UNCW', 'William & Mary']
	for filename in os.listdir(path):
		if 'c_' != filename[:2]:
			for team in caa_teams:
				if team in filename:
					# rename the file for those that were conference games
					os.renames((path+filename), (path+'c_' + filename))
				else:
					continue
	return None

def get_best(pt_list, topn=1, fcn='sum', wts=[]):
	# returns the sublist of pt_list containing the topn elements with highest value under fcn
	# fcn refers to some function that takes the coordinates/features of element in pt_list and outputs a number
	return_list = []
	fcn_values = []
	lengths=[len(p) for p in pt_list]
	try:
		assert min(lengths)==max(lengths)
		n = lengths[0]
		if type(fcn)==int:
			# when user passes an int, the function picks out that coordinate
			try:
				assert all([fcn>-1, fcn<n])
				fcn_values = np.array(pt_list)[:,fcn]
			except AssertionError:
				print('Input error. Parameter \'fcn\' not in range of coordinates.')
				return None
		elif type(fcn)==str:
			# when user passes a string, there are a few pre-made functions on the point set that are defined
			if fcn=='sum':
				fcn_values = np.array([sum(p) for p in pt_list])
			elif fcn=='weighted_sum':
				try:
					fcn_values = np.array([sum([wts[i]*p[i] for i in range(n)]) for p in pt_list])
				except:
					print('Input error. Weights array was not correctly defined, but \'fcn\' was set to \'weighted_sum\'.')
					return None
		else:
			print('Input error. Invalid type for \'fcn\'.')
			return None
		if (len(fcn_values)>0):
			cutoff = quickSelect(fcn_values, len(pt_list)-topn+1)
			for i in range(len(pt_list)):
				if not(fcn_values[i]<cutoff):
					return_list.append(np.array(pt_list[i]))
			# WARNING: the defined return_list might be longer than topn if there are points with the same fcn_values
			return np.array(return_list)
		else:
			return np.array(return_list)
	except AssertionError:
		print('Input error. Some data points have too many/too few features.')
		return None

def create_rosters(filename):
	'''
	creates home and away rosters
	'''
	team_summaries = re.split('\\n\\n\\n',get_rows(filename)[0])[:2]
	for ts in team_summaries:
		# do we want to keep this as home/away or change to TU/opponent?
	    if 'VISITORS' in ts:
	        away_roster = []
	        lines = re.split('\\n', ts)
	        for l in lines:
	            try:
	                int(l[:2])
	                if (l[2] ==' '):
	                    away_roster.append(re.split(',',l[3:])[0].split('..')[0])
	            except ValueError:
	                pass
	    if 'HOME TEAM' in ts:
	        home_roster = []
	        lines = re.split('\\n', ts)
	        for l in lines:
	            try:
	                int(l[:2])
	                if (l[2] ==' '):
	                    home_roster.append(re.split(',.',l[3:])[0].split('..')[0])
	            except ValueError:
	                pass
	return home_roster, away_roster
	
class FourFactors:
	'''
	construction of the Four Factors profiles and other computations
	'''
	# dev note: if name of opposing team is wanted for later, we'll need to change if home_team/else block
	def __init__(self, filename):
		print('Creating FourFactors class for game: ' + filename)
		home_team = get_rows(filename)[0].split('vs ')[1][:6]
		if home_team == 'Towson':
			home_team = 'TU'
		else:
			home_team = 'Opp'
		if 'SECU Arena' in filename:
			# location of this string varies in each file name
			self.towson_is_home = True
		else:
			self.towson_is_home = False
		if (self.towson_is_home != (home_team=='TU')):
			print('Warning. The home_team variable does not agree with self.towson_is_home for game '+filename)
		self.name = filename
		self.event_dictionary = create_eventdictionary(filename, home_team)
		self.home_roster, self.away_roster = create_rosters(filename)
		self.total_poss = self.possessions('1-20:00', '2-00:00')

	def event_which(self, evt, time):
		'''
		returns an int or array of ints, the number of the event (or None if evt did not occur)
		event is a string describing a possible event at that time (e.g. 'TURNOVR'); time is the timestamp to look at
		'''
		result = None
		try:
			play = self.event_dictionary[time]
			occurred = self.helper(evt, play)
			if occurred:
				for k in play.keys():
					if 'event' in k:
						if evt in play[k]:
							if type(result)==int:
								result = [result]
								result.append(int(k[-1:]))
							elif type(result)==list:
									result.append(int(k[-1:]))
							else:
								result = int(k[-1:])
			else:
				print('Event did not occur at specified time.')
		except KeyError:
			print('No event occurred at the time entered.')
		
		return result

	def event_occurred(self, evt, time):
		'''
		returns a boolean, if event happened at time
		event is a string describing a possible event at that time (e.g. 'TURNOVR'); time is the timestamp to look at
		'''
		result = None
		try:
			result = self.helper(evt, self.event_dictionary[time])
		except KeyError:
			print('No event occurred at the time entered.')
		return result

	def helper(self, s, play):
		'''
		play is an entry in self.event_dictionary; looks into the various 'event's and figures out if s has happened (s is a string)
		'''
		found = False
		for k in play.keys():
			if 'event' in k:
				if (s in play[k]):
					found = True
		return found

	def get_event_player(self, name, play):
		'''
		finds the integer after 'player' keys where player appears (e.g., if SMITH is passed in and appears in...
		...keys 'player2' and 'player3', this function returns [2, 3])
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

	def get_oncourt_players(self, time, homeaway):
		'''
		returns list of last names of the players on the court at 'time'
	    '''
	    output_list=[]
	    for k in self.event_dictionary[time].keys():
	        if any([all([homeaway=='home', k in self.home_roster, self.event_dictionary[time][k]==1]), all([homeaway=='away',k in self.away_roster, self.event_dictionary[time][k]==1])]):
	            output_list.append(k)
	    return output_list

	def check_subs(self, time):
		'''
		returns boolean which says whether or not a substitution occurred at 'time'
		'''
		return max(len(self.event_dictionary[time]['SUB IN ']),len(self.event_dictionary[time]['SUB OUT']))>0

	def subtimes(self, homeaway='home'):
		'''
		records times when substitutions happened
		'''
		times = self.valid_times()
		return_times = [times[0]]
		last_event_time = times[len(times)-1]
		try:
			assert self.check_subs(return_times[0])==False
		except AssertionError:
			print('A substitution occurred before any event in the game')
		for t in times:
			if self.check_subs(t):
				if homeaway=='home':
					for player in self.home_roster:
						if player in self.event_dictionary[t]['SUB IN ']:
							return_times.append(t)
							break
				else:
					for player in self.away_roster:
						if player in self.event_dictionary[t]['SUB IN ']:
							return_times.append(t)
							break
			else:
				continue
		return return_times

	def lineup_pt(self, time, fcn, team='TU', depth=2, center='mean', leadin=0):
		# first determine homeaway variable
		# fcn: 0=fga; 1=fgp; 2=to/poss; 3=oreb_pct; 4=foul_counter; 5=ftp. Also possible: 'sum', 'weighted_sum'
		prevtime = ''
		pts = []
		if any([all([team=='TU',self.towson_is_home]),all([not(team=='TU'),not(self.towson_is_home)])]):
			ha = 'home'
		else:
			ha = 'away'
		subtimes = self.subtimes(ha)
		for i in range(len(subtimes)):
			if time == subtimes[i]:
				try:
					assert subtimes[i-1][0]==subtimes[i][0]
					prevtime = subtimes[i-1]
				except:
					prevtime = time[0] + '-20:00'
				break
			else:
				continue
		for p in self.get_oncourt_players(time, ha):
			pts.append(self.four_factors(seconds_to_timestamp(max(timestamp_to_seconds(prevtime)-leadin, 0)), time, p))
		best_pts = get_best(pts, topn=depth, fcn=fcn)
		if center=='mean':
			return np.mean(best_pts, axis=0)
		else:
			return None

	def combo_pt(self, players, start_time, end_time, center='mean'):
		pts = []
		for p in players:
			pts.append(self.four_factors(start_time, end_time, p))
		if center=='mean':
			return np.mean(pts, axis=0)
		else:
			return None

	def combo_pts(self, players, t_bound=60, center='mean', team='TU'):
		combo_on = False
		t_start = ''
		timeints = []
		if any([all([team=='TU',self.towson_is_home]),all([not(team=='TU'),not(self.towson_is_home)])]):
			ha = 'home'
		else:
			ha = 'away'
		for t in self.valid_times():
			if all([p in self.get_oncourt_players(t,ha) for p in players]):
				if not(combo_on):
					combo_on = True
					t_start = t
			elif combo_on:
				combo_on=False
				if timestamp_to_seconds(t) - timestamp_to_seconds(t_start) > t_bound:
					timeints.append([t_start, t])
		return timeints

	def four_factors(self, begin_time, end_time, last_name):
		'''
		computes four factors statistics for each player in a time interval
		'''
		start = timestamp_to_seconds(begin_time)
		finish = timestamp_to_seconds(end_time)
		# factor_dictionary = {edictionary.keys()}
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
				if all([self.event_dictionary[current_time][last_name] == 1, last_name in self.home_roster]):
					pm += self.event_dictionary[current_time]['ptsTU']
					pm -= self.event_dictionary[current_time]['ptsOpp']
				elif all([self.event_dictionary[current_time][last_name] == 1, last_name in self.away_roster]):
					pm += self.event_dictionary[current_time]['ptsOpp']
					pm -= self.event_dictionary[current_time]['ptsTU']
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
			avg_pm = pm/max([self.possessions(begin_time, end_time, last_name),1])
		else:
			avg_pm = 0
		if (self.possessions(begin_time, end_time, playername = last_name) > 0):
			factor_list.extend([fga, fg_pct, to_counter/(self.possessions(begin_time, end_time, playername = last_name)/(2.0)), oreb_pct, foul_counter, ft_pct])
		else:
			factor_list.extend([fga, fg_pct, 0, oreb_pct, foul_counter, ft_pct])
		factor_array = np.array(factor_list)
		return factor_array

	def point_spread(self, begin_time, end_time, last_name=''):
		'''
		computes plus/minus over a time interval when a certain player is on the court
		'''
		start = timestamp_to_seconds(begin_time)
		finish = timestamp_to_seconds(end_time)
		TU_pts = 0
		opp_pts = 0
		for time in range(start, finish + 1):
			current_time = seconds_to_timestamp(time)
			try:
				if len(last_name)>0:
					if self.event_dictionary[current_time][last_name] == 1:
						TU_pts += self.event_dictionary[current_time]['ptsTU']
						opp_pts += self.event_dictionary[current_time]['ptsOpp']
				else:
					TU_pts += self.event_dictionary[current_time]['ptsTU']
					opp_pts += self.event_dictionary[current_time]['ptsOpp']
			except KeyError:
				continue
		tu_spread = TU_pts - opp_pts
		return tu_spread

	def valid_times(self):
		'''
		returns the list of all valid timestamps, in the correct order, for the class
		'''
		unordered = list(self.event_dictionary.keys())
		firsthalf = []
		secondhalf = []
		overtime = []
		for ts in unordered:
			if '1' == ts[0]:
				firsthalf.append(ts)
			elif '2' == ts[0]:
				secondhalf.append(ts)
			else:
				overtime.append(ts)
		if len(overtime)>0:
			ordered = np.concatenate((np.sort(firsthalf)[::-1], np.sort(secondhalf)[::-1], np.sort(overtime)))
		else:
			ordered = np.concatenate((np.sort(firsthalf)[::-1], np.sort(secondhalf)[::-1]))
		return ordered