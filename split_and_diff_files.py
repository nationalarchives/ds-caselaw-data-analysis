#import xml.etree.ElementTree as et
from lxml import etree as etree
from pathlib import Path
import pandas as pd
import shutil

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


def process_parts(parts):
    parts_list = []
    
    for part in parts.strip().split("\n"):
        element, attributes, text = part.split("||")    
        part_dict = {"element": element.strip(), 'text':text.strip()}
        
        if '|' in attributes:
            attribute_list = attributes.split("|")

            for attribute in attribute_list:
                attr, value = attribute.split("=")
                part_dict.update({attr.strip(): value.strip()})
        
        parts_list.append(part_dict)
                   
    return parts_list
        

def output_to_text_files(processing_root, filename, texts):    
    bodytextfile_path = Path(processing_root, "extracted_text", filename + "_body.txt")
    headtextfile_path = Path(processing_root, "extracted_text", filename + "_head.txt")
    partfile_path = Path(processing_root, "extracted_values", filename + ".txt")
    
    parts, head_text, body_text = texts

    head_parts = str(head_text).split("||")
            
    head_text = ' '.join(head_parts[0].split()) + "\n\n" + ' '.join(head_parts[1].split())
    body_text = ' '.join(str(body_text).split())
    
    try:
        with open(headtextfile_path, "w") as myfile:
            myfile.write(head_text) 

        with open(bodytextfile_path, "w") as myfile:
            myfile.write(body_text)   
            
        with open(partfile_path, "w") as myfile:
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
        with open("data/errors-ParsingError.txt", "a") as myfile:
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


processing_root = "data"
data_paths = ["xml-enriched-bucket-test", "xml-second-phase-enriched-bucket-test", "xml-third-phase-enriched-bucket-test"]

filenames = get_filenames(processing_root, data_paths) 

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
            
            output_to_text_files(processing_root, filename, (parts, head_text, body_text))
            
            parts_values = process_parts(str(parts))
            #print(parts_values)
            
            for values in parts_values:
                pass
            
 
         
            
        else:
            not_exists_count += 1
            #print("file: " + str(file_to_check) + " does not exist")   
            
    print("Files checked: " + str(exists_count))
    print("Files mismatched: " + str(not_exists_count))
   
    