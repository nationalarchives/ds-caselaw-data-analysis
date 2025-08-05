from pathlib import Path
import pandas as pd
from dateparser.search import search_dates
import dist_graphs as dg
from datetime import datetime
import jenkspy
from findpeaks import findpeaks

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

def date_cluster_analysis(timeline_path, filename):
    timeline = pd.read_csv(timeline_path)
    date_strings = timeline['date'].to_list()
    timeline['date'] = pd.to_datetime(timeline['date'])
    dates = timeline['date'].to_list()
    dates_no_dups = list(set(dates)) 
    dates_no_dups.sort()

    #print(dates_no_dups)

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

        jnb = jenkspy.JenksNaturalBreaks(int(peak_count) + 1)

        dates_as_strings = list(set(date_strings))
        dates_as_strings.sort()
        print(dates_as_strings)
        jnb.fit(dates_as_strings)
        print(jnb.group_)
        

    #dg.draw_plot_graph(gap_positions, title=filename)


if __name__ == '__main__':
    data_root = Path("..", "booknlp", "output")
    #clean_files(data_root)

    events = get_events(data_root)

    for filename, events_for_file in events.items():
        #with open(Path(data_root, filename + "_events.txt"), "w", encoding='utf-8') as txt_file:
        #    txt_file.write(str(events_for_file))

        #print(events_for_file[0])
        #print(filename + ": num of dated Events:" + str(len(events_for_file)))
        simple_events = [event for event in events_for_file if event['complex'] == False]
        simple_events = [{"line_num": event['line_num'], "date_text": event['dates'][0][0], "date": event['dates'][0][1], "line": event['line'].strip()} for event in simple_events]
        #print(simple_events)
        #print(filename + ": num of Simple Events:" + str(len(simple_events)))
        events_df = pd.DataFrame.from_dict(simple_events)
        #print(events_df)

        #print(events_df.info())

        events_df = events_df.sort_values(by=['date'])
        events_df.to_csv(Path(data_root, filename + "_events.csv"), index=False)

        event_values = {"dates": events_df['date'].to_list(), "labels": events_df['line'].to_list()}
        #dg.draw_timeline(event_values)

        date_cluster_analysis(Path(data_root, filename + "_events.csv"), filename)
    
