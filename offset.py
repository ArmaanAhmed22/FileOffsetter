#!/usr/bin/env python3
import re
import os
import argparse

offset_signal = "\[(\d+|)#\]"

#From https://stackoverflow.com/a/17303428
class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def parseArgs():
	parser = argparse.ArgumentParser(description="Offseter renaming tool for files")
	parser.add_argument("--input","-i",help="Path where files to be offset are stored")
	parser.add_argument("--match","-m",help="File name to match to (Regex). Use '[#]' (with an optional number in front) to indicate the number you want to offset. The number, n, indicates you want to offset the nth digit. Eg hello_world_[2#] indicates you want to offset the tens place of the number right after 'hello_word_' file name. Note... use '\\\\' instead of '\\'",nargs="+")
	parser.add_argument("--offset","-o",help="The offset amount. Use, where 'n' is the offset amount 'n' or '-n' to indicate the offset amount and direction")
	parser.add_argument("--allow-partial","-p",help="Allow for partial match. Essentially doesn't need the 'match' to start from the beginning",action="store_true")
	parser.add_argument("--log","-l",help="Creates a log in the 'input' directory",action="store_true")
	args = parser.parse_args()

	if args.match == None or args.input == None or args.offset == None:
		raise Exception("--math, --offset, and --input command line arguments are necessary")

	args.match = " ".join(args.match)
	args.offset = int(args.offset)
	return args

def matchSpecification():
	num = len(re.findall(offset_signal,args.match))
	if num <= 1:
		return [args.offset for _ in range(num)]
	else:
		answer = input(f"Would you like to change the offset (globally {args.offset}) of some specific regions? (y/N)\n> ")
		offsets = []
		if answer == "y":
			print("\nPress 'Enter' if you want to keep that match offset the same as the global value\n")
			for i in range(num):
				offset = input(f"{i+1}: ")
				if offset == "":
					offset = args.offset
				else:
					offset = int(offset)
				offsets.append(offset)
			return offsets
		else:
			return [args.offset for _ in range(num)]

def listFiles():
	file_names = []
	for file_name in next(os.walk(args.input))[2]:
		if not file_name[0] == ".":
			file_names.append(file_name)
	num_to_display = min(len(file_names),5)
	slash_n = "\n"
	print("Directory: "+color.BOLD+args.input+color.END)
	answer = input(f"These are the top files in the directory: \n{slash_n.join([color.BOLD+'* '+color.RED+file_name+color.END for file_name in file_names[:num_to_display]])}\nIs this correct (N/y)? ")
	if answer == "N":
		print(f"Old path: {color.BOLD+args.input+color.END}")
		args.input = input(f"New path: "+color.BOLD)
		print(color.END)
		listFiles()
	else:
		return file_names

def filterFiles(files,recursive=False,log_list_filtered=[]):
	cur_filtered = []
	if not recursive:
		modified_files_list = []
		modified_match_pattern = re.sub(offset_signal,"`",args.match)
		modified_match_pattern = modified_match_pattern.replace("`", "\d+")
		for file in files:
			init_search = re.search(("^" if not args.allow_partial else "")+modified_match_pattern, file)
			if not init_search is None:
				modified_files_list.append(file)
			else:
				print("TRASHED")
				cur_filtered.append(file)
		log_list_filtered.append(cur_filtered)
	else:
		modified_files_list = files
	answer = input("Would you like to filter the files by the match region range (N/y)?\n> ")
	if answer == "y":
		numbered_matches = " ".join(["" for _ in args.match])
		lower_bound = 0
		match_to_pos_and_exp = {}
		for i,match in enumerate(re.finditer(offset_signal,args.match)):
			digit_portion_str = match.group()[1:-2]
			match_to_pos_and_exp[i+1] = (match.span(),1 if len(digit_portion_str) == 0 else int(digit_portion_str))
			assign = (match.span()[0]+match.span()[1]-1)//2
			numbered_matches = numbered_matches[:assign]+str(i+1)+numbered_matches[assign+1:]
		print(args.match+"\n"+color.RED+color.BOLD+numbered_matches+color.END)
		to_restrict = int(input("Match to restrict: "+color.RED+color.BOLD))
		cur_lower_span = match_to_pos_and_exp[to_restrict][0][0]
		to_restrict_in_effect = -1
		for it_match in range(to_restrict-1,0,-1):
			print(f"LOWER: {cur_lower_span}")
			print(f"HIGHER: {match_to_pos_and_exp[it_match][0][1]}")
			if match_to_pos_and_exp[it_match][0][1] == cur_lower_span:
				cur_lower_span = match_to_pos_and_exp[it_match][0][0]
				if it_match == 1:
					to_restrict_in_effect = it_match
			else:
				to_restrict_in_effect = it_match
				break
		print(color.END,end=f"NEW: {to_restrict_in_effect}")
		lower = int(input("Lower bound (0-9): "))
		upper = int(input("Upper bound (0-9): "))

		
		modified_match_pattern = re.sub(offset_signal,"`",args.match[:match_to_pos_and_exp[to_restrict_in_effect][0][0]])
		modified_match_pattern = modified_match_pattern.replace("`", "\d+")
		new_modified_files_list = []
		cur_filtered = []
		for file in modified_files_list:
			search_to_match = re.search(modified_match_pattern,file)
			if not search_to_match is None:
				num_to_check = int(re.search("^\d+",file[search_to_match.span()[1]:]).group())
				digit = match_to_pos_and_exp[to_restrict][1]
				digit_to_check = (num_to_check % (10**(digit))) // (10**(digit-1))
				if lower <= digit_to_check and upper >= digit_to_check:
					new_modified_files_list.append(file)
				else:
					cur_filtered.append(file)
		log_list_filtered.append(cur_filtered)
		return filterFiles(new_modified_files_list,recursive=True,log_list_filtered=log_list_filtered)
	else:
		return [modified_files_list,log_list_filtered]

def matchAndRename(files,offsets):
	# Repetition, makes me sad :(
	changes = {}
	modified_match_pattern = re.sub(offset_signal,"`",args.match)
	modified_match_pattern = modified_match_pattern.replace("`", "\d+")
	iter_length = sum([1 for i in re.finditer(offset_signal,args.match)])
	file_modified = 0
	for file in files:
		init_search = re.search(("^" if not args.allow_partial else "")+modified_match_pattern, file)
		if not init_search is None:
			file_modified+=1
			cur_pattern = "^"+file[:init_search.span()[0]]
			cur_num = None
			unmodified_num = 0
			lower_bound = 0
			new_file_name = ""
			iteration = re.finditer(offset_signal,args.match)
			for cur_match,i in enumerate(iteration):
				if cur_num is None:
					cur_pattern += args.match[lower_bound:i.span()[0]]
					new_file_name = re.search(cur_pattern,file).group()
					cur_num = int(re.search(f"(?<={cur_pattern})\d+",file).group())
					unmodified_num = cur_num
				elif not (lower_bound == i.span()[0]):
					cur_pattern+=str(unmodified_num)
					new_file_name+=str(cur_num)
					new_file_name+=re.search(f"(?<={cur_pattern}){args.match[lower_bound:i.span()[0]]}",file).group()
					cur_pattern += args.match[lower_bound:i.span()[0]]
					cur_num = int(re.search(f"(?<={cur_pattern})\d+",file).group())
					unmodified_num = cur_num
				lower_bound = i.span()[1]

				exponent = -1
				if args.match[i.span()[0]+1] == "#":
					exponent = 0
				else:
					exponent = int(re.search("(?<=\[)\d+",args.match[i.span()[0]:i.span()[1]]).group()) - 1
				cur_num+=offsets[cur_match]*10**exponent
				if iter_length - 1 == cur_match:
					new_file_name+=str(cur_num)
					cur_pattern+=str(unmodified_num)
					new_file_name+=re.search(f"(?<={cur_pattern}).+",file).group()
			os.rename(os.path.join(args.input,file),os.path.join(args.input,new_file_name))
			changes[file] = new_file_name
	print(color.BOLD+f"SUMMARY: {file_modified} files modified"+color.END)
	return changes
def create_log(changes,log_list_filtered):
	with open("log.txt",mode="w") as handle:
		filter_write = "FILTERING: "
		for i,filter_round in enumerate(log_list_filtered):
			filter_write+="\n\tROUND "+str(i+1)+"\n"+"\t"+"\n\t".join([filtered_file for filtered_file in filter_round])+"\n\n"

		changes_write = "CHANGES:\n" +"\t"+ "\n\t".join([f"{k} -> {v}" for k,v in changes.items()])
		handle.write(filter_write+changes_write)
	print(color.BOLD+"LOG CREATED"+color.END)





args = parseArgs()
offsets = matchSpecification()
files = listFiles()
filtered_files,log_list_filtered = filterFiles(files)
filtered_files.sort()
changes_to_name = matchAndRename(filtered_files,offsets)
if args.log:
	create_log(changes_to_name,log_list_filtered)

