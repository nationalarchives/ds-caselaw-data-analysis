
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
import json, os, datetime, time
import pandas as pd
import matplotlib

def load_replacement_data (processing_folder):
    ''' load data in from folder store it in the appropriate dataframe and save the dataframe
    '''
    # Read in txt files from the data/replacements-bucket
    # Read in each line and put into appropriate dataframe

    data_values = {}
    column_values = {"case": ["file", "last_modified", "citation_match", "corrected_citation/citation_match", "year", "URI", "is_neutral"], "leg":["file", "last_modified", "detected_ref", "href", "canonical_form"], "abb": ["file", "last_modified", "initials", "expanded"]}

    if not any(Path(processing_folder, "cache").glob("*.pkl")):
        try: 
            for file in Path(processing_folder).glob("*.txt"):     
    
                base_filename = Path(file).stem
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
                df2.to_pickle(Path(processing_folder, "cache", key + ".pkl"))
                data_values[key] = df2
                    
        except OSError as e:
            print("Error in data loading: " + e)
    else:
        #print(Path(processing_folder, "cache"))
        
        for file in Path(processing_folder, "cache").glob("*.pkl"):   
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


def get_cases_references(cases):    
    list_of_cases = cases.groupby(['corrected_citation/citation_match', 'URI']).size()

    print(list_of_cases.head)
    #print(cases.head)  


processing_folder = "data/processing"
datasets = load_replacement_data(processing_folder)


#for name, dataset in datasets.items():
#    plot_dates(dataset)


#get_legislation_references(datasets['leg'])
#get_cases_references(cases = datasets['case'])

