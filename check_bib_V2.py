import yaml
import pybtex
import pybtex.database.input.bibtex
import re
import sys
import io
import os
from pathlib import Path

def pull_entry(file_in):
    '''
    Extracts the 'entries' data from a dictionary if it exists.
    Args:
        file_in (dict): A dictionary from which to pull the 'entries' data.
    Returns:
        dict: The 'entries' data if it exists, otherwise the original dictionary.
    '''
    # Checks if 'entries' key is in the dictionary.
    if 'entries' in file_in:
        # If 'entries' key exists, returns its value.
        return file_in.get('entries')
    else:
        # If 'entries' key does not exist, returns the original dictionary.
        return file_in

    
def is_yaml_open(filename):
    """
    This function takes a filename as input and returns the data in the file if it is a valid YAML file.
    :param filename: The name of the file to be opened.
    :return: The data in the file if it is a valid YAML file. Otherwise, False.
    """
    try:
        with open(filename, 'r') as f:
            yaml_data = yaml.safe_load(f) # Loading the YAML data
        return yaml_data
    except yaml.YAMLError:
        return False # If the file is not a valid YAML file


def dict_invertion(data_dic,key_wanted='title'):
    """
    This function takes a dictionary as input and returns a new dictionary where the values of the original dictionary are keys and the keys are values.
    :param data_dic: The dictionary to be inverted.
    :param key_wanted: The key to be used as value in the new dictionary. Default is 'title'.
    :return: A new dictionary where the values of the original dictionary are keys and the keys are values.
    """
    result = {normalize(value[key_wanted]): key for key, value in data_dic.items()} # Inverting the dictionary
    return result


def normalize(s):
    """
    Normalize a string by removing non-alphanumeric characters and converting it to lower case.

    :param s: The string to normalize.
    :return: The normalized string.
    """
    return re.sub(r'\W+', '', s).lower()


def diff_list_dic(list1: list, list2: list) -> bool:
    """
    Compare two lists and return whether they are equal.

    :param list1: First list.
    :param list2: Second list.
    :return: True if the lists are equal, False otherwise.
    """
    diff = [i for i in list1 + list2 if i not in list1 or i not in list2]
    return len(diff) == 0



def author_name_equivalence(entry):# TODO: we need to find a better way to do this since some names are -- or people with 15 middle names 
    """
    This function takes an entry name and returns a dictionary of author name equivalence ( n and n.).
    The dictionary maps each last name to a list of possible first name initials.

    Parameters:
        entry (dict): A dictionary representing an entry in a YAML file.

    Returns:
        dict: A dictionary mapping last names to a list of possible first name initials.
    """
    list_equivalence = {}
    for author in entry['author']:
        #print(author)
        last_name = author['last']
        list_equivalence[last_name] = [author['first'][0]]
        list_equivalence[last_name] += [author['first'][0] + '.']
        if  'middle' in author:# This may no work for exoctic names
            list_equivalence[last_name] = [author['middle'][0]]
            list_equivalence[last_name] += [author['middle'][0] + '.']  
    #print(type(list_equivalence))
    return list_equivalence


def entries_match(entry1, entry2, entry='title'):
    """
    Compare two entries and determine if they match based on title and authors.

    :param entry1: The first entry.
    :param entry2: The second entry.
    :param entry: The field to compare. By default it is 'title'.
    :return: True if the entries match, False otherwise.
    """
    if entry == 'author':
        return (author_name_equivalence(entry1)==author_name_equivalence(entry2))
        #return diff_list_dic(author_name_equivalence(entry1),author_name_equivalence(entry2))# TRUE they match 
        #return diff_list_dic(entry1.get('author'), entry2.get('author')) # TRUE they match 
    else:
        return normalize(entry1.get(entry)) == normalize(entry2.get(entry)) #True they match 


def do_they_have(ref1, ref2, Check_if_have='title'):
    """
    Check if two references have the same field and if the field's value match.

    :param ref1: The first reference.
    :param ref2: The second reference.
    :param Check_if_have: The field to check. By default it is 'title'.
    :return: 3 if both references have the field and the field values match, 
             1 if both references have the field but the field values do not match, 
             0 if both references do not have the field.
    """
    if Check_if_have in ref1 and Check_if_have in ref2:  # They both have the field
        if entries_match(ref1, ref2, Check_if_have):  #if they are the same this is TRUE
            return 3  # They are the same
        else:
            return 1  # They are not the same but have the field
    else:
        return 0  # they both don't have the same fields (as one have title the other no)


def field_values_match_multiple(entry1, entry2, field_name):
    """
    Check if the specified field values match for the two entries.

    :param entry1: The first entry.
    :param entry2: The second entry.
    :param field_name: The name of the field to compare.
    :return: 0 if both entries do not have the field,
             1 if the first entry does not have the field,
             2 if the second entry does not have the field,
             3 if both entries have the field and the field values match,
             4 if both entries have the field but the field values do not match.
    """
    if field_name not in entry1 and field_name not in entry2:
        return 0
    elif field_name not in entry1:
        return 1
    elif field_name not in entry2:   
        return 2
    elif entry1.get(field_name) == entry2.get(field_name):   
        return 3
    else:
        return 4


def compare_files(file1, file2, output_file):# for this we take file 1 to look for then file 2 may be the ground true. I advice to run both cases 1,2 and 2,1   
    """
    Compare two bibliography files and output the comparison result into an output file.

    :param file1: The first file.
    :param file2: The second file.
    :param output_file: The output file.
    """
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        bib_data1 = yaml.safe_load(f1)
        bib_data2 = yaml.safe_load(f2)

    matches = []
    no_matches = {}
    match_counter = {}

    for key1, entry1 in bib_data1['entries'].items():
        found_ref = False
        found_times = 0

        for key2, entry2 in bib_data2['entries'].items():
            title_var = do_they_have(entry1, entry2, 'title')
            author_var = do_they_have(entry1, entry2, 'author')

            if (title_var + author_var) > 2:   # at least one match 3+0 
                if (title_var + author_var) == 6:
                    found_times += 1
                found_ref = True
                
                # Check if the other fields match and save the result (Yes/No) for each field.
                match_results = [field_values_match_multiple(entry1, entry2, field_name) for field_name in ['type', 'journal', 'volume', 'number', 'pages', 'year']]
                matches.append([key1, key2] + ['Yes' if title_var==3 else 'No'] + ['Yes' if author_var==3 else 'No'] + ['Yes' if result==3 else 'M-2' if result==2  else 'M-1'  if result==1  else 'M-Both' if result==0  else 'No' for result in match_results])

        # If no match is found, add the entry to the 'no_matches' dictionary.
        if found_ref:
            if found_times > 1 :
                match_counter[key1] = found_times  
        else:    
            no_matches[key1] = entry1

    with open(output_file, 'w') as f:
        f.write("{: <35}{: <35}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}\n".format('Name in file 1', 'Name in file 2', 'Title','Authors', 'Type', 'Journal', 'Volume', 'Number', 'Pages', 'Year'))
        for match in matches:
            f.write("{: <35}{: <35}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}{: ^10}\n".format(*match))

        f.write('\n\n ** M-1: field is missing for reference in file 1\n ** M-2: field is missing for reference in file 2\n ** MBoth: field is missing for both files\n\n')
        # Print info if more than 1 match is found
        if bool(match_counter):
            for k, v in match_counter.items():
                f.write(f'{v} entries were found for ref: {k}\n')
        if bool(no_matches):
            file_yaml_name_out=output_file.rsplit('.', 1)[0] +'_NO_FOUND.yaml'
            Number_no_found=len(no_matches)
            f.write('\n\n\n')            
            f.write(f'For {Number_no_found} references no match were found (see {file_yaml_name_out})')
            f.write('\n\n\n')
            for k in no_matches.keys():
                f.write(f'{k}\n') 
                
            with open(file_yaml_name_out, 'w') as file:
                documents = yaml.dump(no_matches, file)

def generate_bib_key(id_name, index):
    '''
    Generates a bibliography key based on the given ID name and index.

    Args:
        id_name (str): The ID name to be used in the key generation.
        index (int): The index to be used in the key generation.

    Returns:
        str: The generated bibliography key.
    '''
    return str(id_name) + "-" + str(index).zfill(3)

def preprocess_bibtex_without_key_id(input_filename, output_filename, IDstart='ref', counter_start=1, entry_types=['article', 'book', 'booklet', 'conference', 'inbook', 'incollection', 'inproceedings', 'manual', 'mastersthesis', 'misc', 'phdthesis', 'proceedings', 'techreport', 'unpublished']):
    '''
    Preprocesses a BibTeX file by adding missing unique keys and writing the updated content to a new file.

    Args:
        input_filename (str): The name of the input BibTeX file.
        output_filename (str): The name of the output BibTeX file.
        IDstart (str, optional): The initial ID string to be used in reference key generation. Default is 'ref'.
        counter_start (int, optional): The initial counter value for generating unique keys. Default is 1.
        entry_types (list, optional): The list of BibTeX entry types to consider. Default includes various types.

    Returns:
        None
    '''

    index = counter_start

    with open(input_filename, 'r', encoding='utf-8') as input_file:
        lines = input_file.readlines()

    with open(output_filename, 'w', encoding='utf-8') as output_file:
        for line in lines:
            stripped_line = line.strip()
            if any(re.match(f"@{entry_type}\s*{{\s*,", stripped_line, re.IGNORECASE) for entry_type in entry_types):
                matched_entry_type = re.match(r"@([a-z]*)\s*{", stripped_line, re.IGNORECASE).group(1)
                output_file.write('@' + matched_entry_type + '{' + generate_bib_key(IDstart, index) + ',\n')
                index += 1
            else:
                output_file.write(line)

    return print("preprocess_bibtex_without_key_id created: ",output_filename)

def remove_non_ascii(s):
    '''
    Remove non-ASCII characters from a given string.

    Args:
        s (str): The string from which non-ASCII characters should be removed.

    Returns:
        str: The input string without non-ASCII characters.
    '''
    return "".join(c for c in s if ord(c) < 128)

def replace_special_chars(string):
    '''
    Replaces special characters in the input string as per the mappings specified in 'special_characters.yaml'.

    Args:
        string (str): The input string which may contain special characters.

    Returns:
        str: The input string with special characters replaced.
    '''
    with open('special_characters.yaml', 'r') as f:
        special_chars = yaml.safe_load(f)

    for char, latex in special_chars.items(): 
        string = string.replace(char, latex)

    return string

def replace_journal_name(string):
    '''
    Replaces journal names in the input string as per the mappings specified in 'journal_equivalences.yaml'.

    Args:
        string (str): The input string which may contain journal names.

    Returns:
        str: The input string with journal names replaced.
    '''
    with open('journal_equivalences.yaml', 'r') as f:
        journal_equivalences = yaml.safe_load(f)

    return journal_equivalences.get(string, string)

def process_bib_file(file_name,file_name_output_yaml='file_name.yaml'):
    '''
    Processes a BibTeX file to replace special characters in titles and authors' names, 
    replace full journal names with abbreviations, and save the modified references to a YAML file.

    Args:
        file_name (str): The name of the BibTeX file to be processed.
        file_name_output_yaml (str, optional): The name of the output YAML file. Default is 'file_name.yaml'.

    Returns:
        None
    '''
    parser = pybtex.database.input.bibtex.Parser()
    bib_data = parser.parse_file(file_name)

    for key in bib_data.entries.keys():
        entry = bib_data.entries[key]

        for person in entry.persons['author']:
            for i in range(len(person.first_names)):
                person.first_names[i] = replace_special_chars(person.first_names[i])
            for i in range(len(person.middle_names)):
                person.middle_names[i] = replace_special_chars(person.middle_names[i])
            for i in range(len(person.last_names)):
                person.last_names[i] = replace_special_chars(person.last_names[i])

        if 'title' in entry.fields:
            entry.fields['title'] = replace_special_chars(entry.fields['title'])

        if 'journal' in entry.fields:
            entry.fields['journal'] = replace_journal_name(entry.fields['journal'])

    if file_name_output_yaml=='file_name.yaml':
        bib_data.to_file(file_name.rsplit('.', 1)[0] +'.yaml')
        output_file = file_name.rsplit('.', 1)[0] +'.yaml'
    else:
        bib_data.to_file(file_name.rsplit('.', 1)[0] +'.yaml')
        output_file = file_name.rsplit('.', 1)[0] +'.yaml'

    return(print('New yaml file created:',output_file))

def create_yaml_from_dic(dic_to_yaml,yaml_file_name):
    '''
    Creates a YAML file from a dictionary.

    Args:
        dic_to_yaml (dict): The dictionary to be converted into a YAML file.
        yaml_file_name (str): The name of the output YAML file.

    Returns:
        None
    '''
    with open(yaml_file_name, 'w') as file:
        documents = yaml.dump(dic_to_yaml, file)

def check_if_is_yaml(file_name, dir_name='./'):
    '''
    Checks if a given file is a YAML file.

    Args:
        file_name (str): The name of the file to be checked.
        dir_name (str, optional): The directory where the file is located. Default is current directory.

    Returns:
        bool: True if the file is a YAML file, False otherwise.
    '''
    if isinstance(file_name, dict):
        return False
    elif Path(dir_name, file_name).is_file():
        return file_name.lower().endswith('.yaml')
    else:
        return False
    
            
def add_entry_to_yaml_old_noformat(yaml_file, entry_data_A, dir_entry_data='./'):
    '''
    Adds new entries from a YAML file or dictionary into an existing YAML file.

    Args:
        yaml_file (str): The name of the target YAML file.
        entry_data_A (str or dict): The name of the source YAML file or a dictionary containing data to be added.
        dir_entry_data (str, optional): The directory where the source YAML file is located. Default is current directory.

    Returns:
        str: A message indicating the result of the operation.
    '''

    if check_if_is_yaml(entry_data_A, dir_entry_data):
        with open(entry_data_A, 'r') as f1:
            entry_data = yaml.safe_load(f1)
            if 'entries' in entry_data:
                entry_data = entry_data['entries']
    elif isinstance(entry_data_A, dict):
        entry_data = entry_data_A
    else:
        print("The second file is neither a dictionary nor a YAML file.")
        return

    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        if 'entries' in data:
            data = data['entries']
        elements_add = set(entry_data.keys()) - set(data.keys())
        if elements_add:
            for key_add in elements_add:
                data[key_add] = entry_data[key_add]
            with open(yaml_file, 'w') as file:
                yaml.dump(data, file)
                return f"Added from {entry_data_A} :{os.linesep}{elements_add}{os.linesep} to {yaml_file}"
        else:
            keys = ",".join(list(entry_data.keys()))
            
            return f"from {entry_data_A} :{os.linesep}{keys}{os.linesep} already exists in {yaml_file}"
                

def add_entry_to_yaml_no_set(yaml_file, entry_data_A, dir_entry_data='./'):
    '''
    Adds new entries from a YAML file or dictionary into an existing YAML file.

    Args:
        yaml_file (str): The name of the target YAML file.
        entry_data_A (str or dict): The name of the source YAML file or a dictionary containing data to be added.
        dir_entry_data (str, optional): The directory where the source YAML file is located. Default is current directory.

    Returns:
        str: A message indicating the result of the operation.
    '''

    if check_if_is_yaml(entry_data_A, dir_entry_data):
        with open(entry_data_A, 'r') as f1:
            entry_data = yaml.safe_load(f1)
            if 'entries' in entry_data:
                entry_data = entry_data['entries']
    elif isinstance(entry_data_A, dict):
        entry_data = entry_data_A
    else:
        print("The second file is neither a dictionary nor a YAML file.")
        return

    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        if 'entries' in data:
            data = data['entries']
            for key in entry_data:
                if key in data:
                    print(f"{key} already exists in {yaml_file}")
                else:
                    data[key] = entry_data[key]
            with open(yaml_file, 'w') as file:
                yaml.dump({'entries': data}, file)
                return f"Added from {entry_data_A} to {yaml_file}"
        else:
            with open(yaml_file, 'w') as file:
                yaml.dump({'entries': entry_data}, file)
                return f"Added from {entry_data_A} to {yaml_file}"  
            

def add_entry_dic_to_yaml(yaml_file, entry_data_A, dir_entry_data='./'):
    """
    This function takes two dictionaries as input and adds the entries from the second dictionary (the yaml file) to the first dictionary if they are not already present.
    :param yaml_file: The name of the file to which entries are to be added.
    :param entry_data_A: The dictionary containing the entries to be added.
    :param dir_entry_data: The directory containing the second file. Default is './'.
    :return: 'Done' if the entries were added successfully. Otherwise, an error message.
    """
    #check_if_is_yaml
    if not check_if_is_yaml(yaml_file, dir_name='./'):
        print(f'{yaml_file} is not an appropriate yaml!')
        sys.exit()
        
    open_yaml_Data=is_yaml_open(yaml_file)  
    open_dic_Entry=entry_data_A
    
    if not isinstance(open_dic_Entry, dict):
        return print("The second file needs to be a dictionary.")
    
    if 'entries' in open_dic_Entry:#This is if there is a dictionary of references
        return print('Please do not use entries as key')     
    
    elements_add = set(open_dic_Entry.keys()) - set(open_yaml_Data.keys())
    
    if elements_add: # There are ref to add
        for key_add in elements_add:
            open_yaml_Data[key_add] = open_dic_Entry[key_add]
            with open(yaml_file, 'w') as file:
                yaml.dump(open_yaml_Data, file)
                print(f'Added from {entry_data_A} :')
                print (*list(elements_add), sep=",")
                print(f'to {yaml_file}')
                return f"Done"
    else:
        keys = ",".join(list(open_dic_Entry.keys()))
        return f"{keys} already exists in {yaml_file}"

def add_entry_dic_to_yaml_referece(yaml_file, entry_data_A, dir_entry_data='./'):
    '''
    Adds entries from a given dictionary to an existing YAML reference file.

    Args:
        yaml_file (str): The name of the target YAML reference file.
        entry_data_A (dict): A dictionary containing data to be added.
        dir_entry_data (str, optional): The directory where the source YAML file is located. Default is current directory.

    Returns:
        str: A message indicating the result of the operation.
    '''
    # Checks if the target file is a valid YAML file.
    if not check_if_is_yaml(yaml_file, dir_name='./'):
        print(f'{yaml_file} is not an appropriate yaml!')
        sys.exit()    

    open_dic_Entry=entry_data_A
    open_yaml_Data=is_yaml_open(yaml_file)

    # Checks that the first file is a correct data base and the second file is yaml.
    if not open_dic_Entry or not 'entries' in open_yaml_Data: 
        return print('please check that both files are yaml and that the first file is a correct database with entry:' )  

    # Checks that the second file is a correct dictionary.
    if not isinstance(open_dic_Entry, dict):
        return print("The second file needs to be a dictionary.")

    # Checks that there is no dictionary of references under the key 'entries'.
    if 'entries' in open_dic_Entry:
        return print('Please do not use entries as key') 

    # Inverts the dictionaries for comparison.
    data_inver_Data_pulled=pull_entry(open_yaml_Data)
    data_inver_Data = dict_invertion(data_inver_Data_pulled,'title')       
    data_inver_Entry = dict_invertion(open_dic_Entry,'title')

    # Compares the two dictionaries to find any additional entries in the input dictionary.   
    elements_add = set(data_inver_Entry.keys()) - set(data_inver_Data.keys())

    # If there are references to add, update the YAML file with new entries.
    if elements_add:
        values_to_get = [data_inver_Entry.get(key) for key in elements_add]
        for key_add in values_to_get:
            data_inver_Data_pulled[key_add] = open_dic_Entry[key_add]
        with open(yaml_file, 'w') as file:
            yaml.dump({'entries': data_inver_Data_pulled}, file)
            print(f'From the given dictionary this references where added :')
            print (*list(values_to_get), sep="\n")
            print(f'to {yaml_file}')
            return f"Done"
    else:
        # If there are no references to add, return a message indicating that all entries already exist in the YAML file.
        keys = ",".join(list(open_dic_Entry.keys()))
        return f"{keys} already exists in {yaml_file}"

def add_entry_dic_to_yaml_referece(yaml_file, entry_data_A, dir_entry_data='./'):
    '''
    Adds entries from a given dictionary to an existing YAML reference file.

    Args:
        yaml_file (str): The name of the target YAML reference file.
        entry_data_A (dict): A dictionary containing data to be added.
        dir_entry_data (str, optional): The directory where the source YAML file is located. Default is current directory.

    Returns:
        str: A message indicating the result of the operation.
    '''
    # Checks if the target file is a valid YAML file.
    if not check_if_is_yaml(yaml_file, dir_name='./'):
        print(f'{yaml_file} is not an appropriate yaml!')
        sys.exit()    

    open_dic_Entry=entry_data_A
    open_yaml_Data=is_yaml_open(yaml_file)
    
    # Checks that the first file is a correct data base and the second file is yaml.
    if not open_dic_Entry or not 'entries' in open_yaml_Data: 
        return print('please check that both files are yaml and that the first file is a correct database with entry:' )  
    
    # Checks that the second file is a correct dictionary.
    if not isinstance(open_dic_Entry, dict):
        return print("The second file needs to be a dictionary.")
    
    # Checks that there is no dictionary of references under the key 'entries'.
    if 'entries' in open_dic_Entry:
        return print('Please do not use entries as key') 
    
    # Inverts the dictionaries for comparison.
    data_inver_Data_pulled=pull_entry(open_yaml_Data)
    data_inver_Data = dict_invertion(data_inver_Data_pulled,'title')       
    data_inver_Entry = dict_invertion(open_dic_Entry,'title')
              
    # Compares the two dictionaries to find any additional entries in the input dictionary.   
    elements_add = set(data_inver_Entry.keys()) - set(data_inver_Data.keys())
    
    # If there are references to add, update the YAML file with new entries.
    if elements_add:
        values_to_get = [data_inver_Entry.get(key) for key in elements_add]
        for key_add in values_to_get:
            data_inver_Data_pulled[key_add] = open_dic_Entry[key_add]
        with open(yaml_file, 'w') as file:
            yaml.dump({'entries': data_inver_Data_pulled}, file)
            print(f'From the given dictionary this references where added :')
            print (*list(values_to_get), sep="\n")
            print(f'to {yaml_file}')
            return f"Done"
    else:
        # If there are no references to add, return a message indicating that all entries already exist in the YAML file.
        keys = ",".join(list(open_dic_Entry.keys()))
        return f"{keys} already exists in {yaml_file}"


def add_entry_yaml_to_yaml_referece(yaml_file, entry_data_A, dir_entry_data='./'):
    """
    This function takes two filenames as input and adds the entries from the second yaml file to the yaml first file if they are not already present.
    :param yaml_file: The name of the file to which entries are to be added which need to be in the reference format.
    :param entry_data_A: The name of the file containing the entries to be added.
    :param dir_entry_data: The directory containing the second file. Default is './'.
    :return: 'Done' if the entries were added successfully. Otherwise, an error message.
    """

    #check_if_is_yaml
    if not check_if_is_yaml(yaml_file, dir_name='./'):
        print(f'{yaml_file} is not an appropriate yaml!')
        sys.exit()
    if not check_if_is_yaml(yaml_file, dir_name='./'):
        print(f'{entry_data_A} is not an appropriate yaml!')
        sys.exit()   
    
    #first open files    
    open_yaml_Data=is_yaml_open(yaml_file)
    open_yaml_Entry=is_yaml_open(entry_data_A)
    
    #check that the first yaml is a correct database
    if not open_yaml_Entry or not 'entries' in open_yaml_Data: #Check that the first file is a correct data base and the second file is yaml
        return print('please check that both files are yaml and that the first file is a correct database with entry:' )  
    #Inverse the files
    data_inver_Data_pulled=pull_entry(open_yaml_Data)
    entry_data_Entry_pulled=pull_entry(open_yaml_Entry)
    data_inver_Data = dict_invertion(data_inver_Data_pulled,'title')       
    data_inver_Entry = dict_invertion(entry_data_Entry_pulled,'title')
              
    #compare the 2 objects        
    elements_add = set(data_inver_Entry.keys()) - set(data_inver_Data.keys())
    
    if elements_add: # There are ref to add          
        values_to_get = [data_inver_Entry.get(key) for key in elements_add]
        for key_add in values_to_get:
            data_inver_Data_pulled[key_add] = entry_data_Entry_pulled[key_add]
        with open(yaml_file, 'w') as file:
            yaml.dump({'entries': data_inver_Data_pulled}, file)
            print(f'Added from {entry_data_A} :')
            print (*list(values_to_get), sep="\n")
            #print(f'{values_to_get}')
            print(f'to {yaml_file}')
            return f"Done"
    else:
        return f"from {entry_data_A} : all elements already exists in {yaml_file}"


            
def add_entry_yaml_to_yaml_referece_old(yaml_file, entry_data_A, dir_entry_data='./'):
    
    #first open files
    open_yaml_Data=is_yaml_open(yaml_file)
    open_yaml_Entry=is_yaml_open(entry_data_A)
    
    #check that the first yaml is a correct database
    if not open_yaml_Entry or not 'entries' in open_yaml_Data: #Check that the first file is a correct data base and the second file is yaml
        return print('please check that both files are yaml and that the first file is a correct database with entry:' )  
    #Inverse the files
    data_inver_Data_pulled=pull_entry(open_yaml_Data)
    entry_data_Entry_pulled=pull_entry(open_yaml_Entry)
    data_inver_Data = dict_invertion(data_inver_Data_pulled,'title')       
    data_inver_Entry = dict_invertion(entry_data_Entry_pulled,'title')
              
    #compare the 2 objects        
    elements_add = set(data_inver_Entry.keys()) - set(data_inver_Data.keys())
    
    if elements_add: # There are ref to add          
        values_to_get = [data_inver_Entry.get(key) for key in elements_add]
        for key_add in values_to_get:
            data_inver_Data_pulled[key_add] = entry_data_Entry_pulled[key_add]
        with open(yaml_file, 'w') as file:
            yaml.dump({'entries': data_inver_Data_pulled}, file)
            print(f'Added from {entry_data_A} :')
            print (*values_to_get, sep="\n")
            print(f'to {yaml_file}')
            return f"Done"
    else:
        return f"from {entry_data_A} : all elements already exists in {yaml_file}"

    
    
def add_entry_to_yaml(yaml_file, entry_data_A, dir_entry_data='./'):
    '''
    Adds new entries from a YAML file or dictionary into an existing YAML file.

    Args:
        yaml_file (str): The name of the target YAML file.
        entry_data_A (str or dict): The name of the source YAML file or a dictionary containing data to be added.
        dir_entry_data (str, optional): The directory where the source YAML file is located. Default is current directory.

    Returns:
        str: A message indicating the result of the operation.
    '''

    if check_if_is_yaml(entry_data_A, dir_entry_data):
        with open(entry_data_A, 'r') as f1:
            entry_data = yaml.safe_load(f1)
            if 'entries' in entry_data:
                entry_data = entry_data['entries']
    elif isinstance(entry_data_A, dict):
        entry_data = entry_data_A
    else:
        print("The second file is neither a dictionary nor a YAML file.")
        return

    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)
        if 'entries' in data:
            data = data['entries']
            elements_add = set(entry_data.keys()) - set(data.keys())
            if elements_add:
                for key_add in elements_add:
                    data[key_add] = entry_data[key_add]
                with open(yaml_file, 'w') as file:
                    yaml.dump({'entries': data}, file)
                    return f"Added from {entry_data_A} :{os.linesep}{elements_add}{os.linesep} to {yaml_file}"
            else:
                keys = ",".join(list(entry_data.keys()))
                return f"from {entry_data_A} :{os.linesep}{keys}{os.linesep} already exists in {yaml_file}"
        else:
            with open(yaml_file, 'w') as file:
                yaml.dump({'entries': entry_data}, file)
                return f"Added from {entry_data_A} to {yaml_file}"            
