import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from mpl_interactions import ioff, panhandler, zoom_factory
import time, math
from datetime import date, datetime, timedelta

def draw_bar_graph(data, x_label="", y_label=""):
    plt.style.use('_mpl-gallery')

    with plt.ioff():
        fig, ax = plt.subplots(figsize=(16,8))

    x = data.keys()
    y = data.values()

    fig.subplots_adjust(
        top=0.982,
        bottom=0.065,
        left=0.048,
        right=0.99,
        hspace=0.2,
        wspace=0.2
    )

    ax.bar(x, y, width=1, label=list(x), edgecolor="black", linewidth=0.7)

    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set(xlim=(0, len(x)), ylim=(0, max(y) + (math.ceil((max(y) / 100) * 10))))

    disconnect_zoom = zoom_factory(ax)
    pan_handler = panhandler(fig)
    #display(fig.canvas)
    plt.show()

def draw_weighted_graph(data, title=""):
    
    before_graph = time.time()
    
    G = nx.Graph()
    for row in data:
        G.add_edge(row["node1"], row["node2"], weight=row["weighted_value"])
    
    pos = nx.spring_layout(G, k=0.15, iterations=20, seed=7)
    nx.draw_networkx_nodes(G, pos, node_size=15)
    nx.draw_networkx_edges(G, pos, width=6)
    
    elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 3]
    esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 3]
    
    nx.draw_networkx_edges(G, pos, edgelist=elarge, width=1)
    nx.draw_networkx_edges(G, pos, edgelist=esmall, width=1, alpha=0.5, edge_color="b", style="dashed")

    nx.draw_networkx_labels(G, pos, font_size=6, font_family="sans-serif")
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels)

    ax = plt.gca()
    ax.margins(0.08)
    plt.axis("off")
    plt.tight_layout()
    plt.title(title)
    output_duration(before_graph, "Graphing")
    plt.show()    


def draw_timeline(data, title=""):
    # Code drawn from https://dadoverflow.com/2021/08/17/making-timelines-with-python/

    dates = data["dates"]
    labels = data["labels"]

    min_date = date(np.min(dates).year - 2, np.min(dates).month, np.min(dates).day)
    max_date = date(np.max(dates).year + 2, np.max(dates).month, np.max(dates).day)

    labels = ['{0:%d %b %Y}:\n{1}'.format(d, l) for l, d in zip (labels, dates)]

    fig, ax = plt.subplots(figsize=(15, 4), constrained_layout=True)
    ax.set_ylim(-2, 1.75)
    ax.set_xlim(min_date, max_date)
    ax.axhline(0, xmin=0.05, xmax=0.95, c='deeppink', zorder=1)   
    ax.scatter(dates, np.zeros(len(dates)), s=120, c='palevioletred', zorder=2)
    ax.scatter(dates, np.zeros(len(dates)), s=30, c='darkmagenta', zorder=3)

    label_offsets = np.zeros(len(dates))
    label_offsets[::2] = 0.35
    label_offsets[1::2] = -0.7
    for i, (l, d) in enumerate(zip(labels, dates)):
        ax.text(d, label_offsets[i], l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=12)

    stems = np.zeros(len(dates))
    stems[::2] = 0.3
    stems[1::2] = -0.3   
    markerline, stemline, baseline = ax.stem(dates, stems)
    plt.setp(markerline, marker=',', color='darkmagenta')
    plt.setp(stemline, color='darkmagenta')
    plt.title(title)

    # hide lines around chart
    for spine in ["left", "top", "right", "bottom"]:
        ax.spines[spine].set_visible(False)
    
    # hide tick labels
    ax.set_xticks([])
    ax.set_yticks([])
    
    ax.set_title('', fontweight="bold", fontfamily='serif', fontsize=16, color='royalblue')
    plt.show()

def draw_plot_graph(data, x_label="", y_label="", title=""):
    x_values = data.keys()
    y_values = data.values()

    plt.plot(x_values, y_values)
    plt.title(title)
    plt.show()


def output_duration(start_time, action):
    duration = time.time() - start_time
    current_time = datetime(1,1,1) + timedelta(seconds=duration)
    readable_duration = str(current_time.day-1) + ":" + str(current_time.hour) + ":" + str(current_time.minute) + ":" + str(current_time.second)
    print(action + " took " + readable_duration +  " to run")  

weighting_dist_all = {1: 62822, 2: 16234, 3: 6864, 4: 3774, 5: 2500, 6: 1796, 7: 1360, 8: 956, 9: 834, 10: 654, 11: 512, 12: 458, 13: 408, 14: 282, 15: 280, 16: 258, 17: 222, 18: 182, 19: 138, 20: 174, 21: 148, 22: 126, 23: 104, 24: 110, 25: 94, 26: 60, 27: 68, 28: 82, 29: 78, 30: 78, 31: 64, 32: 76, 33: 70, 34: 58, 35: 54, 36: 44, 37: 46, 38: 34, 39: 50, 40: 30, 41: 24, 42: 30, 43: 28, 44: 28, 45: 12, 46: 26, 47: 22, 48: 14, 49: 18, 50: 16, 51: 14, 52: 12, 53: 22, 54: 24, 55: 10, 56: 24, 57: 18, 58: 12, 59: 18, 60: 14, 61: 10, 62: 16, 63: 16, 64: 14, 65: 16, 66: 20, 67: 10, 68: 10, 69: 8, 70: 8, 71: 8, 72: 6, 73: 8, 74: 10, 75: 10, 76: 10, 77: 6, 78: 4, 79: 10, 81: 6, 82: 8, 83: 8, 84: 6, 85: 14, 86: 14, 87: 6, 88: 14, 89: 6, 90: 4, 91: 6, 92: 4, 93: 2, 94: 2, 97: 8, 99: 6, 101: 4, 102: 2, 103: 2, 104: 2, 105: 6, 106: 2, 107: 8, 108: 2, 110: 4, 112: 6, 113: 8, 114: 2, 115: 4, 116: 4, 117: 4, 118: 4, 119: 2, 123: 2, 124: 2, 125: 4, 127: 2, 128: 2, 129: 4, 130: 6, 131: 6, 133: 2, 134: 4, 136: 2, 137: 2, 138: 2, 139: 6, 141: 2, 143: 2, 146: 2, 149: 2, 150: 4, 152: 2, 155: 2, 156: 4, 158: 2, 162: 4, 164: 2, 166: 2, 171: 2, 175: 2, 177: 2, 194: 2, 197: 2, 198: 2, 199: 2, 200: 2, 205: 2, 211: 2, 225: 2, 226: 2, 232: 4, 235: 4, 236: 2, 241: 2, 246: 2, 263: 2, 279: 2, 298: 2, 300: 2, 311: 2, 314: 2, 328: 2, 371: 2, 383: 2, 395: 2, 416: 4, 460: 2, 522: 2, 539: 2, 609: 2}

weighting_dist = {3: 6864, 4: 3774, 5: 2500, 6: 1796, 7: 1360, 8: 956, 9: 834, 10: 654, 11: 512, 12: 458, 13: 408, 14: 282, 15: 280, 16: 258, 17: 222, 18: 182, 19: 138, 20: 174, 21: 148, 22: 126, 23: 104, 24: 110, 25: 94, 26: 60, 27: 68, 28: 82, 29: 78, 30: 78, 31: 64, 32: 76, 33: 70, 34: 58, 35: 54, 36: 44, 37: 46, 38: 34, 39: 50, 40: 30, 41: 24, 42: 30, 43: 28, 44: 28, 45: 12, 46: 26, 47: 22, 48: 14, 49: 18, 50: 16, 51: 14, 52: 12, 53: 22, 54: 24, 55: 10, 56: 24, 57: 18, 58: 12, 59: 18, 60: 14, 61: 10, 62: 16, 63: 16, 64: 14, 65: 16, 66: 20, 67: 10, 68: 10, 69: 8, 70: 8, 71: 8, 72: 6, 73: 8, 74: 10, 75: 10, 76: 10, 77: 6, 78: 4, 79: 10, 81: 6, 82: 8, 83: 8, 84: 6, 85: 14, 86: 14, 87: 6, 88: 14, 89: 6, 90: 4, 91: 6, 92: 4, 93: 2, 94: 2, 97: 8, 99: 6, 101: 4, 102: 2, 103: 2, 104: 2, 105: 6, 106: 2, 107: 8, 108: 2, 110: 4, 112: 6, 113: 8, 114: 2, 115: 4, 116: 4, 117: 4, 118: 4, 119: 2, 123: 2, 124: 2, 125: 4, 127: 2, 128: 2, 129: 4, 130: 6, 131: 6, 133: 2, 134: 4, 136: 2, 137: 2, 138: 2, 139: 6, 141: 2, 143: 2, 146: 2, 149: 2, 150: 4, 152: 2, 155: 2, 156: 4, 158: 2, 162: 4, 164: 2, 166: 2, 171: 2, 175: 2, 177: 2, 194: 2, 197: 2, 198: 2, 199: 2, 200: 2, 205: 2, 211: 2, 225: 2, 226: 2, 232: 4, 235: 4, 236: 2, 241: 2, 246: 2, 263: 2, 279: 2, 298: 2, 300: 2, 311: 2, 314: 2, 328: 2, 371: 2, 383: 2, 395: 2, 416: 4, 460: 2, 522: 2, 539: 2, 609: 2}

weighting_dist_reduced = {8: 956, 9: 834, 10: 654, 11: 512, 12: 458, 13: 408, 14: 282, 15: 280, 16: 258, 17: 222, 18: 182, 19: 138, 20: 174, 21: 148, 22: 126, 23: 104, 24: 110, 25: 94, 26: 60, 27: 68, 28: 82, 29: 78, 30: 78, 31: 64, 32: 76, 33: 70, 34: 58, 35: 54, 36: 44, 37: 46, 38: 34, 39: 50, 40: 30, 41: 24, 42: 30, 43: 28, 44: 28, 45: 12, 46: 26, 47: 22, 48: 14, 49: 18, 50: 16, 51: 14, 52: 12, 53: 22, 54: 24, 55: 10, 56: 24, 57: 18, 58: 12, 59: 18, 60: 14, 61: 10, 62: 16, 63: 16, 64: 14, 65: 16, 66: 20, 67: 10, 68: 10, 69: 8, 70: 8, 71: 8, 72: 6, 73: 8, 74: 10, 75: 10, 76: 10, 77: 6, 78: 4, 79: 10, 81: 6, 82: 8, 83: 8, 84: 6, 85: 14, 86: 14, 87: 6, 88: 14, 89: 6, 90: 4, 91: 6, 92: 4, 93: 2, 94: 2, 97: 8, 99: 6, 101: 4, 102: 2, 103: 2, 104: 2, 105: 6, 106: 2, 107: 8, 108: 2, 110: 4, 112: 6, 113: 8, 114: 2, 115: 4, 116: 4, 117: 4, 118: 4, 119: 2, 123: 2, 124: 2, 125: 4, 127: 2, 128: 2, 129: 4, 130: 6, 131: 6, 133: 2, 134: 4, 136: 2, 137: 2, 138: 2, 139: 6, 141: 2, 143: 2, 146: 2, 149: 2, 150: 4, 152: 2, 155: 2, 156: 4, 158: 2, 162: 4, 164: 2, 166: 2, 171: 2, 175: 2, 177: 2, 194: 2, 197: 2, 198: 2, 199: 2, 200: 2, 205: 2, 211: 2, 225: 2, 226: 2, 232: 4, 235: 4, 236: 2}

num_of_refs_dist = {1: 17705, 2: 10958, 3: 6181, 4: 3613, 5: 2087, 6: 1288, 7: 702, 8: 483, 9: 316, 10: 198, 11: 113, 12: 106, 13: 61, 14: 37, 15: 36, 16: 15, 17: 12, 18: 9, 19: 6, 21: 2, 22: 2, 24: 2, 27: 1, 29: 1, 43: 1, 51: 1}


if __name__ == '__main__':
    '''
    draw_graph(weighting_dist_all, "Number of Collocations", "Number of Cases")

    draw_graph(weighting_dist_reduced, "Number of Collocations", "Number of Cases")
    '''
    draw_bar_graph(num_of_refs_dist, "Number of References", "Number of Cases")

    plt.show()