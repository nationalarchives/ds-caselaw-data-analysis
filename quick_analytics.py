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

def analyse_refs(processing_root, pkl_file, columns=[], limit=100, cutoff=0, renew_data=False):   
    ''' Function reads the pickle file and runs the functions of the specified types
    '''  
    references_df = pd.read_pickle(pkl_file)

    if 'uk:type' in references_df.columns:  
        cases_df = references_df[references_df['uk:type'] == "case"]
        case_refs(processing_root, cases_df, limit=limit, cutoff=cutoff, renew_data=renew_data)
        
        #legislation_df = references_df[references_df['uk:type'] == "legislation"] 
        #legislation_refs(processing_root, legislation_df, limit=limit, cutoff=cutoff, renew_data=renew_data)

    elif len(columns) > 0:
        process_refs(processing_root, references_df, columns, limit=limit, cutoff=cutoff, renew_data=renew_data)

    else:
        print("Not enough information to analyse data")


def generate_blank_matrix(index_names):
    ''' Funcation creates a blank matrix with the index names as the columns and row values
    '''

    values = {}
    
    #print("Length of index" + str(len(index_names)))
    
    for name in index_names:
        if ".gov.uk/" in name:
            values[name.split(".gov.uk/")[1]] = [0] * len(index_names)
        else:
            values[name] = [0] * len(index_names)
        
    #blank_df = pd.DataFrame(values, index=[name.split(".gov.uk/")[1] for name in index_names])      
    #print(blank_df)  
    
    index = [name.split(".gov.uk/")[1] if ".gov.uk/" in name else name for name in index_names]
    
    return (values, index)

def load_graph_data(weighting_csv_path, cutoff = 1):
    before_loading = time.time()

    print("Load graph data called")

    nodes_and_edges = []
    #print("Loading graph data")

    weighting_df = pd.read_csv(weighting_csv_path, index_col=0)
    list_of_nodes = [*weighting_df]

    #print(weighting_df)

    #print(list_of_nodes)

    for node1 in list_of_nodes:
        for node2 in list_of_nodes:
            if node1 != node2:
                #print("Node1:" + node1 + " , Node2:" + node2)
                weighted_value = weighting_df.at[node1, node2]
                if weighted_value > cutoff:
                    nodes_and_edges.append({"node1":node1, "node2":node2, "weighted_value": int(weighted_value)})

    #print(nodes_and_edges)

    dg.output_duration(before_loading, "Loading")  

    return nodes_and_edges

def generate_graph_data(df, col, limit=-1, cutoff=1):
    before_processing = time.time()
    
    print("Generate graph data called")

    #print(df)

    file_list = df['file'].astype(str).unique()
    weighting = {}
    
    print("Number of files " + str(len(file_list)))
    
    linked_refs_lists = []    
    num_of_refs_distribution = {}
    weighting_distribution = {}
    nodes_and_edges = []
    
    # generate weighting matrix
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

    processed_data = [pd.DataFrame(matrix_dict, index_list), dict(sorted(weighting_distribution.items())), dict(sorted(num_of_refs_distribution.items()))]

    #print(matrix_dict) 
    #print(index_list) 

    dg.output_duration(before_processing, "Processing")   

    return (nodes_and_edges, processed_data)

def save_graph_data(processing_root, processed_data, limit=0, type="test"):  
    weighting_df = processed_data[0]
    weighting_distribution = processed_data[1]
    num_of_refs_distribution = processed_data[2]
    #print(weighting_df)
    
    if limit > 0:
        weighting_df.to_csv(Path(processing_root, "weighting_" + type + "_" + str(limit) + ".csv"))
        weighting_distribution_path = Path(processing_root, "weighting_distribution_" + type + "_" + str(limit) + ".txt")     
        num_of_refs_distribution_path = Path(processing_root, "num_of_refs_distribution_" + type + "" + str(limit) + ".txt")
    else:
        weighting_df.to_csv(Path(processing_root, "weighting_" + type + ".csv"))
        weighting_distribution_path = Path(processing_root, "weighting_distribution_" + type + ".txt")     
        num_of_refs_distribution_path = Path(processing_root, "num_of_refs_distribution_" + type + ".txt")

    try:
        with open(weighting_distribution_path, "w", encoding="utf-8") as myfile:
            myfile.write(str(weighting_distribution))
        with open(num_of_refs_distribution_path, "w", encoding="utf-8") as myfile:
            myfile.write(str(num_of_refs_distribution))
    except IOError as e:
        print("Could not save file: " + str(e)) 

def create_graph(processing_root, df, col, limit=-1, cutoff=1, type="test", renew_data=False):
    ''' Creates a weighted network graph based on a named column (col) in the dataframe (df). 
            If an optional limit is given then it only draws that number of rows otherwise it does all the rows. 
            Only edges with a value of the specified cutoff are drawn.
            Text files with the weighting matrix and distribution are saved.
    '''
    processed_data = []

    if limit > 0:
        weighting_csv_path = Path(processing_root, "weighting_" + type + "_" + str(limit) + ".csv")
    else:
        weighting_csv_path = Path(processing_root, "weighting_" + type + ".csv")

    #print(weighting_csv_path)

    if weighting_csv_path.exists() and renew_data == False:
        nodes_and_edges = load_graph_data(weighting_csv_path, cutoff=cutoff)
    else:
        nodes_and_edges, processed_data = generate_graph_data(df, col, limit, cutoff)
            
    dg.draw_weighted_graph(nodes_and_edges)        
    
    #print(num_of_refs_distribution)
    #print(weighting_distribution)    
    #components = list(nx.connected_components(G))

    return processed_data

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
               
def get_frequency(df, key):
    ''' For a given dataframe, the function groups the values by the specified column (key) and by file. Returns dictionary with count for each key value '''
    
    if 'pass' in df.columns:
        sorted_values = df.sort_values(['file', 'pass'], ascending=False)   
    else:
        sorted_values = df.sort_values(['file', 'data'], ascending=False)     

    #print("key:" + key)

    #print(sorted_values.head(100))

    freq_of_values_by_file = sorted_values.groupby([key, 'file'], sort=False).size().reset_index(name='size').sort_values(['size'], ascending=False)

    value_frequency_across_files = freq_of_values_by_file.groupby([key], sort=False).size().reset_index(name='freq').sort_values(by='freq', ascending=False) 
    #print(value_frequency_across_files)

    keys = value_frequency_across_files[key].tolist()
    values = value_frequency_across_files['freq'].tolist()

    return dict(zip(keys, values)) 

# Helper functions

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

# Analysis

def legislation_refs(processing_root, legislation_df, limit=100, cutoff=5, renew_data=False):
    ''' Function takes a dataframe of legislation references and analyses them '''

    print("Legislation refs called")
    # Legislation
        # Which legislation and how often
    
    legislation_df['section'] = legislation_df['href'].apply(get_section)
    legislation_df['href'] = legislation_df['href'].apply(get_root_href)
    
    #print(legislation_df.head(10))
    leg_refs = legislation_df[['file', 'href']]
    create_graph(processing_root, leg_refs, 'href', limit, cutoff, "legislation", renew_data)
        
    list_of_leg = get_frequency(legislation_df, 'href')
    dg.draw_bar_graph(list_of_leg) 

    #print(list_of_leg.head(10))
    #list_of_leg.to_csv("data/legislation.csv")
        # Specific reference - what and how often
        # Clustering      
   
def case_refs (processing_root, cases_df, limit=100, cutoff=2, renew_data=False):  
    ''' Function takes a dataframe of case references and analyses them ''' 
    # Case Law
        # Which cases and how often  
    #print(cases_df.head(10))

    print("Case refs called")

    list_of_cases = get_frequency(cases_df, 'uk:canonical')
    dg.draw_bar_graph(list_of_cases) 
    
    case_refs = cases_df[['file', 'href', 'uk:canonical']]
    create_graph(processing_root, case_refs, 'uk:canonical', limit, cutoff, "case", renew_data)
    
    #print(list_of_cases.head(10))
    #list_of_cases.to_csv("data/cases.csv")

def process_refs (processing_root, df, columns, limit=100, cutoff=2, type="test", renew_data=False):
    ''' Runs analysis on general dataframe of data. 
    '''

    refs = df[columns]

    graph_data = create_graph(processing_root, refs, columns[-1], limit, cutoff, type, renew_data)

    if len(graph_data) > 0:
        save_graph_data(processing_root, graph_data, limit, type)

    refs_frequency = get_frequency(df, columns[-1])
    dg.draw_bar_graph(refs_frequency)  

    #print(list_of_refs)

# Main

#def main(processing_root, pickle_file, folders, case=True, leg=True, renew_data=False):    
    #start_time = time.time()
    #dg.output_duration(start_time, "Loading")
    #analyse_refs(processing_root, pickle_file, folders, case, leg, renew_data)


if __name__ == '__main__':
    processing_root = "data"

    refs_pkl_file = Path(processing_root, "processing", "cache", "extracted_data", "ref.pkl")
    test_pkl_file = Path(processing_root, "processing", "test", "cache", "extracted_data", "ref.pkl")

    folders = ['file', 'href']

    #analyse_refs(processing_root, test_pkl_file, folders, renew_data=False)
    analyse_refs(processing_root, refs_pkl_file, limit=100, cutoff=0, renew_data=False)






    
# Dates
    # Get hearing dates
    # Get other dates
    
