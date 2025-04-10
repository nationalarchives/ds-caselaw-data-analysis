
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
import json, os, datetime, time, re
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

    data_values = {}
    column_values = {"case": ["file", "last_modified", "citation_match", "corrected_citation/citation_match", "year", "URI", "is_neutral"], 
                     "leg":["file", "last_modified", "detected_ref", "href", "canonical_form"], 
                     "abb": ["file", "last_modified", "initials", "expanded"],
                     "judgment":["file", "last_modified", "hearing_date_1", "hearing_date_2", "judgment_date"]
                    }

    if not any(Path(cache_path).glob("*.pkl")):
        try: 
            for file in Path(data_path).glob("*.txt"):     
    
    
                
                base_filename = Path(file).stem
                
                dates = get_date_values(processing_root + "/xml-enriched-bucket", base_filename)
                temp_list = [base_filename, last_modified] + dates[]
                
                if base_filename[0] == "-":
                    base_filename = base_filename[1:] + "_2"
                    
                print("Processing file:" + str(base_filename))   

                file_date = datetime.datetime.strptime(time.ctime(os.path.getmtime(file)), "%a %b %d %H:%M:%S %Y")
                last_modified = file_date.strftime('%Y-%m-%d')            
                            
                with open(file, 'r') as replacements_file:
                    for line in replacements_file.readlines():
                        temp_dict = json.loads(line)
                        dict_keys = temp_dict.keys()                    
                        
                        for key in dict_keys:
                            temp_list = [base_filename, last_modified] + temp_dict[key]
                            #print(temp_list)
                            
                            if key in data_values.keys():
                                df = data_values[key]
                                df.loc[len(df)] = temp_list
                            else:
                                df = pd.DataFrame([temp_list], columns=column_values[key])
                                data_values[key] = df
                                
                                
                                
            for key, df in data_values.items():
                df2 = df.groupby(df.columns.tolist(), as_index=False).size()
                #print(df.to_string())
                #df2.to_pickle(Path(cache_path, key + ".pkl"))
                data_values[key] = df2
                    
        except OSError as e:
            print("Error in data loading: " + str(e))
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
    list_of_leg = legislation.groupby(['detected_ref', 'href']).size()
    file_leg = legislation.groupby(['detected_ref', 'file']).size()

    print(list_of_leg.head)
    print(file_leg.head)
    
    list_of_leg.to_csv("data/leg.csv")
    file_leg.to_csv("data/file_leg.csv")


def get_cases_references(cases):    
    list_of_cases = cases.groupby(['corrected_citation/citation_match', 'URI']).size()

    print(list_of_cases.head)
    #print(cases.head)  
    
    list_of_cases.to_csv("data/cases.csv")

def get_date_values(folder, filename):
    print(Path(folder, filename + ".xml"))
    
    data = {}
    
    tree = et.parse(Path(folder, filename + ".xml"))
    root = tree.getroot()
    
    text = et.tostring(root, encoding='utf-8').decode()
    
    #Path("data/processing/text.txt").write_text(text)
    
    ns = re.match(r'{.*}', root.tag).group(0)
    
    judgment_date_string = tree.find(f".//{ns}FRBRWork/{ns}FRBRdate[@name='judgment']").get('date')
    
    if judgment_date_string != "":
        try:
            data["judgment date"] = datetime.datetime.strptime(judgment_date_string, '%Y-%m-%d')
        except ValueError as e:
            print("Error in judgment date extraction in " + filename + ".xml: " + str(e))
    
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
                data["hearing date_1"] = datetime.datetime.strptime(hearing_date_string1, '%d %B %Y')
                data["hearing date_2"] = datetime.datetime.strptime(hearing_date_string2, '%d %B %Y')
                
            else:
                hearing_date_string = day + " " + month + " " + year
                data["hearing date_1"] = datetime.datetime.strptime(hearing_date_string, '%d %B %Y')
                data["hearing date_2"] = ""
                
        except ValueError as e:
            match_results = str(m) + "\nGroup 1:\n" + str(m.group(1)) + "\nGroup 2\n" + str(m.group(2)) + "\nGroup 3:\n" + str(m.group(3)) + "\nGroup 4:\n" + str(m.group(4)) + "\nGroup 5:\n" + str(m.group(5)) + "\nGroup 6:\n" + str(m.group(6))  
            
            print("Error in hearing date extraction in " + filename + ".xml. '" + match_results + "': " + str(e))
            
    else:
        print("No match found in " + filename + ".xml")

    #print(data)
    return data
    


processing_root = "data"
#data_folder = "replacements-bucket"
data_folder = "test-data"

datasets = load_replacement_data(processing_root, data_folder)


#for name, dataset in datasets.items():
#    plot_dates(dataset)

'''
if 'leg' in datasets.keys():
    get_legislation_references(datasets['leg'])

if 'case' in datasets.keys():    
    get_cases_references(datasets['case'])
'''
