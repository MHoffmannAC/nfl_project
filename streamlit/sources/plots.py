import matplotlib.pyplot as plt
import streamlit as st

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

    ax.plot(timeLeft / 60, homeScore, color=f"#{homeColor}", linewidth=1)
    ax.plot(timeLeft / 60, awayScore, color=f"#{awayColor}", linewidth=1,linestyle=(0, (9.1,2)))

    plt.fill_between(timeLeft / 60, homeScore, awayScore, where=(homeScore > awayScore), interpolate=True, color=f"#{homeColor}", alpha=0.5)
    plt.fill_between(timeLeft / 60, homeScore, awayScore, where=(homeScore < awayScore), interpolate=True, color=f"#{awayColor}", alpha=0.5)
    # plt.fill_between(timeLeft / 60, homeScore, 0, where=(homeScore > awayScore), interpolate=True, color=f"#{homeColor}", alpha=0.5)
    # plt.fill_between(timeLeft / 60, awayScore, 0, where=(homeScore < awayScore), interpolate=True, color=f"#{awayColor}", alpha=0.5)

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