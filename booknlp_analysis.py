from pathlib import Path
import pandas as pd
from dateparser.search import search_dates
import dist_graphs as dg
from datetime import datetime
import jenkspy
from findpeaks import findpeaks
import numpy as np
import re

def clean_files(data_folder):

    for file in data_folder.glob("*.tokens.tsv"):  
        with open(file, "r", encoding='utf-8') as orig_file:
            cleaned_file = orig_file.read().replace('“','"').replace('”','"')

        with open(file, "w", encoding='utf-8') as new_file:
            new_file.write(cleaned_file)

def clean_file(file):
    with open(file, "r", encoding='utf-8') as orig_file:
        cleaned_file = orig_file.read().replace('“','"').replace('”','"')

    with open(file, "w", encoding='utf-8') as new_file:
        new_file.write(cleaned_file)

def include_dates(possible_dates):

    dates = []
    months = {'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'}
    #print(possible_dates)

    for poss_date in possible_dates:
        text, date = poss_date

        #print("Checking: " + text)

        words = text.split()

        if len(words) > 1:
            matches = months.intersection(set(words))
            if len(matches) > 0:
                dates.append((text, date))

    #print(dates)
    return dates

def get_events(data_folder, regen=False):
    dataframes = {}
    events_by_file = {}

    for file in data_folder.glob("*.tokens"):  
        filename = Path(file).stem
        print("Processing " + filename)

        if (Path(data_folder, filename+".pkl").exists() and regen == False):
            print("Loading values from pkl")
            df = pd.read_pickle(Path(data_folder, filename+".pkl"))
            dataframes[filename] = df
            #print(df.info())
        else:
            print("Reading values from TSV")
            clean_file(file)
            df = pd.read_csv(file, delimiter="\t")             
            dataframes[filename] = df
            #print(df.info())
            df.to_pickle(Path(data_folder, filename+".pkl"))

    for file, df in dataframes.items():
        if Path(data_root, file + "_events.csv").exists() and regen == False:
            print("Loading existing timeline values from CSV")
            processed_data = pd.read_csv(Path(data_root, file + "_events.csv"))
            #print(processed_data)
            loaded_events = processed_data.to_dict()
            possible_events = []
            for i in range(0, len(loaded_events['line_num'])):
                possible_events.append({"line_num": loaded_events['line_num'][i], "dates": [(loaded_events['date_text'][i], datetime.strptime(loaded_events['date'][i], "%Y-%m-%d"))], "line": loaded_events['line'][i], "complex": False})

            #print(possible_events)
            events_by_file[file] = possible_events
        else:
            print("Generating timeline")
            possible_events = []
            #print("For " + file)
            events = df[~df['event'].isnull()]
            found_events = events.loc[df["event"] == "EVENT"]
            #event_words = set(found_events.word.tolist())
            #print(event_words)
            sentences = list(set(found_events.sentence_ID.tolist()))
            sentences.sort()

            for event_sentence in sentences:
                event = df[df["sentence_ID"] == int(event_sentence)]
                words = event.word.tolist()
                resentence = " ".join(words)
                dates = search_dates(resentence)

                if dates:
                    filtered_dates = include_dates(dates)
                    if len(filtered_dates) > 1:
                        possible_events.append({"line_num": event_sentence, "dates": filtered_dates, "line": resentence, "complex": True})
                    elif len(filtered_dates) > 0:
                        possible_events.append({"line_num": event_sentence, "dates": filtered_dates, "line": resentence, "complex": False})

            events_by_file[file] = possible_events
        #print(len(events_by_file[file]))
        #print(events_by_file[file][0])

    return (events_by_file)

def date_cluster_analysis(timeline_path, filename="", merge_gap = 30, graph_split = 182):

    timeline = pd.read_csv(timeline_path)
    timeline['date'] = pd.to_datetime(timeline['date'])
    timeline.sort_values(by=['date'], inplace=True)
    timeline['converted_dates'] = timeline['date'].values.astype(np.int64) // 10 ** 9
    #timeline['converted_dates'] = pd.to_numeric(timeline['converted_dates'])
    date_numbers = timeline['converted_dates'].to_list()
    dates = timeline['date'].to_list()
    dates_no_dups = list(set(dates)) 
    dates_no_dups.sort()

    #print("dates no dups: " + str(dates_no_dups))
    #print("dates as numbers: " + str(date_numbers))

    gaps = []
    gap_positions = {}


    for i in range(0, len(dates_no_dups)):
        if i+1 < len(dates_no_dups):
            time_diff = dates_no_dups[i+1] - dates_no_dups[i]
            gaps.append(time_diff.days)
            gap_positions[i] = time_diff.days

    gaps.sort()    
    #print(gaps)
    #print(gap_positions)

    if len(dates_no_dups) > 1:
        fp = findpeaks(method='topology')
        results = fp.fit(list(gap_positions.values()))

        data = results['df']    
        #print(data)
        #fp.plot()
        peak_count = data[data['score'] > 0].count()['score']
        #print(peak_count)
        #dg.draw_plot_graph(gap_positions, title=filename)

        jnb = jenkspy.JenksNaturalBreaks(int(peak_count) + 1)

        dates_as_numbers = list(set(date_numbers))
        #print("dates: " + str(dates_as_numbers))
        jnb.fit(dates_as_numbers)
        groups = jnb.groups_

        merged_groups = [groups[0]]
        for i in range(0, len(groups)):
            last_date_in_group = datetime.fromtimestamp(groups[i][-1])
            if i+1 < len(groups):
                first_date_in_next_group = datetime.fromtimestamp(groups[i+1][0])
                gap = first_date_in_next_group - last_date_in_group
                #print("Last date: " + str(last_date_in_group) + ", Next date: " + str(first_date_in_next_group) + ", Gap: " + str(gap.days))

                if int(gap.days) < merge_gap:
                    #print("Before Merge" + str(merged_groups))
                    new_group = np.concatenate((merged_groups[-1], groups[i+1]))
                    new_group = np.sort(new_group)
                    merged_groups[-1] = new_group
                    #print("After Merge" + str(merged_groups))
                else:
                    merged_groups.append(groups[i+1])

        #print("Merged: " + str(merged_groups))

        first_group = [datetime.fromtimestamp(x) for x in merged_groups[0]]
        date_groups = [first_group]
        for i in range(0, len(merged_groups)):
            #print("Loop: " + str(i) + "/" + str(len(merged_groups)))
            print("Before: " + str(date_groups))
            last_date_in_group = datetime.fromtimestamp(merged_groups[i][-1])
            if i+1 < len(merged_groups):
                first_date_in_next_group = datetime.fromtimestamp(merged_groups[i+1][0])
                diff = first_date_in_next_group - last_date_in_group
                gap = diff.days
                #print("Last date: " + str(last_date_in_group) + ", Next date: " + str(first_date_in_next_group) + ", Gap: " + str(gap))
                
                date_group = [datetime.fromtimestamp(x) for x in merged_groups[i+1]]
                date_group.sort()
                print(date_group)

                if gap > graph_split:
                    print("Append")
                    date_groups.append([date_group])
                else:
                    print("Current Group: " + str(date_groups[-1]))
                    print(len(date_groups[-1]))
                    if isinstance(date_groups[-1][0], list):
                        date_groups[-1].append(date_group)
                    else:
                        date_groups[-1] = [date_groups[-1], date_group]
                    print("Join")

            print("After: " + str(date_groups))


    else:
        date_groups = [[dates_no_dups]]
        
    #print(date_groups)
    return(date_groups)
    

def cluster_text():
    pass

def niave_text_reduction(event_values):
    date_text = event_values['date_text']
    line = event_values['line']
    date_text = date_text.strip()

    #print(date_text)
    #print(line)

    text_sections = line.split(date_text)
    text_sections = [x for x in text_sections if x]

    start = text_sections[0].strip()

    #print(text_sections)

    if len(text_sections) > 1:
        end = text_sections[1].strip()
        date_text = date_text.lower()

        if len(end) < 2 or end[0] == "," or end[0] == ".":
            #print("shorten 1: " + start)
            return start
        elif start[-1] == "," or start[-1] == ".":
            #print("shorten 2: " + end)
            return end
        elif 'on ' in date_text or start[-2:].lower() == 'on':
            #print("shorten 3: " + start)
            return start
        elif 'the' in date_text or start[-3:].lower() == 'the':
            #print("shorten 4: " + end)
            return end
        elif start[-5:].lower() == 'dated':
            #print("shorten 5: " + start)
            return start
        elif re.search(r'\(\s*\w\s*\)', start) or re.search(r'\(\s*\w\s*\)', end):
            short_start = start
            short_end = end
            if re.search(r'\(\s*\w\s*\)([\w\s,]*)$', start):
                short_start = re.search(r'\(\s*\w\s*\)([\w\s]*)$', start).group(1)

            if re.search(r'^([\w\s;,]*)\(\s*\w\s*\)', end):
                short_end = re.search(r'^([\w\s;,]*)\(\s*\w\s*\)', end).group(1)

            #print("shorten 6: " + short_start + " " + short_end)
            return short_start + " " + short_end   
        else:
            short_start = start
            short_end = end

            short_start = re.search(r'[^\w\s]\s*([\w\s]*)$', start).group(1)
            short_end = re.search(r'^([\w\s]*)[^\w\s]', end).group(1)

            #print("shorten 7: " + short_start + " " + short_end )
            return short_start + " " + short_end 
    else:
        #print("shorten 6: " + start)
        return start


def combine_events_by_date(event_values):

    combined_labels = {}

    if len(event_values['dates']) != len(event_values['labels']):
        raise Exception("Date mismatch between dates and labels")

    dated_events = zip(event_values['dates'], event_values['labels'])

    for event in dated_events:
        if event[0] in combined_labels.keys():
            combined_labels[event[0]] += " | " + event[1]
        else:
            combined_labels[event[0]] = event[1]

    return combined_labels


if __name__ == '__main__':
    data_root = Path("..", "booknlp", "output")
    #clean_files(data_root)

    events = get_events(data_root)

    for filename, events_for_file in events.items():

        #with open(Path(data_root, filename + "_events.txt"), "w", encoding='utf-8') as txt_file:
        #    txt_file.write(str(events_for_file))

        # Broken: eat-2022-1_body, eat-2022-4_body
        # Needs Tweaks: eat-2022-5_body
        if filename == "-eat-2022-2_body" or filename == "eat-2022-3_body" or filename == "eat-2022-5_body":
            #print(events_for_file[0])
            print(filename + ": num of dated Events:" + str(len(events_for_file)))
            simple_events = [event for event in events_for_file if event['complex'] == False]
            simple_events = [{"line_num": event['line_num'], "date_text": event['dates'][0][0], "date": event['dates'][0][1], "line": event['line'].strip()} for event in simple_events]
            #print(simple_events)
            #print(filename + ": num of Simple Events:" + str(len(simple_events)))
            events_df = pd.DataFrame.from_dict(simple_events)
            #print(events_df)

            #print(events_df.info())
            events_df['shortened_text'] = events_df.apply(niave_text_reduction, axis=1)

            #print(filename)
            #print(events_df)
            

            events_df = events_df.sort_values(by=['date'])
            events_df.to_csv(Path(data_root, filename + "_events.csv"), index=False)

            event_values = {"dates": events_df['date'].to_list(), "labels": events_df['shortened_text'].to_list()}
            #print(event_values)
            #dg.draw_timeline(event_values)

            combined_events = combine_events_by_date(event_values)
            #print("Combined Events: " + str(combined_events))

            #print({"dates": list(combined_events.keys()), "labels": list(combined_events.values())})

            #dg.draw_timeline({"dates": list(combined_events.keys()), "labels": list(combined_events.values())})
            

            grouped_events = date_cluster_analysis(Path(data_root, filename + "_events.csv"), filename, merge_gap=30, graph_split=182)
            print("Grouped Events: " + str(grouped_events))
            #print("Labels: " + str(list(combined_events.values())))

            dg.draw_grouped_timeline({"dates": grouped_events, "labels": list(combined_events.values())}, title=filename.split('_body')[0], save_path=Path(data_root, filename.split('_body')[0] + ".png"))



            
    
