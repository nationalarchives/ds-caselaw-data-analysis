#import xml.etree.ElementTree as et
from lxml import etree as etree
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import shutil, time
import io

def get_filenames(processing_root, data_paths):
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

def process_parts(pass_num, filename, parts):
    parts_list = []
    
    for part in parts.strip().split("\n"):
        element, attributes, text = part.split("|||")    
        part_dict = {"pass":pass_num, "file": filename, "element": element.strip(), 'text':text.strip()}
        
        if '||' in attributes:
            attribute_list = attributes.split("||")

            
            for attribute in attribute_list:
                try:
                    attr, value = attribute.split("=", 1)
                    part_dict.update({attr.strip(): value.strip()})
                except ValueError as e:
                    print("Error in pass: " + str(pass_num) + ", file: " + filename + ", attribute: " + attribute + " - " + str(e))
        
        parts_list.append(part_dict)
                   
    return parts_list
        
def output_to_text_files(processing_root, filename, texts):    
    bodytextfile_path = Path(processing_root, "extracted_text", filename + "_body.txt")
    headtextfile_path = Path(processing_root, "extracted_text", filename + "_head.txt")
    partfile_path = Path(processing_root, "extracted_values", filename + ".txt")
    
    parts, head_text, body_text = texts
    
    try:
        with open(headtextfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(head_text) 

        with open(bodytextfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(body_text)   
            
        with open(partfile_path, "w", encoding="utf-8") as myfile:
            myfile.write(str(parts))  
    except IOError as e:
        print("Could not save file: " + str(e))
    
def parse_file(folder, filename):
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

def print_element_info(data_dict):
    
    for element, element_data in data_dict.items():
        #print(parts_full_dataframe.info())
        num_rows = element_data.shape[1] 
        #element_details_file = element.replace(":", "_")

        with open(Path("temp", element + ".txt"), "w", encoding="utf-8") as myfile:
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
    
    dataframes = {}
       
    element_list = data['element'].astype(str).unique()

    #print(element_list)

    for element in element_list:
        #print("Element: " + element)
        
        temp_df = data.loc[data['element'] == element]
        temp_df = temp_df.dropna(axis='columns', how='all')
        
        dataframes[element.replace(":", "_")] = temp_df

    return dataframes

def combine(dict1, dict2):
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

start_time = time.time()
processing_root = "data"
#data_paths = ["xml-enriched-bucket-test", "xml-second-phase-enriched-bucket-test", "xml-third-phase-enriched-bucket-test"]
#pass_num = {"xml-enriched-bucket-test":1, "xml-second-phase-enriched-bucket-test":2, "xml-third-phase-enriched-bucket-test":3}
data_paths = ["xml-enriched-bucket", "xml-second-phase-enriched-bucket", "xml-third-phase-enriched-bucket"]
pass_num = {"xml-enriched-bucket":1, "xml-second-phase-enriched-bucket":2, "xml-third-phase-enriched-bucket":3}
cache_path = processing_root + "/processing/cache/extracted_data"

filenames = get_filenames(processing_root, data_paths) 
parts_data_dict = {}
text_list = []
body_set = set()
head_set = set()

for data_path in data_paths:
    count = len(list(Path(processing_root, data_path).glob("*.xml")))
    print("Processing folder: " + data_path + "(" + str(count) + " files)")
    
    exists_count = 0
    not_exists_count = 0
         
    for filename in filenames: 
        
        data_root = [filename, data_path]
        
        folder_path = Path(processing_root, data_path)
       
        #xml_file1 = Path(processing_root, folder1, filename + ".xml") 
        #xml_file2 = Path(processing_root, folder2, filename + ".xml") 
        #xml_file3 = Path(processing_root, folder3, filename + ".xml") 
        
        file_to_check = Path(str(folder_path), str(filename) + ".xml")
        
        if file_to_check.exists():
            exists_count += 1
            parts, head_text, body_text = parse_file(folder_path, filename)
            #print("file: " + str(file_to_check) + " exists") 
            
            if "|||" in str(head_text):
                head_parts = str(head_text).split("|||")            
                head_text = ' '.join(head_parts[0].split()) + "\n\n" + ' '.join(head_parts[1].split())
            else:
                head_text = str(head_text)
                
            body_text = ' '.join(str(body_text).split())
            
            output_to_text_files(processing_root, filename, (parts, head_text, body_text))
            
            # parts dataframes
            parts_values = process_parts(pass_num[data_path], filename, str(parts))
            new_values = split(pd.DataFrame(parts_values))            
            parts_data_dict = combine(parts_data_dict, new_values)       
            
            # text dataframe  
            if body_text not in body_set or head_text not in head_set:
                #print("Adding value to text_list")
                text_list.append({"pass":pass_num[data_path], "file": filename, "head_text": head_text, 'body_text':body_text})
                head_set.add(head_text)
                body_set.add(body_text)
                       
        else:
            not_exists_count += 1
            #print("file: " + str(file_to_check) + " does not exist")   
            
    print("Files checked: " + str(exists_count))
    print("Files mismatched: " + str(not_exists_count))
    print_element_info(parts_data_dict)

text_dataframe = pd.DataFrame.from_dict(text_list)
text_dataframe.to_pickle(Path(cache_path, "plain_text.pkl"))

for element, element_data in parts_data_dict.items():
    element_data.to_pickle(Path(cache_path, element + ".pkl"))

duration = time.time() - start_time
time = datetime(1,1,1) + timedelta(seconds=duration)
readable_duration = str(time.day-1) + ":" + str(time.hour) + ":" + str(time.minute) + ":" + str(time.second)

print("Reading and pickling took " + readable_duration +  " to run")        