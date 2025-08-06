import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import os
from sklearn.tree import export_graphviz
from sklearn.tree._tree import TREE_LEAF
import graphviz
import fitz
from PIL import Image
from io import BytesIO
import re

def plot_play_probabilities(classes, probabilities):
    fig, ax = plt.subplots(figsize=(3, 1.5))
    fig.patch.set_facecolor("#00093a")
    ax.set_facecolor("#00093a")
    sorted_classes = classes[probabilities.argsort()]
    sorted_probabilities = probabilities[probabilities.argsort()]

    colors =  ["gray"] * (len(sorted_classes) - 1) + ["#800020"]
    bars = ax.barh(sorted_classes, sorted_probabilities * 100, color=colors)
    for i, bar in enumerate(bars):
        ax.text(
            bar.get_width() + 1 if bar.get_width()<90 else bar.get_width() -1,  # Position to the right of the bar
            bar.get_y() + bar.get_height() / 2,  # Centered vertically on the bar
            f"{sorted_probabilities[i] * 100:.0f}%",  # Display percentage with 1 decimal place
            va="center",
            ha="left" if bar.get_width()<90 else "right",
            color="white",
            fontsize=6
        )    
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.tick_params(axis='x', colors='white', which='both', top=False, bottom=False, labelbottom=False)
    ax.tick_params(axis='y', colors='white')
    #plt.xlabel("Probabilities", fontsize=9, color="white")
    plt.yticks(fontsize=10, color="white")
    plt.xlim(0,100)
    for spine in ax.spines.values():
        spine.set_edgecolor("white")
    st.pyplot(fig, use_container_width=False)

def plot_win_probabilities(timeLeft, probabilities, homeColor, awayColor, homeName, awayName):
    ot = timeLeft.iloc[-1]<0
    fig, ax = plt.subplots(figsize=(3, 2))    
    fig.patch.set_facecolor("#00093a")
    ax.set_facecolor("white")
    ax.plot(timeLeft / 60, probabilities*100, color="#00093a", linewidth=1)
    ax.axhline(50, color="gray", linestyle="-", linewidth=0.5)

    plt.fill_between(timeLeft / 60, probabilities*100, 50, where=(probabilities*100 > 50), interpolate=True, color=f"#{homeColor}", alpha=0.5)
    plt.fill_between(timeLeft / 60, probabilities*100, 50, where=(probabilities*100 < 50), interpolate=True, color=f"#{awayColor}", alpha=0.5)

    for time in range(0, 3601, 900):  # 900 seconds = 15 minutes
        ax.axvline(time / 60, color="#00093a", linestyle="--", linewidth=0.25, alpha=0.7)

    ax.set_ylabel("Win Probability", fontsize=10, color="white")
    ax.tick_params(axis='x', colors='#00093a')
    ax.tick_params(axis='y', colors='#00093a', which='both', left=False, right=False, labelleft=False)
    ax.set_ylim(0, 100)

    if ot:
        ax.set_xlim(60, -15)
        quarter_labels = ["Q1", "Q2", "Q3", "Q4", "OT"]
        quarter_positions = [3600 / 60 - 7.5, 2700 / 60 - 7.5, 1800 / 60 - 7.5, 900 / 60 - 7.5, -900/60 + 7.5]
    else:
        ax.set_xlim(60, 0)
        quarter_labels = ["Q1", "Q2", "Q3", "Q4"]
        quarter_positions = [3600 / 60 - 7.5, 2700 / 60 - 7.5, 1800 / 60 - 7.5, 900 / 60 - 7.5]
    ax.set_xticks(quarter_positions)
    ax.set_xticklabels(quarter_labels, fontsize=8, color="white")

    ax.text(58, 90, homeName, va="center", ha="left", color=f"#{homeColor}", fontsize=8, bbox=dict(facecolor='white', edgecolor=f"#{homeColor}", boxstyle='round,pad=0.3'))
    ax.text(58, 10, awayName, va="center", ha="left", color=f"#{awayColor}", fontsize=8, bbox=dict(facecolor='white', edgecolor=f"#{awayColor}", boxstyle='round,pad=0.3',linestyle=(3, (9.1,1))))

    for spine in ax.spines.values():
        spine.set_edgecolor("#00093a")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=False)


def plot_points(timeLeft, homeScore, awayScore, homeColor, awayColor, homeName, awayName):
    ot = timeLeft.iloc[-1]<0
    fig, ax = plt.subplots(figsize=(3, 2))    
    fig.patch.set_facecolor("#00093a")
    ax.set_facecolor("white")

    ax.step(timeLeft / 60, homeScore, color=f"#{homeColor}", linewidth=1, where="post")
    ax.step(timeLeft / 60, awayScore, color=f"#{awayColor}", linewidth=1,linestyle=(0, (9.1,2)), where="post")

    timeLeft_post = np.repeat(timeLeft, 2)[1:]
    homeScore_post = np.repeat(homeScore, 2)[:-1]
    awayScore_post = np.repeat(awayScore, 2)[:-1]

    #plt.fill_between(timeLeft / 60, homeScore, awayScore, where=(homeScore > awayScore), interpolate=True, color=f"#{homeColor}", alpha=0.5)
    #plt.fill_between(timeLeft / 60, homeScore, awayScore, where=(homeScore < awayScore), interpolate=True, color=f"#{awayColor}", alpha=0.5)
    plt.fill_between(timeLeft_post / 60, homeScore_post, 0, where=(homeScore_post > awayScore_post), interpolate=True, color=f"#{homeColor}", alpha=0.5)
    plt.fill_between(timeLeft_post / 60, awayScore_post, 0, where=(homeScore_post < awayScore_post), interpolate=True, color=f"#{awayColor}", alpha=0.5)
    plt.fill_between(timeLeft_post / 60, awayScore_post, 0, where=(homeScore_post == awayScore_post), interpolate=True, color=f"#111", alpha=0.75)

    for time in range(0, 3600, 900):  # 900 seconds = 15 minutes
        ax.axvline(time / 60, color="#00093a", linestyle="--", linewidth=0.25, alpha=0.7)

    ax.set_ylabel("Points", fontsize=10, color="white", rotation=270, labelpad=15, loc='center')
    ax.tick_params(axis='x', colors='#00093a')
    ax.tick_params(axis='y', colors='white')
    #ax.set_ylim(0, 100)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()

    if ot:
        ax.set_xlim(60, -15)
        quarter_labels = ["Q1", "Q2", "Q3", "Q4", "OT"]
        quarter_positions = [3600 / 60 - 7.5, 2700 / 60 - 7.5, 1800 / 60 - 7.5, 900 / 60 - 7.5, -900/60 + 7.5]
    else:
        ax.set_xlim(60, 0)
        quarter_labels = ["Q1", "Q2", "Q3", "Q4"]
        quarter_positions = [3600 / 60 - 7.5, 2700 / 60 - 7.5, 1800 / 60 - 7.5, 900 / 60 - 7.5]
    ax.set_xticks(quarter_positions)
    ax.set_xticklabels(quarter_labels, fontsize=8, color="white")

    #ax.text(58, 90, homeName, va="center", ha="left", color=f"#{homeColor}", fontsize=8, bbox=dict(facecolor='white', edgecolor=f"#{homeColor}", boxstyle='round,pad=0.3'))
    #ax.text(58, 10, awayName, va="center", ha="left", color=f"#{awayColor}", fontsize=8, bbox=dict(facecolor='white', edgecolor=f"#{awayColor}", boxstyle='round,pad=0.3'))

    for spine in ax.spines.values():
        spine.set_edgecolor("#00093a")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=False)
    

def prune_duplicate_leaves(mdl):
    def is_leaf(inner_tree, index):
        return (inner_tree.children_left[index] == TREE_LEAF and 
                inner_tree.children_right[index] == TREE_LEAF)

    def prune_index(inner_tree, decisions, index=0):
        if not is_leaf(inner_tree, inner_tree.children_left[index]):
            prune_index(inner_tree, decisions, inner_tree.children_left[index])
        if not is_leaf(inner_tree, inner_tree.children_right[index]):
            prune_index(inner_tree, decisions, inner_tree.children_right[index])
        if (is_leaf(inner_tree, inner_tree.children_left[index]) and
            is_leaf(inner_tree, inner_tree.children_right[index]) and
            (decisions[index] == decisions[inner_tree.children_left[index]]) and 
            (decisions[index] == decisions[inner_tree.children_right[index]])):
            inner_tree.children_left[index] = TREE_LEAF
            inner_tree.children_right[index] = TREE_LEAF

    decisions = mdl.tree_.value.argmax(axis=2).flatten().tolist()
    prune_index(mdl.tree_, decisions)

def display_tree(clf, feature_names, font_size=10, label_font_size=10, highlight=None):
    os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

    dot_data = export_graphviz(clf,
                            out_file=None,
                            filled=True,
                            rounded=True,
                            special_characters=True,
                            feature_names=feature_names,
                            class_names=None,
                            impurity=False)

    dot_data_lines = dot_data.splitlines()
    new_dot_data_lines = []
    tree = clf.tree_

    for line in dot_data_lines:
        if 'label=<' in line:
            node_id = int(line.split()[0])
            label_parts = line.split('label=<')[1].split('>,')[0].split('<br/>')
            new_label_parts = [part for part in label_parts if 'value =' not in part and 'samples =' not in part]
            if (tree.children_left[node_id] == TREE_LEAF and 
                tree.children_right[node_id] == TREE_LEAF):
                leaf_label = f'{clf.classes_[tree.value[node_id].argmax()]}'
                new_label_parts.append(leaf_label)
            new_label = '<br/>'.join(new_label_parts)
            new_line = line.split('label=<')[0] + f'label=<{new_label}>, fontsize={font_size},' + line.split('>,')[1]
            if highlight and not node_id in highlight: # and not (tree.children_left[node_id] == tree.children_right[node_id] == -1):
                new_line = re.sub(r'fillcolor="#[0-9a-fA-F]{6}"', 'fillcolor="#333333", fontcolor="#eeeeee"', new_line)
            new_dot_data_lines.append(new_line)
        elif '->' in line:
            parent_node = int(line.split()[0])
            child_node = int(line.split()[2].replace(';', ''))
            if (child_node - parent_node) % 2 == 1:
                headlabel = f'[labeldistance=2.5, labelangle=45, headlabel="True", fontsize={label_font_size}]'
            else:
                headlabel = f'[labeldistance=2.5, labelangle=-45, headlabel="False", fontsize={label_font_size}]'
            new_line = f'{parent_node} -> {child_node} {headlabel};'
            new_dot_data_lines.append(new_line)
        else:
            new_dot_data_lines.append(line)

    new_dot_data_lines = [(i.replace('pipeline-1__', '')
                            .replace('pipeline-2__', '')
                            .replace('num_pipe__', '')
                            .replace('cat_pipe__', '')
                            .replace('cat_ordinal__', '')
                            ) for i in new_dot_data_lines]

    new_dot_data_lines.insert(1, f'    dpi={100};')

    new_dot_data = "\n".join(new_dot_data_lines)
    custom_tree_graphviz = graphviz.Source(new_dot_data, engine='dot')
    
    #st.graphviz_chart(custom_tree_graphviz, width=5000)
    
    # Render directly to PNG bytes
    #png_bytes = custom_tree_graphviz.pipe(format='png')
    #image = Image.open(BytesIO(png_bytes))
    #st.image(image, caption="Decision Tree", use_column_width=False)
    
    pdf_bytes = custom_tree_graphviz.pipe(format='pdf')
    doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    page = doc.load_page(0)
    pix = page.get_pixmap()
    img = Image.open(BytesIO(pix.tobytes("ppm")))
    st.image(img, width=5800)