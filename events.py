from bs4 import BeautifulSoup
import re
import pandas as pd
from os import listdir

def make_dataset(root, folder, target = 'mydata.csv'):
	for file in listdir(root + folder):
		if (file.endswith('.csv')):
			try:
				df = pd.concat([df, player_triples_with_labels(file[:-4], folder)])
			except NameError:
				df = player_triples_with_labels(file[:-4], folder)
	df.to_csv(target, index=False)
	return df

def get_periods(filename, folder = ''):
	with open(folder + filename + '.html') as file:
		soup = BeautifulSoup(file, "lxml")
	# the following is for the format used in 2017-2018
	table = soup.find_all('font', {'size':'-1'})
	split_table = re.split('------------------------------------------------------------------------------------------------',str(table))
	periods = [re.split('\\n', split_table[1:][i]) for i in range(len(split_table[1:]))]
	# get rid of summary info after period of play
	end_indices = [-1, -1 , -1]
	for i in range(len(periods)):
		for j in range(len(periods[i])):
			if (periods[i][j] == '<hr/>'):
				end_indices[i] = j
				break

	trimmed_periods = [add_period(periods[i][ :end_indices[i]], i + 1) for i in range(len(periods))]  # This is a list of each period of play, with each period of play being a list of lines in play-by-play
	#access the part of the record that is the time
	return trimmed_periods

def get_rows(period_list):

	for i in range(len(period_list)):
		try:
			table_rows = table_rows + period_list[i]
		except:
			if (i == 0):
				table_rows = period_list[i]
	return table_rows

def add_period(period_record, period_num):
 	
 	p = str(period_num) + '-'
 	timestamp_list = []
 	for row in period_record:
 		try:
	 		temp = row.split(get_time(row))[0] + p + get_time(row) + row.split(get_time(row))[1]
	 		timestamp_list.append(temp)
	 	except IndexError:
	 		print("Problem with: " + row)
 	return timestamp_list

def get_time(row, period = False, **kwargs):
	if (len(row) == 0):
		return None
	else:
		z1=''
		z2=''
		per = ''
		try:
			minute = int(re.split(':',row)[0][-2:])
			second = int(re.split(':',row)[1][:2])
			if (period == True):
				per = re.split('-',row)[0][-1:] + '-'
		except ValueError:
			minute = int(re.split(':',row)[1][-2:])
			second = int(re.split(':',row)[2][:2])
			if (period == True):
				per = re.split('-',row)[0][-1:] + '-'
		if (minute < 10):
			z1 = '0'
		if (second < 10):
			z2 = '0'
		return per + z1 + str(minute) + ':' + z2 + str(second)

def row_events_players(row):
	fourpieces = row.split(get_time(row)).split('by')
	# check that there was a (event) _by_ (player)...
	if (len(fourpieces) > 2):
		return fourpieces[0], fourpieces[1], fourpieces[2], fourpieces[3]

def timestamp_to_seconds(periodandtime):
    triple = re.split('-|:',periodandtime)
    try:
        return (int(triple[0])-1)*20*60 + (19 - int(triple[1]))*60 + (60 - int(triple[2])) ## this, if first half is 1-, second half 2-, etc. If first half is 0-, second half 1-, etc, then just use int(triple[0]) instead of int(triple[0])-1.
        # also, this presumes that nothing ever gets recorded at time 20:00
    except IndexError:
        print('Error in the time format')
        return None

def get_event1(row, rows_before, rows_after):
	useit = False # a Boolean that says whether we have found a primary event in this row or not
	foundflag = '' # a string that contains the keyword that told us we found the primary event (and that begins the string that identifies the event)
	event1flags = ['GOOD!', 'MISSED', 'STEAL'] ## possible candidates for the variable foundflag
	alt_event1flags = ['FOUL', 'TURNOVR'] ## conditional candidates for variable foundflag. these events can be primary, but are not always so
	for flag in event1flags:
		if (flag in row):
			if (not 'FT SHOT' in row): ## !!!!!!! May need to change when we include checks for other keywords in event1flags, since assumes 'FT SHOT' never in same row as event1
				useit = True
				foundflag = flag
			elif all([(flag == 'STEAL'), ('TURNOVR' in rows_before[-1]), (timestamp_to_seconds(get_time(row), period = True) - timestamp_to_seconds(get_time(rows_before[-1]), period = True) < 2)]):
				useit = True
				foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0] ## assumes that the flag appears just once in the row
	else:
		for flag in alt_event1flags:
			if all([(get_time(row) != get_time(rows_before[-1])), (flag in row)]):
				if all([(flag == 'FOUL'), any([('GOOD!' not in row), ('MISSED' not in row)])]):
					personal = row.split('(P')[1].split('T')[0]
					team = personal.split('T')[1].split(')')[0]
					p_counter = 'Personal Foul No. ' + personal
					t_counter = 'Team Foul No. ' + team
					useit = True
					foundflag = flag
				elif all([(flag == 'TURNOVR'), ('STEAL' not in row), ('STEAL' not in rows_after[0])]): 
					useit = True
					foundflag = flag
		if (useit):
			return foundflag + row.split(foundflag[1]).split(' by')[0]
		else:
			return None

def get_event2(row, rows_before, rows_after):
	useit = False # a Boolean that says whether we have found a secondary event in this row or not
	foundflag = '' # a string that contains the keyword that told us we found the secondary event (and that begins the string that identifies the event)
	event2flags = ['ASSIST', 'BLOCK'] ## possible candidates for the variable foundflag
	alt_event2flags = ['FOUL', 'REBOUND', 'TURNOVR', 'FT SHOT'] ## conditional candidates for variable foundflag. these events can be secondary, but are not always so
	for flag in event2flags:
		if (flag in row):
			useit = True
			foundflag = flag
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0] ## assumes that the flag appears just once in the row
	else:
		for flag in alt_event2flags:
			if all([(get_time(row) == get_time(rows_before[-1])), (flag in row)]):
				if all([(flag == 'FOUL'), any([('GOOD!' in rows_before[-1]), ('MISSED' in rows_before[-1]), ('TURNOVR' in rows_before[-1])])]): #account for potential of good FG with assist
					personal = row.split('(P')[1].split('T')[0]
					team = personal.split('T')[1].split(')')[0]
					p_counter = 'Personal Foul No. ' + personal
					t_counter = 'Team Foul No. ' + team
					useit = True
					foundflag = flag
				elif all([(flag == 'REBOUND'), any([('MISSED FT SHOT' not in rows_before[-1]), ('MISSED FT SHOT' not in row)])]): # !!! check to see if this statement holds as expected
					reb_type = row.split('(')[1].split(')')[0]
					useit = True
					foundflag = flag + '(' + reb_type + ')'
			elif (flag == 'TURNOVR'):
				if ('STEAL' in row):
					useit = True
					foundflag = flag
				elif all([('STEAL' in rows_after[0]), (timestamp_to_seconds(get_time(rows_after[0]), period = True) - timestamp_to_seconds(get_time(row), period = True) == 1)]):
					useit = True
					foundflag = flag
			elif all([(flag == 'FT SHOT'), (timestamp_to_seconds(get_time(rows_before[-1]), period = True) != timestamp_to_seconds(get_time(row), period = True))]):
				useit = True
				foundflag = flag
		if (useit):
			return foundflag + row.split(foundflag[1]).split(' by')[0]
		else:
			return None

def get_event3(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event3flags = ['FT SHOT', 'REBOUND', 'FOUL']
	for flag in event3flags:
		if all([(get_time(row) == get_time(rows_before[-1])), (flag in row)]):
			if (flag == 'FT SHOT'):
				if all([('FOUL' in row), any([('GOOD!' in rows_before[-1]), ('ASSIST' in rows_before[-1])]), ('FT SHOT' not in rows_before[-1])]):
					## want some way to indicate that a first FT shot can be a tertiary event or that a second FT shot can be a tertiary event
					## possible scenarios for (1):
						## (a) good unassisted shot, foul, first -- and only -- FT shot
						## (b) missed shot, foul, first FT shot
					## possible scenarios for (2):
						## (a) foul, first FT shot, second FT shot
					useit = True
					foundflag = flag
				if all(('FOUL' in row), ('MISSED' in rows_before[-1]), ('FT SHOT' not in rows_before[-1])):
					useit = True
					foundflag = flag
			elif (flag == 'REBOUND'):
				if all([('FOUL' in rows_before[-1]), ('MISSED FT SHOT' in rows_before[-1]), (get_time(rows_before[-2]) != get_time(rows_before[-1]))]):
					reb_type = row.split('(')[1].split(')')[0]
					useit = True
					foundflag = flag + '(' + reb_type + ')'
			elif (flag == 'FOUL'):
				if ('ASSIST' in rows_before[-1]):
					useit = True
					foundflag = flag
				elif any([all([('TURNOVR' in rows_before[-1]), ('STEAL' in rows_before[-1])]), all([('TURNOVR' in rows_before[-2]), ('STEAL' in rows_before[-1])])]):
					useit = True
					foundflag = flag
		elif all([(flag == 'FT SHOT'), ('FOUL' in rows_before[-1]), ('GOOD! FT SHOT' in rows_before[-1]), (get_time(row) != get_time(rows_before[-2]))]):
			useit = True
			foundflag = flag
		elif all([(flag == 'REBOUND'), ('BLOCK' in rows_before[-1]), (timestamp_to_seconds(get_time(row), period = True) - timestamp_to_seconds(get_time(rows_before[-1]), period = True) < 3)]): ## !!! add this check outside of the current if block (also for steals + turnovers)
		## for some reason, each rebound after a blocked shot is recorded as happening 2 seconds after the initial shot
			reb_type = row.split('(')[1].split(')')[0]
			useit = True
			foundflag = flag + '(' + reb_type + ')'
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_event4(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event4flags = ['GOOD! FT SHOT', 'MISSED FT SHOT', 'REBOUND']
	for flag in event4flags:
		if all([(flag in row), (get_time(row) == get_time(rows_before[-1]))]):
			## possible scenarios for first FT shot to be quaternary event:
				## (a) good shot, assist, foul, first -- and only -- FT shot
			## possible scenarios for second FT shot to be quaternary event:
				## (a) good unassisted shot, foul, first FT shot, second FT shot
				## (b) missed shot, foul, first FT, second FT shot
			if (flag == 'GOOD! FT SHOT'):
				if all([('FOUL' in row), ('ASSIST' in rows_before[-1])]):
					useit = True
					foundflag = flag
			elif (flag == 'MISSED FT SHOT'):
				if all([('FOUL' in row), ('ASSIST' in rows_before[-1])]):
					useit = True
					foundflag = flag
				elif all([any([('GOOD! FT SHOT' in rows_before[-1]), ('MISSED FT SHOT' in rows_before[-1])]), ('MISSED' in rows_before[-2])]):
					useit = True
					foundflag = flag
			elif (flag == 'REBOUND'):
				if all([any([('MISSED FT SHOT' in row), ('MISSED FT SHOT' in rows_before[-1])]), ('FOUL' in rows_before[-1]), any([(get_time(row) != get_time(rows_before[-2])), (get_time(row) != get_time(rows_before[-3]))])]): ## foul is primary event, second free throw is missed, rebound occurs
					reb_type = row.split('(')[1].split(')')[0]
					useit = True
					foundflag = flag + '(' + reb_type + ')'
				elif all([any([all([('FOUL' in rows_before[-1]), ('MISSED FT SHOT' in rows_before[-1])]), all([('FOUL' in rows_before[-2]), ('MISSED FT SHOT' in rows_before[-2])])]), any([all([('GOOD!' in rows_before[-2]), ('FT SHOT' not in rows_before[-2])]), all([('GOOD!' in rows_before[-3]), ('FT SHOT' not in rows_before[-3])])])]): # good FG, foul, missed FT shot, rebound
					reb_type = row.split('(')[1].split(')')[0]
					useit = True
					foundflag = flag + '(' + reb_type + ')'
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_event5(row, rows_before, rows_after):
	useit = False
	foundflag = ''
	event5flags = ['REBOUND']
	for flag in event5flags:
		if all([(flag in row), (get_time(row) == get_time(rows_before[-1]))]):
			if (flag == 'REBOUND'):
				## good FG, foul, one FT shot where it misses
				if all([('MISSED FT SHOT' in rows_before[-1]), ('FOUL' in rows_before[-1]), ('ASSIST' in rows_before[-2])]):
					## would it be helpful to see if the time in the row after is not equivalent to the time in the row being evaluated?
					reb_type = row.split('(')[1].split(')')
					useit = True
					foundflag = flag + '(' + reb_type + ')'
				## missed FG, foul, two FT shots where the second one misses; need to include exception for FT shot in third portion of condition. maybe `and 'FT SHOT' not in rows_before[-2/-3]` added to the end?
				elif all([any([('MISSED FT SHOT' in row), ('MISSED FT SHOT' in rows_before[-1])]), any([('GOOD! FT SHOT' in rows_before[-1]), ('GOOD! FT SHOT' in rows_before[-2])]), any([all([('MISSED' in rows_before[-2]), ('FT SHOT' not in rows_before[-2])]), ('MISSED' in rows_before[-3])])]):
					reb_type = row.split('(')[1].split(')')
					useit = True
					foundflag = flag + '(' + reb_type + ')'
				elif all([any([('MISSED FT SHOT' in row), ('MISSED FT SHOT' in rows_before[-1])]), any([('MISSED FT SHOT' in rows_before[-1]) ('MISSED FT SHOT' in rows_before[-2])]), any([all([('MISSED' in rows_before[-2]), ('FT SHOT' not in rows_before[-2])]), ('MISSED' in rows_before[-3])])]):
					reb_type = row.split('(')[1].split(')')
					useit = True
					foundflag = flag + '(' + reb_type + ')'
	if (useit):
		return (foundflag + row.split(foundflag)[1]).split(' by')[0]
	else:
		return None

def get_player(row, event):
	player = row.split(event + ' by ')[1]
	last_name = player.split(',')[0]
	return last_name

## what about 3 point FT shots? they're rare, but they happen
## make sure to dump anything that looks like it isn't an event (e.g., substitutions) and place in separate file
## if concerned about miscategorization, then look through spreadsheet manually for verification