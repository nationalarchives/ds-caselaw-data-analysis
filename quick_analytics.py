from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import time
import dist_graphs as dg

'''
input_from_values_files(processing_root, pass_num = "")
analyse_refs(pkl_file, case=True, leg=True)
generate_blank_matrix(index_names)
create_graph(df, col, limit = -1, cutoff = 1, type="leg")
update_colloc_matrix(matrix, ref_list)
get_distribution(df, key)
get_root_href(href)
get_section(href)
legislation_refs(legislation_df, start_time)
case_refs (cases_df)

'''

'''
[To Do] - refactor the create_graph so the processing of the data into the nodes and edges dictionary is separated out and reading from the csv/txt outputs from previous analysis.
[To Do] - Co-reference distribution analysis
[To Do] - cluster analysis
'''



def input_from_values_files(processing_root, pass_num = ""):
    ''' Function reads in the values from the text files in the processing root
        If a pass_num is given then only get the values from that pass
    '''
    
    parts_dict = {}
    head_text_dict = {}
    body_text_dict = {}
    
    if len(pass_num) > 0:  #Get all folders
        for i in range(3):
            for file in Path(processing_root, "extracted_values", "pass" + str(i)).glob("*.txt"):  
                pass
    else:            
        for file in Path(processing_root, "extracted_values", pass_num).glob("*.txt"):  
                pass
            
    return(parts_dict, head_text_dict, body_text_dict)


def analyse_refs(pkl_file, case=True, leg=True):   
    ''' Function reads the pickle file and runs the functions of the specified types
    '''  
    references_df = pd.read_pickle(pkl_file)
    
    if case:
        cases_df = references_df[references_df['uk:type'] == "case"]
        case_refs(cases_df)
        
    if leg:
        legislation_df = references_df[references_df['uk:type'] == "legislation"] 
        legislation_refs(legislation_df, start_time)


def generate_blank_matrix(index_names):
    ''' Funcation creates a blank matrix with the index names as the columns and row values
    '''

    values = {}
    
    print(len(index_names))
    
    for name in index_names:
        if ".gov.uk/" in name:
            values[name.split(".gov.uk/")[1]] = [0] * len(index_names)
        else:
            values[name] = [0] * len(index_names)
        
    #blank_df = pd.DataFrame(values, index=[name.split(".gov.uk/")[1] for name in index_names])      
    #print(blank_df)  
    
    index = [name.split(".gov.uk/")[1] if ".gov.uk/" in name else name for name in index_names]
    
    return (values, index)
        

def create_graph(df, col, limit = -1, cutoff = 1, type="leg"):
    ''' Creates a weighted network graph based on a named column (col) in the dataframe (df). 
            If an optional limit is given then it only draws that number of rows otherwise it does all the rows. 
            Only edges with a value of the specified cutoff are drawn.
            Text files with the weighting matrix and distribution are saved.
    '''
    
    before_processing = time.time()
    
    file_list = df['file'].astype(str).unique()
    weighting = {}
    
    print(len(file_list))
    
    linked_refs_lists = []
    
    num_of_refs_distribution = {}
    
    if limit > 0:
        
        for file in file_list[0:limit]:
            temp_df = df.loc[df['file'] == file].drop_duplicates()
            #print(temp_df.head())
            leg = temp_df[col].tolist()
            linked_refs_lists += leg
            
            num_of_refs = len(leg)
            
            if num_of_refs in num_of_refs_distribution:
                num_of_refs_distribution[num_of_refs] += 1
            else:
                num_of_refs_distribution[num_of_refs] = 1
            
            if num_of_refs > 1:
                weighting = update_colloc_matrix(weighting, leg)
    else:
        for file in file_list:
            temp_df = df.loc[df['file'] == file].drop_duplicates()
            #print(temp_df.head())
            leg = temp_df[col].tolist()
            linked_refs_lists += leg
            
            num_of_refs = len(leg)
            
            if num_of_refs in num_of_refs_distribution:
                num_of_refs_distribution[num_of_refs] += 1
            else:
                num_of_refs_distribution[num_of_refs] = 1
            
            if num_of_refs > 1:
                weighting = update_colloc_matrix(weighting, leg)        
    
           
    #grouped_values = df.groupby(['file'], sort=False)   
    linked_refs_set = set(linked_refs_lists) 
    #print(weighting)
    #print(linked_refs_set)
    
    matrix_dict, index_list = generate_blank_matrix(list(linked_refs_set))
    
    weighting_distribution = {}
    nodes_and_edges = []
    
    for key_string, weighted_value in weighting.items():
        node1 = key_string.split("-")[0]
        node2 = key_string.split("-")[1] 
        
        if node2 in index_list:
            position = index_list.index(node2)
            matrix_dict[node1][position] = weighted_value
        
        if weighted_value in weighting_distribution:
            weighting_distribution[weighted_value] += 1
        else:
            weighting_distribution[weighted_value] = 1        
                 
        if weighted_value > cutoff:   
            nodes_and_edges.append({"node1":node1, "node2":node2, "weighted_value": weighted_value})
    
    dg.output_duration(before_processing, "Processing")
            
    dg.draw_weighted_graph(nodes_and_edges)        
    
    #print(matrix_dict) 
    #print(index_list)   
    weighting_df = pd.DataFrame(matrix_dict, index_list)
    weighting_distribution = dict(sorted(weighting_distribution.items()))
    num_of_refs_distribution = dict(sorted(num_of_refs_distribution.items()))
    #print(weighting_df)
    
    if limit > 0:
        weighting_df.to_csv("data/weighting_" + type + "_" + str(limit) + ".csv")
        weighting_distribution_path = Path("data", "weighting_distribution_" + type + "_" + str(limit) + ".txt")     
        num_of_refs_distribution_path = Path("data", "num_of_refs_distribution_" + type + "" + str(limit) + ".txt")
    else:
        weighting_df.to_csv("data/weighting_" + type + ".csv")
        weighting_distribution_path = Path("data", "weighting_distribution_" + type + ".txt")     
        num_of_refs_distribution_path = Path("data", "num_of_refs_distribution_" + type + ".txt")
        
    try:
        with open(weighting_distribution_path, "w", encoding="utf-8") as myfile:
            myfile.write(str(weighting_distribution))
        with open(num_of_refs_distribution_path, "w", encoding="utf-8") as myfile:
            myfile.write(str(num_of_refs_distribution))
    except IOError as e:
        print("Could not save file: " + str(e))      

    
    #print(num_of_refs_distribution)
    #print(weighting_distribution)
    
    #components = list(nx.connected_components(G))


def update_colloc_matrix(matrix, ref_list):   
    ''' function takes an existing matrix of coreferences and expands it with a list of refernces from the same source. The expanded matrix is returned '''
    for ref1 in ref_list:
        for ref2 in ref_list:
            if ref1 != ref2:
                short_ref1 = ref1
                short_ref2 = ref2
                
                if ".gov.uk/" in ref1:
                    short_ref1 = ref1.split(".gov.uk/")[1]

                if ".gov.uk/" in ref2:
                    short_ref2 = ref2.split(".gov.uk/")[1]
                
                key = short_ref1 + "-" + short_ref2
                
                if key in matrix.keys():
                    matrix[key] += 1
                else:
                    matrix[key] = 1
                    
    return matrix
               

def get_distribution(df, key):
    ''' For a given dataframe, the function groups the values by the specified column (key) and by file. Returns list with count of each key value '''
    
    sorted_cases = df.sort_values(['file', 'pass'], ascending=False)     
    list_of_refs_by_file = sorted_cases.groupby([key, 'file'], sort=False).count().sort_values(ascending=False)  #.reset_index(['count']).sort_values(['count'], ascending=False)
    
    print(list_of_refs_by_file.head())
    return list_of_refs_by_file.groupby([key], sort=False).count().sort_values(ascending=False)      


def get_root_href(href):
    ''' Function returns the base document information if section information it exists in the URL '''
        
    if "/section" in href:
        return href.split("/section")[0]
    else:
        return href


def get_section(href):
    ''' Function returns the section information if it exists in the URL '''

    if "/section" in href:
        return "/section" + href.split("/section")[1]
    else:
        return ""
     

def legislation_refs(legislation_df, start_time):
    ''' Function takes a dataframe of legislation references and analyses them '''

    # Legislation
        # Which legislation and how often
    
    legislation_df['section'] = legislation_df['href'].apply(get_section)
    legislation_df['href'] = legislation_df['href'].apply(get_root_href)
    
    #print(legislation_df.head(10))
    leg_refs = legislation_df[['file', 'href']]
    create_graph(leg_refs, 'href', limit=100, cutoff=5)
        
    #list_of_leg = get_distribution(legislation_df, 'href')
    #print(list_of_leg.head(10))
    #list_of_leg.to_csv("data/legislation.csv")
        
        # Specific reference - what and how often
        # Clustering      
   

def case_refs (cases_df):  
    ''' Function takes a dataframe of case references and analyses them ''' 
    # Case Law
        # Which cases and how often  
    #print(cases_df.head(10))
    #list_of_cases = get_distribution(cases_df, 'uk:canonical')
    
    case_refs = cases_df[['file', 'href', 'uk:canonical']]
    create_graph(case_refs, 'uk:canonical', cutoff=2)
    
    #print(list_of_cases.head(10))
    #list_of_cases.to_csv("data/cases.csv")
    
    
start_time = time.time()
processing_root = "data"
refs_pkl_file = Path(processing_root, "processing", "cache", "extracted_data_full", "ref.pkl")

dg.output_duration(start_time, "Loading")

analyse_refs(refs_pkl_file, case=True, leg=False)








    
# Dates
    # Get hearing dates
    # Get other dates
    
