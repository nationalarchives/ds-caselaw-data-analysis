#import xml.etree.ElementTree as et
from lxml import etree as etree
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import shutil, time
import io

'''
get_filenames(processing_root, data_paths)
process_parts(folder, filename, parts)
parts_to_df(processing_root, folders)
get_parts_values(processing_root, folder)
output_to_text_files(processing_root, folder, filename, texts)
parse_file(folder, filename)
read_xml_file(folder_path, filename)
input_from_text_files(processing_root, folders)
print_element_info(data_dict)
split(data)
combine(dict1, dict2)

Processes:
    Extract values from XML and save as text [Done] 
    Creates DataFrame from values [Done]
    Writes DataFrame to Pickle [Done]
    
'''

def get_filenames(processing_root, data_paths):
    ''' Function gets the list of XML files in the data folder

        Returns list of filenames
    '''

    filenames = set()
    
    for data_path in data_paths:
        for file in Path(processing_root, data_path).glob("*.xml"):  
            base_filename = Path(file).stem
            
            if base_filename[0] == "-":
                base_filename_trimmed = base_filename[1:]
                if base_filename_trimmed in filenames:
                    filenames.remove(base_filename_trimmed)
            
            if "-" + base_filename not in filenames:
                filenames.add(base_filename)
    
    return filenames


def process_parts(folder, filename, parts):
    ''' For a given file in a given pass the function processes the values extracted from the tag elements into a list of dictionaries, one for each file. '''

    parts_list = []
    
    for part in parts.strip().split("\n"):
        try:
            element, attributes, text = part.split("|||", 2)   
        except ValueError as e:
            print("Can't split line in "  + filename + ": " + part + ": " + str(e))
            break
            
        part_dict = {"data":folder, "file": filename, "element": element.strip().tolower(), 'text':text.strip()}
        
        if '||' in attributes:
            attribute_list = attributes.split("||")

            
            for attribute in attribute_list:
                try:
                    attr, value = attribute.split("=", 1)
                    part_dict.update({attr.strip().tolower(): value.strip()})
                except ValueError as e:
                    print("Error in data: " + folder + ", file: " + filename + ", attribute: " + attribute + " - " + str(e))
        
        parts_list.append(part_dict)
                   
    return parts_list


def parts_to_df(processing_root, cache_path, folders):
    ''' For the folders in the list, get the parts values and create a dataframe from the list of values. Split the dataframe into dictionary of dataframes by element type, print out the information about each element, pickle the dataframes and return the dictionay of dataframes.
    '''    
    
    parts_list = []
    parts_data_dict = {}
    
  
    for folder in folders:
        print("Processing " + folder)
        parts_list += get_parts_values(processing_root, folder)    
    
    #print(parts_list)                    
    parts_data_dict = split(pd.DataFrame(parts_list))            

    print_element_info(cache_path, parts_data_dict)
    
    for element, element_data in parts_data_dict.items():
        element_data.to_pickle(Path(cache_path, element + ".pkl"))
        
    return parts_data_dict


def get_parts_values(processing_root, folder):
    ''' Function reads the values from the text files in the processing folder for a given folder and reads the text into a list'''

    parts_list = []
    count = 0
    
    for file in Path(processing_root, "extracted_values", folder).glob("*.txt"):  
        filename = Path(file).stem
        with open(file, "r", encoding="utf-8") as myfile:
            parts = myfile.read()
            parts_list += process_parts(folder, filename, parts)
            count += 1
            
        if count % 10000 == 0:
            print("Processed " + str(count) + " extracted value files")
                   
    return parts_list             

        
def output_to_text_files(processing_root, folder, filename, texts):   
    ''' Write the extracted values (texts) to text files.
        texts should be a triple with the parts values, head text values and body text values in that order.

        Writes text files with extracted values
    '''

    bodytextfile_path = Path(processing_root, "extracted_text", folder, filename + "_body.txt")
    headtextfile_path = Path(processing_root, "extracted_text", folder, filename + "_head.txt")
    partfile_path = Path(processing_root, "extracted_values", folder, filename + ".txt")
    
    parts, head_text, body_text = texts
    
    try:
        with open(headtextfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(head_text) 

        with open(bodytextfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(body_text)   
            
        with open(partfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(parts)  
    except IOError as e:
        print("Could not save file: " + str(e))

    
def parse_file(folder, filename):
    ''' Function reads the specified XML file and runs the transformations on it to extract the element values, head text and body text. Returns the values in a tuple in that order.
    '''
    
    get_head_text_transform_file = Path("data", "xslt", "get_head_text.xsl")
    get_body_text_transform_file = Path("data", "xslt", "get_body_text.xsl")
    get_parts_transform_file = Path("data", "xslt", "get_parts.xsl")
    
    xml_file = Path(folder, filename + ".xml") 

    try:
        tree = etree.parse(xml_file)       
    except etree.ParseError as e:
        with open("data/errors-ParsingError.txt", "a", encoding="utf-8") as myfile:
            myfile.write("Parser error in " + filename + ".xml: " + str(e) + "\n")
        
        shutil.move(Path(folder, filename + ".xml"), Path(folder, "ParsingError", filename + ".xml"))    
        
    #root = tree.getroot()  
    
    try: 
        get_head_text_transform = etree.parse(get_head_text_transform_file)  
        get_body_text_transform = etree.parse(get_body_text_transform_file)  
        get_parts_transform = etree.parse(get_parts_transform_file) 
    except etree.ParseError as e:
        print(e)
    
    get_head_text_transform = etree.XSLT(get_head_text_transform)  
    get_body_text_transform = etree.XSLT(get_body_text_transform) 
    get_parts_transform = etree.XSLT(get_parts_transform)  
    
    body_text = get_body_text_transform(tree)
    head_text = get_head_text_transform(tree)
    parts = get_parts_transform(tree)
    
    return(parts, head_text, body_text)


def read_xml_file(folder_path, filename):
    ''' Function gets values extracted from the specified XML file, processes the head and body text into strings and returns the values in a tuple in the order part values, head text body text. 
    '''

    parts, head_text, body_text = parse_file(folder_path, filename)
    #print("file: " + str(file_to_check) + " exists") 
    
    if "|||" in str(head_text):
        head_parts = str(head_text).split("|||")            
        head_text = ' '.join(head_parts[0].split()) + "\n\n" + ' '.join(head_parts[1].split())
    else:
        head_text = str(head_text)
        
    body_text = ' '.join(str(body_text).split())    
    
    return (parts, head_text, body_text)


def read_text_file(processing_file, current_folder, filename):    
    ''' For the specified file, read the head text, body text and element values from the extracted text file. Returns the values in a tuple in the order part values, head text body text
    '''

    headtextfile_path = Path(processing_file, "extracted_text", current_folder, filename + "_head.txt")
    bodytextfile_path = Path(processing_file, "extracted_text", current_folder, filename + "_body.txt")
    valuestextfile_path = Path(processing_file, "extracted_values", current_folder, filename + ".txt")
    
    #print(headtextfile_path)
    #print(bodytextfile_path)
    #print(valuestextfile_path)
    
    try:
        with open(headtextfile_path, "r", encoding="utf-8") as myfile:
            head_text = myfile.read()
        
        with open(bodytextfile_path, "r", encoding="utf-8") as myfile:
            body_text = myfile.read()
        
        with open(valuestextfile_path, "r", encoding="utf-8") as myfile:
            parts = myfile.read()
                 
    except IOError as e:
        print("Could not read file: " + str(e))    
               
    return (parts, head_text, body_text)


def input_from_text_files(processing_root, folders = []):
    ''' If folder names are given then get the parts values for the specified folder, otherwise get them from the extracted values folder. Get the extracted values from the text files.
        [Not implemented yet!]
    '''

    parts_dict = {}
    head_text_dict = {}
    body_text_dict = {}
    

    if len(folders) > 0:  #Get all folders
        for folder in folders:         
            for file in Path(processing_root, "extracted_values", folder).glob("*.txt"):  
                parts, head_text, body_text = read_text_file(processing_root, folder, file)
                # DO SOMETHING HERE

    else:   
        for file in Path(processing_root, "extracted_values").glob("*.txt"):  
            parts, head_text, body_text = read_text_file(processing_root, folder, file)
            # DO SOMETHING HERE
            
    return(parts_dict, head_text_dict, body_text_dict)


def print_element_info(folder_path, data_dict):
    ''' Save info about each element dictionary into text files.
    '''
    
    for element, element_data in data_dict.items():
        #print(parts_full_dataframe.info())
        num_rows = element_data.shape[1] 
        #element_details_file = element.replace(":", "_")

        with open(Path(folder_path, element + ".txt"), "w", encoding="utf-8") as myfile:
                buffer = io.StringIO()
                element_data.info(buf = buffer)
            
                myfile.write(buffer.getvalue()) 
                myfile.write("\n")
                myfile.write("Shape: " + str(element_data.shape) + "\n") 
                
                if num_rows < 10:
                    myfile.write("All:\n")
                    myfile.write(element_data.head(num_rows).to_string()) 
                else:
                    myfile.write("Sample:\n")
                    myfile.write(element_data.head(5).to_string()) 
                    myfile.write("\n")
                    myfile.write(element_data.tail(5).to_string()) 


def split(data):
    ''' Function separates the data into the different elements. Process 
    '''
    
    dataframes = {}
    
    #print(data.info)
       
    element_list = data['element'].astype(str).unique()

    #print(element_list)

    for element in element_list:
        #print("Element: " + element)
        
        temp_df = data.loc[data['element'] == element]
        temp_df = temp_df.dropna(axis='columns', how='all')
        
        dataframes[element.replace(":", "_")] = temp_df

    return dataframes


def combine(dict1, dict2):
    ''' Function combines two dictionaries 
    '''

    combined_dict = {}
    keys1 = dict1.keys()
    keys2 = dict2.keys()
    
    overlap = [x for x in keys1 if x in keys2]
    keys1_only = [x for x in keys1 if x not in keys2]
    keys2_only = [x for x in keys2 if x not in keys1]
    
    # get the overlap of keys and for each concat the dataframes   
    # drop duplicates for the combined dataframes
    # add to dict
    for overlapped_element in overlap:
        combined_df = pd.concat([dict1[overlapped_element], dict2[overlapped_element]])
        combined_df = combined_df.drop_duplicates(subset=combined_df.columns.difference(['pass']))
        combined_dict[overlapped_element] = combined_df.reset_index(drop=True)
    
    # add the dataframes from the non-overlapped keys to the dict
    for dict1_only_element in keys1_only:
        combined_dict[dict1_only_element] = dict1[dict1_only_element]
        
    for dict2_only_element in keys2_only:
        combined_dict[dict2_only_element] = dict2[dict2_only_element]        
    
    # return the dict
    return combined_dict

def generate_dfs(start_time, processing_root, cache_path, folders=[]):
    read_time = time.time()
    dict_of_dfs = {}

    duration = read_time - start_time
    current_time = datetime(1,1,1) + timedelta(seconds=duration)
    readable_duration = str(current_time.day-1) + ":" + str(current_time.hour) + ":" + str(current_time.minute) + ":" + str(current_time.second)
    print("Reading took " + readable_duration +  " to run") 

    dict_of_dfs = parts_to_df(processing_root, cache_path, folders)

    duration = time.time() - read_time
    current_time = datetime(1,1,1) + timedelta(seconds=duration)
    readable_duration = str(current_time.day-1) + ":" + str(current_time.hour) + ":" + str(current_time.minute) + ":" + str(current_time.second)
    print("Pickling took " + readable_duration +  " to run")   

    return dict_of_dfs 


def main(processing_root, data_paths, folder_map, cache_path, folders = []):
    start_time = time.time()

    filenames = get_filenames(processing_root, data_paths) 
    not_matched = []
    #parts_data_dict = {}
    #text_list = []
    #body_set = set()
    #head_set = set()

    for data_path in data_paths:
        count = len(list(Path(processing_root, data_path).glob("*.xml")))
        print("Processing folder: " + data_path + "(" + str(count) + " files)")
        
        exists_count = 0
        not_exists_count = 0
        current_folder = folder_map[data_path]
            
        for filename in filenames: 
            
            #data_root = [filename, data_path]
            
            xml_folder_path = Path(processing_root, data_path)
        
            #xml_file1 = Path(processing_root, folder1, filename + ".xml") 
            #xml_file2 = Path(processing_root, folder2, filename + ".xml") 
            #xml_file3 = Path(processing_root, folder3, filename + ".xml") 
            
            xml_file_to_check = Path(str(xml_folder_path), str(filename) + ".xml")
            values_file_to_check = Path(processing_root, "extracted_values", current_folder, str(filename) + ".txt")
            head_file_to_check = Path(processing_root, "extracted_text", current_folder, str(filename) + "_head.txt")
            body_file_to_check = Path(processing_root, "extracted_text", current_folder, str(filename) + "_body.txt")
            
            if xml_file_to_check.exists():
                exists_count += 1
                if values_file_to_check.exists() and head_file_to_check.exists() and body_file_to_check.exists():
                    parts, head_text, body_text = read_text_file(processing_root, current_folder, filename)
                else:
                    parts, head_text, body_text = read_xml_file(xml_folder_path, filename)
                    parts = str(parts)
                    output_to_text_files(processing_root, current_folder, filename, (parts, head_text, body_text))     
                
                
                '''
                # parts dataframes    
                parts_values = process_parts(current_pass, filename, parts)
                new_values = split(pd.DataFrame(parts_values))            
                parts_data_dict = combine(parts_data_dict, new_values)       
                
                # text dataframe  
                if body_text not in body_set or head_text not in head_set:
                    #print("Adding value to text_list")
                    text_list.append({"pass":current_pass, "file": filename, "head_text": head_text, 'body_text':body_text})
                    head_set.add(head_text)
                    body_set.add(body_text)
                '''  
                        
            else:
                not_exists_count += 1
                not_matched.append(filename)
                #print("file: " + str(file_to_check) + " does not exist")   
                
        print("Files checked: " + str(exists_count))
        if not_exists_count > 0:
            print("Files mismatched: " + str(not_exists_count) + " (Missing:" + ','.join(not_matched) + ")")
        #print_element_info(parts_data_dict)

    '''
    text_dataframe = pd.DataFrame.from_dict(text_list)
    text_dataframe.to_pickle(Path(cache_path, "plain_text.pkl"))

    for element, element_data in parts_data_dict.items():
        element_data.to_pickle(Path(cache_path, element + ".pkl"))
    '''

    if len(folders) == 0:
        data_folders = []
        for folder in folder_map.values():
            data_folders.append(folder)
        generate_dfs(start_time, processing_root, cache_path, data_folders)
    else:
        generate_dfs(start_time, processing_root, cache_path, folders)


if __name__ == '__main__':
    processing_root = "data"

    #test data
    test_paths = ["xml-test"]
    test_pass_nums = {"xml-test":"test"}
    test_cache_path = processing_root + "/processing/test/cache/extracted_data"

    #FCL data
    test_enrichment_paths = ["xml-enriched-bucket-test", "xml-second-phase-enriched-bucket-test", "xml-third-phase-enriched-bucket-test"]
    test_enrichment_pass_nums = {"xml-enriched-bucket-test":"pass0", "xml-second-phase-enriched-bucket-test":"pass1", "xml-third-phase-enriched-bucket-test":"pass2"}
    enrichment_paths = ["xml-third-phase-enriched-bucket", "xml-second-phase-enriched-bucket", "xml-enriched-bucket"]
    enrichment_pass_nums = {"xml-enriched-bucket":"pass0", "xml-second-phase-enriched-bucket":"pass1", "xml-third-phase-enriched-bucket":"pass2"}
    enrichment_cache_path = processing_root + "/processing/cache/extracted_data"
   
    main(processing_root, test_paths, test_pass_nums, test_cache_path) 