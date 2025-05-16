import xml.etree.ElementTree as et
from pathlib import Path
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
    

def parse_file(folder, filename):
    get_text_transform_file = Path("data", "xslt", "get_text.xsl")
    get_parts_transform_file = Path("data", "xslt", "get_parts.xsl")
    
    xml_file = Path(folder, filename + ".xml") 

    try:
        tree = et.parse(xml_file)       
    except et.ParseError as e:
        with open("data/errors-ParsingError.txt", "a") as myfile:
            myfile.write("Parser error in " + filename + ".xml: " + str(e) + "\n")
        
        shutil.move(Path(folder, filename + ".xml"), Path(folder, "ParsingError", filename + ".xml"))    
        
    #root = tree.getroot()  
    
    get_text_transform = et.XSLT(get_text_transform_file)  
    get_parts_transform = et.XSLT(get_parts_transform_file)  
    
    text = get_text_transform(xml_file)
    parts = get_parts_transform(xml_file)
     


processing_root = "data"
data_paths = ["xml-enriched-bucket", "xml-second-phase-enriched-bucket", "xml-third-phase-enriched-bucket"]

filenames = get_filenames(processing_root, data_paths)

for data_path in data_paths:
    count = len(list(Path(processing_root, data_path).glob("*.xml")))
    print("Processing folder: " + data_path + "(" + str(count) + " files)")
    
    exists_count = 0
    not_exists_count = 0
        
    for filename in filenames: 
          
    #    data = {}
        
        folder_path = Path(processing_root, data_path)
        
        #xml_file1 = Path(processing_root, folder1, filename + ".xml") 
        #xml_file2 = Path(processing_root, folder2, filename + ".xml") 
        #xml_file3 = Path(processing_root, folder3, filename + ".xml") 
        
        file_to_check = Path(str(folder_path), str(filename) + ".xml")
        
        if file_to_check.exists():
            exists_count += 1
            parse_file(folder_path, filename)
            #print("file: " + str(file_to_check) + " exists") 
        else:
            not_exists_count += 1
            #print("file: " + str(file_to_check) + " does not exist")   
            
    print("Files checked: " + str(exists_count))
    print("Files mismatched: " + str(not_exists_count))
   
    