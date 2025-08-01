from pathlib import Path
import pandas as pd
from dateparser.search import search_dates

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
    possible_events = {}
    events_by_file = {}

    for file in data_folder.glob("*.tokens"):  
        filename = Path(file).stem
        if (Path(data_folder, filename+".pkl").exists() and regen == False):
            df = pd.read_pickle(Path(data_folder, filename+".pkl"))
            dataframes[filename] = df
        else:
            print("Print reading values from TSV")
            clean_file(file)
            df = pd.read_csv(file, delimiter="\t")             
            dataframes[filename] = df
            df.to_pickle(Path(data_folder, filename+".pkl"))

    for file, df in dataframes.items():
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
                    possible_events[event_sentence] = {"dates": filtered_dates, "line": resentence, "complex": True}
                elif len(filtered_dates) > 0:
                    possible_events[event_sentence] = {"dates": filtered_dates, "line": resentence, "complex": False}

        events_by_file[file] = possible_events

    return (events_by_file)


if __name__ == '__main__':
    data_root = Path("..", "booknlp", "output")
    #clean_files(data_root)
    events = get_events(data_root)

    for filename, events_for_file in events.items():
        with open(Path(data_root, filename + "_events.txt"), "w", encoding='utf-8') as new_file:
            new_file.write(str(events_for_file))