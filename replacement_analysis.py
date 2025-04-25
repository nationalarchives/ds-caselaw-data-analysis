
# Read replacement data into pandas dataframes - case, leg and abbrev

# Case
# citation_match, citation_match, year, URI, is_neutral
# citation_match, corrected_citation, year, URI, is_neutral

# Leg
# detected_ref, href, canonical_form

# Abbrev
# initials, expanded

#filename - if - at start then rerun

from pathlib import Path
import json, os, datetime, time, re, shutil
import pandas as pd
import matplotlib
import xml.etree.ElementTree as et

def load_replacement_data (processing_root, folder):
    ''' load data in from folder store it in the appropriate dataframe and save the dataframe
    '''
    # Read in txt files from the data/replacements-bucket
    # Read in each line and put into appropriate dataframe
    
    data_path = processing_root + "/processing/" + folder
    cache_path = processing_root + "/processing/cache"
    date_error = 0
    date_not_found = 0
    parsing_error = 0
    processing = 0
    duplication = 0
    no_match = 0
    

    data_values = {}
    column_values = {"case": ["file", "pass", "last_modified", "citation_match", "corrected_citation/citation_match", "year", "URI", "is_neutral"], 
                     "leg":["file", "pass", "last_modified", "detected_ref", "href", "canonical_form"], 
                     "abb": ["file", "pass", "last_modified", "initials", "expanded"]
                    }
    move_list = []

    if not any(Path(cache_path).glob("*.pkl")):
        try: 
            for file in Path(data_path).glob("*.txt"):     
                processing += 1
                
                base_filename = Path(file).stem
                
                pass_num = 1
                
                if base_filename[0] == "-":
                    base_filename_trimmed = base_filename[1:]
                    pass_num = 2
                    duplication += 1
                    
                print("Processing file:" + str(base_filename))   

                file_date = datetime.datetime.strptime(time.ctime(os.path.getmtime(file)), "%a %b %d %H:%M:%S %Y")
                last_modified = file_date.strftime('%Y-%m-%d')         
                            
                with open(file, 'r') as replacements_file:
                    for line in replacements_file.readlines():
                        temp_dict = json.loads(line)
                        dict_keys = temp_dict.keys()                    
                        
                        for key in dict_keys:
                            temp_list = [base_filename_trimmed, pass_num, last_modified] + temp_dict[key]
                            #print(temp_list)
                            
                            if key in data_values.keys() and key != "dates":
                                df = data_values[key]
                                df.loc[len(df)] = temp_list
                            else:
                                df = pd.DataFrame([temp_list], columns=column_values[key])
                                data_values[key] = df
                
                xml_file = Path(processing_root + "/xml-enriched-bucket", base_filename + ".xml") 
                
                if xml_file.is_file():               
                    (dates, p_error, no_date, d_error) = get_date_values(processing_root + "/xml-enriched-bucket", base_filename, data_path)
                    date_error += d_error
                    date_not_found += no_date
                    parsing_error += p_error
                    dates_temp_list = [base_filename_trimmed, pass_num, last_modified, dates["hearing_date_1"], dates["hearing_date_2"], dates["judgment_date"]]   
                    
                    if "dates" in data_values.keys():      
                        dates_df = data_values["dates"]
                        #print(dates_df.to_string())
                        #print(dates_temp_list)
                        dates_df.loc[len(dates_df)] = dates_temp_list
                    else:
                        dates_df = pd.DataFrame([dates_temp_list], columns=["file", "pass", "last_modified", "hearing_date_1", "hearing_date_2", "judgment_date"])
                        data_values["dates"] = dates_df
                else:
                    with open("data/errors-NoMatchingFile.txt", "a") as myfile:
                        myfile.write("Could not find " + base_filename + ".xml\n")  
                    
                    no_match += 1    
                    move_list.append(base_filename + ".txt")                    
            
            for file_to_move in move_list:
                try:
                    #print("Moving " + str(Path(data_path, file_to_move)) + " to " + str(Path(data_path, "NoMatchingFile", file_to_move)))
                    shutil.move(Path(data_path, file_to_move), Path(data_path, "NoMatchingFile", file_to_move))   
                except Exception as e:
                    print("Could not copy " + str(Path(data_path, file_to_move)) + " to " + str(Path(data_path, "NoMatchingFile", file_to_move)) + ": " + str(e))
                                
            for key, dfs in data_values.items():
                remove_dups = dfs.groupby(dfs.columns.tolist(), as_index=False).size()
                #print(df.to_string())
                #print(remove_dups.to_string())
                
                #remove_dups.to_pickle(Path(cache_path, key + ".pkl"))
                data_values[key] = remove_dups
                    
        except OSError as e:
            print("Error in data loading: " + str(e))
            
            
        print("Processed " + str(processing) + " files (" + str(duplication) + " repeats)")
        print("XML files not parsable: " + str(parsing_error))
        print("Dates not found: " + str(date_not_found))
        print("Date extraction error: " + str(date_error))
    else:
        #print(Path(processing_folder, "cache"))
        
        for file in Path(cache_path).glob("*.pkl"):   
            base_filename = Path(file).stem
            
            print("Reading file:" + str(base_filename))   
            
            df = pd.read_pickle(file)
            
            #print(df.to_string())
                       
            data_values[base_filename] = df
            
    return data_values



def plot_dates (df):
    
    #file_date = df[["last_modified", "size"]]
    #fig, axs = plt.subplots(figsize=(12, 4))
    
    file_date = df[pd.to_datetime(df['last_modified']), pd.to_numeric(df['size'])]
    
    #print(file_date.head)
    
    file_date.plot.scatter(title="dates", x="last_modified", y="size")
    
    #print(file_date.shape)
    #print(file_date.head)


def get_legislation_references(legislation):  
    
    sorted_leg = legislation.sort_values(['file', 'pass'], ascending=False)
    filtered_leg = sorted_leg.drop_duplicates(['file', 'detected_ref'], keep="first")

    #print("Filtered:")
    #print(filtered_leg.head)    
     
    list_of_leg_by_file = filtered_leg.groupby(['file', 'detected_ref', 'href', 'size'], sort=False).size()
    
    #legislation_reduced_columns = filtered_leg['detected_ref', 'href', 'size']
    
    list_of_leg = filtered_leg.groupby(['detected_ref', 'href', 'canonical_form'], sort=False)['size'].sum()


    #print("By File:")
    #print(list_of_leg_by_file.head)
    
    #print("Leg:")
    #print(list_of_leg.head)
    
    #print(file_leg.head)
    
    list_of_leg.to_csv("data/leg.csv")
    list_of_leg_by_file.to_csv("data/file_leg.csv")


def get_cases_references(cases):    
    
    sorted_cases = cases.sort_values(['file', 'pass'], ascending=False)
    
    filtered_cases = sorted_cases.drop_duplicates(['file', 'corrected_citation/citation_match'], keep="first")
    
    list_of_cases = filtered_cases.groupby(['corrected_citation/citation_match', 'URI']).size()

    #print(list_of_cases.head)
    #print(cases.head)  
    
    list_of_cases.to_csv("data/cases.csv")


def get_date_references(dates):

    sorted_dates = dates.sort_values(['file', 'pass'], ascending=False)
    
    filtered_dates = sorted_dates.drop_duplicates(['file'], keep="first") 
    
    #print(filtered_dates.head)   
    
    filtered_dates.to_csv("data/dates.csv")
    

def get_date_values(xml_folder, filename, processing_folder=""):
    #print(Path(folder, filename + ".xml"))
    
    date_error = 0
    date_not_found = 0
    parsing_error = 0
    data = {}
    try:
        tree = et.parse(Path(xml_folder, filename + ".xml"))
    except et.ParseError as e:
        with open("data/errors-ParsingError.txt", "a") as myfile:
            myfile.write("Parser error in " + filename + ".xml: " + str(e) + "\n")
        parsing_error += 1
 
        if processing_folder != "":
            try:
                #print("Copying " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "ParsingError", filename + ".txt")))
                shutil.copyfile(Path(processing_folder, filename + ".txt"), Path(processing_folder, "ParsingError", filename + ".txt")) 
                shutil.copyfile(Path(xml_folder, filename + ".xml"), Path(xml_folder, "ParsingError", filename + ".xml")) 
            except Exception as e:
                print("Could not copy " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "ParsingError", filename + ".txt")) + ": " + str(e))
        
        return ({"judgment_date":"", "hearing_date_1":"", "hearing_date_2":""}, parsing_error, date_not_found, date_error)
        
    root = tree.getroot()
    
    text = et.tostring(root, encoding='utf-8').decode()
    
    #Path("data/processing/text.txt").write_text(text)
    
    if m := re.match(r'{.*}', root.tag):
        ns = m.group(0)
    else:
        with open("data/errors-ParsingError.txt", "a") as myfile:
            myfile.write("Could not find namespaces in " + filename + ".xml\n")
        parsing_error += 1
            
        if processing_folder != "":
            try:
                #print("Copying " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "ParsingError", filename + ".txt")))
                shutil.copyfile(Path(processing_folder, filename + ".txt"), Path(processing_folder, "ParsingError", filename + ".txt"))
                shutil.copyfile(Path(xml_folder, filename + ".xml"), Path(xml_folder, "ParsingError", filename + ".xml")) 
            except Exception as e:
                print("Could not copy " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "ParsingError", filename + ".txt")) + ": " + str(e))
        
        return ({"judgment_date":"", "hearing_date_1":"", "hearing_date_2":""}, parsing_error, date_not_found, date_error)       
    
    judgment_date_string = ""
    
    for date_node in tree.findall(f".//{ns}FRBRWork/{ns}FRBRdate[@name='judgment']"):
        if judgment_date_string == "":
            judgment_date_string = date_node.get('date')
    
    if judgment_date_string != "":
        try:
            data["judgment_date"] = datetime.datetime.strptime(judgment_date_string, '%Y-%m-%d')
        except ValueError as e:
            with open("data/errors-DateError.txt", "a") as myfile:
                myfile.write("Error in judgment date extraction in " + filename + ".xml: " + str(e) + "\n")
                
            data["judgment_date"] = ""
            date_error += 1
            
            if processing_folder != "":
                try:
                    #print("Copying " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateError", filename + ".txt")))
                    shutil.copyfile(Path(processing_folder, filename + ".txt"), Path(processing_folder, "DateError", filename + ".txt"))
                    shutil.copyfile(Path(xml_folder, filename + ".xml"), Path(xml_folder, "DateError", filename + ".xml")) 
                except Exception as e:
                    print("Could not copy " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateError", filename + ".txt")) + ": " + str(e))
                
    else:
        data["judgment_date"] = ""
    
    if m := re.search(r'Hearing\s+date:?\s+(\d+)([&;a-z\-\s]+)?(\d+)?\s*(<[\w\W]*?>)?\s*(\w+)\s+(\d+)', text):
        day = m.group(1)
        day2 = m.group(3)
        month = m.group(5)
        year = m.group(6)
        #print("Match found in " + filename + ".xml")

        try:        
            if day2 != None:
                hearing_date_string1 = day + " " + month + " " + year
                hearing_date_string2 = day2 + " " + month + " " + year 
                data["hearing_date_1"] = datetime.datetime.strptime(hearing_date_string1, '%d %B %Y')
                data["hearing_date_2"] = datetime.datetime.strptime(hearing_date_string2, '%d %B %Y')
                
            else:
                hearing_date_string = day + " " + month + " " + year
                data["hearing_date_1"] = datetime.datetime.strptime(hearing_date_string, '%d %B %Y')
                data["hearing_date_2"] = ""
                
        except ValueError as e:
            match_results = str(m) + "\nGroup 1:\n" + str(m.group(1)) + "\nGroup 2\n" + str(m.group(2)) + "\nGroup 3:\n" + str(m.group(3)) + "\nGroup 4:\n" + str(m.group(4)) + "\nGroup 5:\n" + str(m.group(5)) + "\nGroup 6:\n" + str(m.group(6))  
            
            with open("data/errors-DateError.txt", "a") as myfile:
                myfile.write("Error in hearing date extraction in " + filename + ".xml. '" + match_results + "': " + str(e) + "\n")
            data["hearing_date_1"] = ""
            data["hearing_date_2"] = ""
            date_error += 1
               
            if processing_folder != "":
                try:
                    #print("Copying " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateError", filename + ".txt")))
                    shutil.copyfile(Path(processing_folder, filename + ".txt"), Path(processing_folder, "DateError", filename + ".txt"))
                    shutil.copyfile(Path(xml_folder, filename + ".xml"), Path(xml_folder, "DateError", filename + ".xml")) 
                except Exception as e:
                    print("Could not copy " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateError", filename + ".txt")) + ": " + str(e))                               
            
    else:
        with open("data/errors-DateNotFound.txt", "a") as myfile:
            myfile.write("No hearing date match found in " + filename + ".xml\n")
        data["hearing_date_1"] = ""
        data["hearing_date_2"] = ""    
        date_not_found += 1
        
        if processing_folder != "":
            try:
                #print("Copying " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateNotFound", filename + ".txt")))
                shutil.copyfile(Path(processing_folder, filename + ".txt"), Path(processing_folder, "DateNotFound", filename + ".txt"))
                shutil.copyfile(Path(xml_folder, filename + ".xml"), Path(xml_folder, "DateNotFound", filename + ".xml")) 
            except Exception as e:    
                print("Could not copy " + str(Path(processing_folder, filename + ".txt")) + " to " + str(Path(processing_folder, "DateNotFound", filename + ".txt")) + ": " + str(e))

    #print(data)
    return (data, parsing_error, date_not_found, date_error)
    


open("data/errors-DateNotFound.txt", 'w').close()
open("data/errors-DateError.txt", 'w').close()
open("data/errors-ParsingError.txt", 'w').close()
open("data/errors-NoMatchingFile.txt", 'w').close()

processing_root = "data"
#data_folder = "replacements-bucket"
data_folder = "test-data"

datasets = load_replacement_data(processing_root, data_folder)


#for name, dataset in datasets.items():
#    plot_dates(dataset)


#if 'leg' in datasets.keys():
#    get_legislation_references(datasets['leg'])


#if 'case' in datasets.keys():    
#    get_cases_references(datasets['case'])

if 'dates' in datasets.keys(): 
    get_date_references(datasets['dates'])

