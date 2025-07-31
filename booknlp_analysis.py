from pathlib import Path
import pandas as pd


def main(data_folder, regen="False"):
    dataframes = {}

    for file in data_folder.glob("*.tokens"):  
        filename = Path(file).stem
        if (Path(data_folder, filename+".pkl").exists() and regen == False):
            df = pd.read_pickle(Path(data_folder, filename+".pkl"))
            dataframes[filename] = df
        else:
            df = pd.read_csv(file, delimiter="\t") 
            dataframes[filename] = df
            df.to_pickle(Path(data_folder, filename+".pkl"))

    for df in dataframes:
        print(df.info())

if __name__ == '__main__':
    data_root = Path("..", "booknlp", "output")
    main(data_root)