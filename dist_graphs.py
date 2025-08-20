import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from brokenaxes import brokenaxes
import numpy as np
import networkx as nx
from mpl_interactions import ioff, panhandler, zoom_factory
import time, math, textwrap
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import datetime
from pandas import Timestamp


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


def draw_timeline(point_data, title=""):
    # Code drawn from https://dadoverflow.com/2021/08/17/making-timelines-with-python/

    dates = point_data["dates"]
    labels = point_data["labels"]

    min_date = date(np.min(dates).year - 1, np.min(dates).month, np.min(dates).day)
    max_date = date(np.max(dates).year + 1, np.max(dates).month, np.max(dates).day)

    labels = ['{0:%d %b %Y}:\n{1}'.format(d, hard_wrap(l)[0]) for l, d in zip (labels, dates)]

    fig, ax = plt.subplots(figsize=(15, 10), constrained_layout=True)
    ax.set_ylim(-2, 1.75)
    ax.set_xlim(min_date, max_date)
    ax.axhline(0, xmin=0.05, xmax=0.95, c='deeppink', zorder=1)   
    ax.scatter(dates, np.zeros(len(dates)), s=120, c='palevioletred', zorder=2)
    ax.scatter(dates, np.zeros(len(dates)), s=30, c='darkmagenta', zorder=3)

    label_offsets = np.zeros(len(dates))
    label_offsets[::4] = 0.625
    label_offsets[1::4] = 0.325
    label_offsets[2::4] = -0.325
    label_offsets[3::4] = -0.625
    for i, (l, d) in enumerate(zip(labels, dates)):
        lines = hard_wrap(l)[1]
        offset = label_offsets[i]
        if offset > 0:
            ax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='baseline')
        else:
            ax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='top')

    stems = np.zeros(len(dates))
    stems[::4] = 0.6
    stems[1::4] = 0.3
    stems[2::4] = -0.3   
    stems[3::4] = -0.6  
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

def draw_grouped_timeline_old(data, title="", save_path=""):
    # Code drawn from https://dadoverflow.com/2021/08/17/making-timelines-with-python/

    dates_sections = data["dates"]
    number_of_sections = len(dates_sections)

    #print(dates_sections)

    all_labels = data["labels"]
    all_dates = []
    processed_labels = []
    
    min_date = dates_sections[0][0][0]
    max_date = dates_sections[-1][-1][-1]

    #print("Min date:" + str(min_date))
    #print("Max date:" + str(max_date))

    print("Num of sections: " + str(number_of_sections))

    fig, axs = plt.subplots(1, number_of_sections, figsize=(18, 8), constrained_layout=True, sharey=True)
    #fig, axs = plt.subplots(1, number_of_sections, figsize=(15, 10), sharey=True)

    if number_of_sections == 1:
        axs = [axs]

    number_of_groups = sum([len(section) for section in dates_sections])

    cmap = plt.get_cmap('tab10')
    colours = [mpl.colors.to_hex(cmap(i)) for i in range(number_of_groups)]
    #print("Colour array: " + str(colours))

    colour_start = 0
    start = 0
    for i, ax in enumerate(axs):
        dates_groups = dates_sections[i]
        section_min_date = dates_groups[0][0]
        section_max_date = dates_groups[-1][-1]

        #min_x = date(section_min_date.year, section_min_date.month - 3, section_min_date.day)
        #max_x = date(section_max_date.year, section_max_date.month + 3, section_max_date.day)

        min_x = section_min_date - relativedelta(days=10)
        max_x = section_max_date + relativedelta(days=10)

        #print(str(section_min_date) + " -> " + str(min_x))
        #print(str(section_max_date) + " -> " + str(max_x))

        ax.set_ylim(-2, 1.75)
        ax.set_xlim(min_x, max_x)
        ax.axhline(0, xmin=0.05, xmax=0.95, c='deeppink', zorder=1)   

        #print("Number of date groups in section: " + str(len(dates_groups)) + " out of " + str(number_of_groups) + " total")
        
        for j in range(0, len(dates_groups)):
            dates = dates_groups[j]
            labels = all_labels[start:start+len(dates)]

            colour_end = colour_start + 1
            colour_array = colours[colour_start:colour_end]
            #print(str(colour_start) + " - " + str(colour_end))

            start += len(dates)
            processed_labels += ['{0:%d %b %Y}:\n{1}'.format(d, hard_wrap(l)[0]) for l, d in zip (labels, dates)]

            #print("Colour array: " + str(colours))
            #print("Colours" + str(colour_array))
            ax.scatter(dates, np.zeros(len(dates)), s=120, c=colour_array, zorder=2, cmap=cmap)
            ax.scatter(dates, np.zeros(len(dates)), s=30, c='darkmagenta', zorder=3)
            all_dates += dates
            colour_start = colour_end

        label_offsets = np.zeros(len(all_dates))
        label_offsets[::4] = 1.025
        label_offsets[1::4] = -0.325
        label_offsets[2::4] = 0.325
        label_offsets[3::4] = -1.025

        #print(processed_labels)
        #print(all_dates)

        for n, (l, d) in enumerate(zip(processed_labels, all_dates)):
            #line_count = hard_wrap(l)[1]
            #print("Event: " + str(n) + " - " + l)

            offset = label_offsets[n]
            if offset > 0:
                ax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='baseline')
            else:
                ax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='top')

        stems = np.zeros(len(all_dates))
        stems[::4] = 1.0
        stems[1::4] = -0.3
        stems[2::4] = 0.3   
        stems[3::4] = -1.0  
        markerline, stemline, baseline = ax.stem(all_dates, stems)

        # hide lines around chart
        for spine in ["left", "top", "right", "bottom"]:
            ax.spines[spine].set_visible(False)
        
        # hide tick labels
        ax.set_xticks([])
        ax.set_yticks([])

        d = 0.015
        kwargs = dict(transform=ax.transAxes, color='deeppink', clip_on=False)
        #kwargs = dict(transform=ax.transAxes, clip_on=False)
        #ax.plot((-d, +d), (0.565-d, 0.5+d), **kwargs)
        if number_of_groups > 1:
            #print("\nSub axis: " + str(i))
            #print("Number of groups: " + str(number_of_sections))

            if  i != 0: #and i != (number_of_groups -1):
                #left hand side of axis line except first (left hand side of break) 
                #   ----  X----  X----  X----
                ax.plot((-d, +d), (0.565-d, 0.5+d), **kwargs)
                #print("Add red")
            
            if i != (number_of_sections - 1):
                #right hand side of axis line except the last (right hand side of break) 
                #   ----X  ----X ----X ----
                ax.plot((0.95-d, 0.95+d), (0.565-d, 0.5+d), **kwargs)
                #print("Add green")
                #print("i: " + str(i) + " , groups " + str(number_of_sections))

    plt.subplots_adjust(wspace=0.05,left=0.1,top=0.9,right=0.9,bottom=0.1)
    plt.setp(markerline, marker=',', color='darkmagenta')
    plt.setp(stemline, color='darkmagenta')
    #plt.title(title)
    
    plt.suptitle(title, fontweight="bold", fontfamily='serif', fontsize=16, color='royalblue')

    '''
    if save_path != "":
        plt.savefig(save_path)
    '''
    plt.show()

    
def draw_grouped_timeline(data, title="", save_path=""):
    # Code drawn from https://dadoverflow.com/2021/08/17/making-timelines-with-python/

    dates_sections = data["dates"]
    number_of_sections = len(dates_sections)

    #print(dates_sections)
    
    #min_date = dates_sections[0][0][0]
    #max_date = dates_sections[-1][-1][-1]

    #print("Min date:" + str(min_date))
    #print("Max date:" + str(max_date))

    #print("Num of sections: " + str(number_of_sections))

    #fig, axs = plt.subplots(1, number_of_sections, figsize=(18, 8), constrained_layout=True, sharey=True)
    #fig, axs = plt.subplots(1, number_of_sections, figsize=(15, 10), sharey=True)

    #if number_of_sections == 1:
    #    axs = [axs]

    number_of_groups = sum([len(section) for section in dates_sections])

    cmap = plt.get_cmap('tab10')
    colours = [mpl.colors.to_hex(cmap(i)) for i in range(number_of_groups)]
    #print("Colour array: " + str(colours))

    xlims_list = [] 

    for section in dates_sections:
        section_min_date = section[0][0]
        section_max_date = section[-1][-1]

        min_x = section_min_date - relativedelta(days=15)
        max_x = section_max_date + relativedelta(days=15)

        xlims_list.append((min_x, max_x))

    #grid = GridSpec(nrows=1, ncols=number_of_sections, wspace=0.05)
    fig = plt.figure(figsize=(18, 8))
    bax = brokenaxes(xlims=tuple(xlims_list), d=0.01, tilt=60)
    bax.axhline(0, xmin=0.05, xmax=0.95, c='deeppink', zorder=1) 
    bax.set_ylim(-2, 1.75)

    all_labels = data["labels"]
    all_dates = []
    processed_labels = []
    colour_start = 0
    start = 0
    for section in dates_sections:

        #dates = section[0]
        #bax.scatter(dates, np.zeros(len(dates)), s=30, c='darkmagenta', zorder=3)
        
        for j in range(0, len(section)):
            dates = section[j]
            labels = all_labels[start:start+len(dates)]

            start += len(dates)
            processed_labels += ['{0:%d %b %Y}:\n{1}'.format(d, hard_wrap(l)[0]) for l, d in zip (labels, dates)]

            bax.scatter(dates, np.zeros(len(dates)), s=120, c=colours[colour_start], zorder=2, cmap=cmap)
            bax.scatter(dates, np.zeros(len(dates)), s=30, c='darkmagenta', zorder=3)
            all_dates += dates
            colour_start = colour_start + 1

    label_offsets = np.zeros(len(all_dates))
    label_offsets[::4] = 1.025
    label_offsets[1::4] = -0.325
    label_offsets[2::4] = 0.325
    label_offsets[3::4] = -1.025

        #print(processed_labels)
        #print(all_dates)

    for n, (l, d) in enumerate(zip(processed_labels, all_dates)):
        #line_count = hard_wrap(l)[1]
        #print("Event: " + str(n) + " - " + l)
        offset = label_offsets[n]
        if offset > 0:
            bax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='baseline')
        else:
            bax.text(d, offset, l, ha='center', fontfamily='serif', fontweight='bold', color='royalblue',fontsize=10, verticalalignment='top')

    stems = np.zeros(len(all_dates))
    stems[::4] = 1.0
    stems[1::4] = -0.3
    stems[2::4] = 0.3   
    stems[3::4] = -1.0  
    bax.stem(all_dates, stems)


        # hide lines around chart
    #for spine in ["left", "top", "right", "bottom"]:
    #    bax.spines[spine].set_visible(False)

    
        # hide tick labels
    #bax.set_xticks([])
    #bax.set_yticks([])

    size = fig.get_size_inches()

    for i, ax in enumerate(bax.axs):
        #ax.set_xticks([])
        ax.set_yticks([])  
        for spine in ["left", "top", "right"]:
            ax.spines[spine].set_visible(False)


        bounds = ax.get_position().bounds
        d = 0.035
        ylen=d * np.sin(35 * np.pi / 180) * size[0] / size[1]
        xlen=d * np.cos(35 * np.pi / 180) / size[0] / bounds[2]

        kwargs = dict(
                    transform=ax.transAxes, 
                    color='deeppink', 
                    clip_on=False                     
                )
        #kwargs = dict(transform=ax.transAxes, clip_on=False)

        if number_of_groups > 1:
            #print("\nSub axis: " + str(i))
            #print("Number of groups: " + str(number_of_sections))

            # if not first section
            if  i != 0: #and i != (number_of_groups -1):
                #left hand side of axis line except first (left hand side of break) 
                #   ----  X----  X----  X----
                #ax.plot((-d, +d), (0.565-d, 0.5+d), **kwargs)
                #print(str((+xlen, -xlen)) + str((0.565-ylen, 0.5+ylen)))

                #ax.plot((+d, -d), (0.565-d, 0.5+d), **kwargs)
                ax.plot((-xlen, +xlen), (0.565-ylen, 0.5+ylen), **kwargs)
                #print("Add red")

            
            # if not last section
            if i != (number_of_sections - 1):
                #right hand side of axis line except the last (right hand side of break) 
                #   ----X  ----X ----X ----
                #print(str((1+d, 1-d)) + str((0.565-d, 0.5+d)))
                #ax.plot((0.95+d, 0.95-d), (0.565-d, 0.5+d), **kwargs)
                #ax.plot((1+d, 1-d), (0.565-d, 0.5+d), **kwargs)
                ax.plot((1-xlen, 1+xlen), (0.565-ylen, 0.5+ylen), **kwargs)
                #print("Add green")
                #print("i: " + str(i) + " , groups " + str(number_of_sections))'''
    

    
    '''
    plt.subplots_adjust(wspace=0.05,left=0.1,top=0.9,right=0.9,bottom=0.1)
    plt.setp(markerline, marker=',', color='darkmagenta')
    plt.setp(stemline, color='darkmagenta')
    #plt.title(title)
    '''    
    
    #bax.set_title(title, fontweight="bold", fontfamily='serif', fontsize=16, color='royalblue')
    bax.big_ax.get_yaxis().set_visible(False)
    plt.suptitle(title, fontweight="bold", fontfamily='serif', fontsize=16, color='royalblue')

    if save_path != "":
        plt.savefig(save_path)

    plt.show()




def hard_wrap(text, length=40):
    tw = textwrap.TextWrapper(width=length)
    wrapped_text = '\n'.join(tw.wrap(text))
    line_count = wrapped_text.count('\n') + 1
    return (wrapped_text, line_count)


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


grouped_timeline_reduced = {'dates': [['2019-09-04', '2019-09-15', '2019-09-19', '2019-09-20'], ['2019-10-23', '2019-10-30'], ['2025-10-23']],
                    'labels': [['the comment was made when none of us had heard of the Coronavirus and no ', 
                         'a letter from his employer , TBW Global Limited , dated', 
                         'hearing', 
                         'He attached a handwritten letter dated'], 
                         ['hearing', 
                         "This matter comes before the appeal tribunal on the appellant 's appeal from the judgment of Employment Judge Hildebrand ( sitting alone ) at London Central Employment Tribunal which was sent to the parties"], 
                         ['hearing']]
                    }

grouped_timeline = {'dates': [[datetime.datetime(2019, 9, 7, 1, 0)], [datetime.datetime(2019, 9, 15, 1, 0), datetime.datetime(2019, 9, 19, 1, 0), datetime.datetime(2019, 9, 20, 1, 0)], [datetime.datetime(2019, 10, 23, 1, 0), datetime.datetime(2019, 10, 30, 0, 0)], [datetime.datetime(2025, 10, 23, 1, 0)]],
                    'labels': [
                        'the comment was made when none of us had heard of the Coronavirus and no ', 

                        "He enclosed a letter from his employer , TBW Global Limited , dated | Despite the letter from the Claimant 's employer dated", 
                        
                        'The complaints of unfair dismissal and unlawful deduction of wages , which it was acknowledged were outside the scope and jurisdiction of the employment tribunal for police officers were withdrawn at a closed preliminary hearing | hearing Employment Judge Hildebrand listed the strike out application of the discrimination complaint on limitation grounds to be heard on 23 October 2019 at an open preliminary hearing . | hearing when the letter from the employer was discussed and no appeal has been made in respect of that decision . | Turning to the hearing', 
                        
                        'He attached a handwritten letter dated', 
                        
                        "In short that the claimant was unable to participate effectively in his hearing | hearing it appears that the claimant 's counsel raised the issue of the claimant being excused from giving evidence or giving evidence via video link at a substantive hearing , referring to the letter from his employer . | hearing .", 
                        
                        "This matter comes before the appeal tribunal on the appellant 's appeal from the judgment of Employment Judge Hildebrand ( sitting alone ) at London Central Employment Tribunal which was sent to the parties", 
                        
                        'hearing that had been converted to a preliminary hearing to be by video link . | At the hearing | hearing .']
                    }


grouped_timeline_eat_2022_3_test = {'dates': [[[datetime.datetime(2019, 9, 7, 1, 0), datetime.datetime(2019, 9, 15, 1, 0), datetime.datetime(2019, 9, 19, 1, 0), datetime.datetime(2019, 9, 20, 1, 0)], [datetime.datetime(2019, 10, 23, 1, 0), datetime.datetime(2019, 10, 30, 0, 0)]], [[datetime.datetime(2025, 10, 23, 1, 0)]]],
                        'labels': ['the comment was made when none of us had heard of the Coronavirus and no ', "He enclosed a letter from his employer , TBW Global Limited , dated | Despite the letter from the Claimant 's employer dated", 'The complaints of unfair dismissal and unlawful deduction of wages , which it was acknowledged were outside the scope and jurisdiction of the employment tribunal for police officers were withdrawn at a closed preliminary hearing | hearing Employment Judge Hildebrand listed the strike out application of the discrimination complaint on limitation grounds to be heard on 23 October 2019 at an open preliminary hearing . | hearing when the letter from the employer was discussed and no appeal has been made in respect of that decision . | Turning to the hearing', 'He attached a handwritten letter dated', "In short that the claimant was unable to participate effectively in his hearing | hearing it appears that the claimant 's counsel raised the issue of the claimant being excused from giving evidence or giving evidence via video link at a substantive hearing , referring to the letter from his employer . | hearing .", "This matter comes before the appeal tribunal on the appellant 's appeal from the judgment of Employment Judge Hildebrand ( sitting alone ) at London Central Employment Tribunal which was sent to the parties", 'hearing that had been converted to a preliminary hearing to be by video link . | At the hearing | hearing .']
                        }

grouped_timeline_eat_2022_1_test = {'dates': [
                                                [
                                                    [datetime.datetime(2011, 10, 1, 1, 0)]
                                                ], 
                                                [
                                                    [datetime.datetime(2013, 2, 20, 0, 0), datetime.datetime(2013, 9, 24, 1, 0), datetime.datetime(2013, 12, 19, 0, 0)]
                                                ], 
                                                [
                                                    [datetime.datetime(2020, 2, 4, 0, 0), datetime.datetime(2020, 2, 28, 0, 0)]
                                                ], 
                                                [
                                                    [datetime.datetime(2020, 9, 16, 1, 0), datetime.datetime(2021, 3, 26, 0, 0)]
                                                ]],
                        'labels': ['claimant attended the scene of the brutal murder of a prisoner who had been mutilated and disembowelled .', 'The application form for ill - health retirement was submitted by the claimant | date on which the application for ill - health retirement was submitted .', 'The employment tribunal concluded that any delay was for a relatively short period of time because it focused on any conduct having ceased to have been unwanted by September 2013 .', 'The claimant submitted a claim form', ' there is prejudice to the respondent in having to answer complaints about matters which occurred in 2012 and 2013 .', 'The judgment was signed by the employment judge', 'By a notice of appeal originally submitted', 'He made an order with seal date 26 March 2021 .']
                        }


#timeline = {'dates': [Timestamp('2019-09-04 00:00:00'), Timestamp('2019-09-15 00:00:00'), Timestamp('2019-09-15 00:00:00'), Timestamp('2019-09-19 00:00:00'), Timestamp('2019-09-19 00:00:00'), Timestamp('2019-09-19 00:00:00'), Timestamp('2019-09-19 00:00:00'), Timestamp('2019-09-20 00:00:00'), Timestamp('2019-10-23 00:00:00'), Timestamp('2019-10-23 00:00:00'), Timestamp('2019-10-23 00:00:00'), Timestamp('2019-10-30 00:00:00'), Timestamp('2025-10-23 00:00:00'), Timestamp('2025-10-23 00:00:00'), Timestamp('2025-10-23 00:00:00')], 'labels': ['the comment was made when none of us had heard of the Coronavirus and no ', 'He enclosed a letter from his employer , TBW Global Limited , dated', "Despite the letter from the Claimant 's employer dated", 'The complaints of unfair dismissal and unlawful deduction of wages , which it was acknowledged were outside the scope and jurisdiction of the employment tribunal for police officers were withdrawn at a closed preliminary hearing', 'hearing Employment Judge Hildebrand listed the strike out application of the discrimination complaint on limitation grounds to be heard on 23 October 2019 at an open preliminary hearing .', 'hearing when the letter from the employer was discussed and no appeal has been made in respect of that decision .', 'Turning to the hearing', 'He attached a handwritten letter dated', 'In short that the claimant was unable to participate effectively in his hearing', "referring to the letter from his employer .", 'hearing .', "This matter comes before the appeal tribunal on the appellant 's appeal from the judgment of Employment Judge Hildebrand ( sitting alone ) at London Central Employment Tribunal which was sent to the parties", 'hearing that had been converted to a preliminary hearing to be by video link .', 'At the hearing', 'hearing .']}
timeline = {'dates': [Timestamp('2019-09-07 00:00:00'), Timestamp('2019-09-15 00:00:00'), Timestamp('2019-09-19 00:00:00'), Timestamp('2019-09-20 00:00:00'), Timestamp('2019-10-23 00:00:00'), Timestamp('2019-10-30 00:00:00'), Timestamp('2025-10-23 00:00:00')], 'labels': ['the comment was made when none of us had heard of the Coronavirus and no ', "He enclosed a letter from his employer , TBW Global Limited , dated | Despite the letter from the Claimant 's employer dated", 'The complaints of unfair dismissal and unlawful deduction of wages , which it was acknowledged were outside the scope and jurisdiction of the employment tribunal for police officers were withdrawn at a closed preliminary hearing | hearing Employment Judge Hildebrand listed the strike out application of the discrimination complaint on limitation grounds to be heard on 23 October 2019 at an open preliminary hearing . | hearing when the letter from the employer was discussed and no appeal has been made in respect of that decision . | Turning to the hearing', 'He attached a handwritten letter dated', "In short that the claimant was unable to participate effectively in his hearing | hearing it appears that the claimant 's counsel raised the issue of the claimant being excused from giving evidence or giving evidence via video link at a substantive hearing , referring to the letter from his employer . | hearing .", "This matter comes before the appeal tribunal on the appellant 's appeal from the judgment of Employment Judge Hildebrand ( sitting alone ) at London Central Employment Tribunal which was sent to the parties", 'hearing that had been converted to a preliminary hearing to be by video link . | At the hearing | hearing .']}


if __name__ == '__main__':
    '''
    draw_graph(weighting_dist_all, "Number of Collocations", "Number of Cases")

    draw_graph(weighting_dist_reduced, "Number of Collocations", "Number of Cases")
    
    draw_bar_graph(num_of_refs_dist, "Number of References", "Number of Cases")
    '''
    #draw_timeline(timeline, title="eat-2022-3_body")
    #draw_grouped_timeline(grouped_timeline_eat_2022_3_test, title="eat-2022-3")
    #draw_grouped_timeline(grouped_timeline_eat_2022_1_test, title="eat-2022-1")
    #plt.show()