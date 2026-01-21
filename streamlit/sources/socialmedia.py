import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
from sources.plots import plot_win_probabilities, plot_points
from sources.sql import (
    create_sql_engine,
    get_current_week,
    query_db,
    update_week,
    update_full_schedule,
)
from sources.long_queries import query_plays, query_week
from PIL import Image, ImageDraw, ImageFont
import zipfile
import requests


@st.cache_resource(show_spinner=False)
def get_stats(game_id):
    url = f"https://site.web.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
    response = requests.get(url)
    stats = {}
    for i in [0, 1]:
        stats[i] = {
            stat["name"]: stat["displayValue"]
            for stat in response.json()["boxscore"]["teams"][i]["statistics"]
        }

    stats[0]["interceptions"], stats[1]["interceptions"] = (
        stats[1]["interceptions"],
        stats[0]["interceptions"],
    )
    stats[0]["fumblesLost"], stats[1]["fumblesLost"] = (
        stats[1]["fumblesLost"],
        stats[0]["fumblesLost"],
    )

    return stats


def create_image_from_stats(game, home_color, away_color, title, subtitle):
    """
    Creates a single image from text details and two Matplotlib plots.
    """

    stats = get_stats(game["game_id"])

    stats[0]["score"] = game["away_team_score"]
    stats[1]["score"] = game["home_team_score"]

    # Define image size and background color
    img_width, img_height = 1080, 1920
    img = Image.open("streamlit/images/tt_bg_red.png")
    draw = ImageDraw.Draw(img)

    # Load a font (or use a default one)
    try:
        title_font = ImageFont.truetype("Arimo-Regular.ttf", 50)
        subtitle_font = ImageFont.truetype("Arimo-Regular.ttf", 70)
        details_font = ImageFont.truetype("Arimo-Regular.ttf", 40)
        score_font = ImageFont.truetype("Arimo-Regular.ttf", 60)
    except:
        url = "https://github.com/google/fonts/raw/refs/heads/main/apache/arimo/Arimo%5Bwght%5D.ttf"
        r = requests.get(url)
        with open("Arimo-Regular.ttf", "wb") as f:
            f.write(r.content)
        title_font = ImageFont.truetype("Arimo-Regular.ttf", 50)
        subtitle_font = ImageFont.truetype("Arimo-Regular.ttf", 70)
        details_font = ImageFont.truetype("Arimo-Regular.ttf", 40)
        score_font = ImageFont.truetype("Arimo-Regular.ttf", 60)

    # Draw the text
    text_color = "white"
    text_start_y = 50
    draw.text((320, text_start_y), title, font=title_font, fill=text_color)
    text_start_y += 100
    draw.text((320, text_start_y), subtitle, font=subtitle_font, fill=text_color)
    text_start_y += 160

    draw.line(
        [(0, text_start_y - 30), (1080, text_start_y - 30)], fill="white", width=2
    )
    text_start_y += 60

    spacers = [1, 0, 0, 1, 0, 1, 0]

    for ind, (stat_name, stat_value) in enumerate(
        [
            ("score", "Final Score"),
            ("totalYards", "Total Yards"),
            ("netPassingYards", "Passing Yards"),
            ("rushingYards", "Rushing Yards"),
            # ("thirdDownEff", "3rd Down Efficiency"),
            # ("fourthDownEff", "4th Down Efficiency"),
            # ("redZoneEff", "Red Zone Efficiency"),
            # ("turnovers", "Turnovers"),
            ("interceptions", "Interceptions Caught"),
            ("fumblesLost", "Fumbles Recovered"),
            ("possessionTime", "Time of Possession"),
        ]
    ):
        text = f"{stat_value}"
        if stat_name == "score":
            draw.text(
                (img_width / 2, text_start_y),
                text,
                font=score_font,
                fill=text_color,
                anchor="mb",
            )
        else:
            draw.text(
                (img_width / 2, text_start_y),
                text,
                font=details_font,
                fill=text_color,
                anchor="mm",
            )
        if ":" in str(stats[0][stat_name]):
            away_width = (
                (980 - 100)
                * (
                    int(stats[0][stat_name].split(":")[0])
                    + int(stats[0][stat_name].split(":")[1]) / 60
                )
                / 60
            )
        elif (
            max(0, float(stats[0][stat_name])) + max(0, float(stats[1][stat_name]))
        ) > 0:
            away_width = (
                (980 - 100)
                * max(0, float(stats[0][stat_name]))
                / (
                    max(0, float(stats[0][stat_name]))
                    + max(0, float(stats[1][stat_name]))
                )
            )
        else:
            away_width = (980 - 100) / 2
        away_coords = [100, text_start_y + 30, 100 + away_width, text_start_y + 120]
        draw.rectangle(away_coords, fill=f"#{away_color}", outline="white", width=1)
        home_coords = [100 + away_width, text_start_y + 30, 980, text_start_y + 120]

        draw.rectangle(home_coords, fill=f"#{home_color}", outline="white", width=1)

        if stat_name == "score":
            draw.text(
                (120, text_start_y + 75),
                str(stats[0][stat_name]),
                font=score_font,
                fill=text_color,
                anchor="lm",
            )
            draw.text(
                (960, text_start_y + 75),
                str(stats[1][stat_name]),
                font=score_font,
                fill=text_color,
                anchor="rm",
            )
        else:
            draw.text(
                (120, text_start_y + 75),
                str(stats[0][stat_name]),
                font=details_font,
                fill=text_color,
                anchor="lm",
            )
            draw.text(
                (960, text_start_y + 75),
                str(stats[1][stat_name]),
                font=details_font,
                fill=text_color,
                anchor="rm",
            )

        if spacers[ind] == 1:
            draw.line(
                [(50, text_start_y + 150), (1030, text_start_y + 150)],
                fill="white",
                width=1,
            )
            text_start_y += 20
        text_start_y += 190

    return img


def create_image_from_plots_and_text(title, subtitle, details, plot1_fig, plot2_fig):
    """
    Creates a single image from text details and two Matplotlib plots.
    """
    # Define image size and background color
    img_width, img_height = 1080, 1920
    img = Image.open("streamlit/images/tt_bg.png")
    draw = ImageDraw.Draw(img)

    # Load a font (or use a default one)
    try:
        title_font = ImageFont.truetype("Arimo-Regular.ttf", 50)
        subtitle_font = ImageFont.truetype("Arimo-Regular.ttf", 70)
        details_font = ImageFont.truetype("Arimo-Regular.ttf", 50)
    except:
        url = "https://github.com/google/fonts/raw/refs/heads/main/apache/arimo/Arimo%5Bwght%5D.ttf"
        r = requests.get(url)
        with open("Arimo-Regular.ttf", "wb") as f:
            f.write(r.content)
        title_font = ImageFont.truetype("Arimo-Regular.ttf", 50)
        subtitle_font = ImageFont.truetype("Arimo-Regular.ttf", 70)
        details_font = ImageFont.truetype("Arimo-Regular.ttf", 50)

    # Draw the text
    text_color = "white"
    text_start_y = 50
    draw.text((320, text_start_y), title, font=title_font, fill=text_color)
    text_start_y += 100
    draw.text((320, text_start_y), subtitle, font=subtitle_font, fill=text_color)
    text_start_y += 160

    draw.line(
        [(0, text_start_y - 30), (1080, text_start_y - 30)], fill="white", width=2
    )

    lines = details.split("\n")
    line_spacing = 45
    bbox = details_font.getbbox("A")
    line_height = bbox[3] - bbox[1]

    for i, line in enumerate(lines):
        y = text_start_y + i * (line_height + line_spacing)
        draw.text((50, y), line, font=details_font, fill=text_color)

    # draw.text((50, text_start_y), details, font=details_font, fill=text_color)

    buffer1 = io.BytesIO()
    plot1_fig.savefig(buffer1, format="png", bbox_inches="tight")
    buffer1.seek(0)
    plot1_img = Image.open(buffer1)

    buffer2 = io.BytesIO()
    plot2_fig.savefig(buffer2, format="png", bbox_inches="tight")
    buffer2.seek(0)
    plot2_img = Image.open(buffer2)

    # Resize plots to fit the image
    plot1_width = 980
    plot1_height = int(plot1_width / plot1_img.width * plot1_img.height)
    plot1_img = plot1_img.resize((plot1_width, plot1_height), Image.Resampling.LANCZOS)
    plot2_width = 980
    plot2_height = int(plot2_width / plot2_img.width * plot2_img.height)
    plot2_img = plot2_img.resize((plot2_width, plot2_height), Image.Resampling.LANCZOS)

    crop_height = 99
    plot2_img = plot2_img.crop((0, 0, plot2_img.width, plot2_img.height - crop_height))

    plot_start_y = text_start_y + 250
    img.paste(plot1_img, (50, plot_start_y))
    img.paste(plot2_img, (50, plot_start_y + plot1_height - 38))

    return img


def create_cover_image(image_path, title, subtitle):
    # colors: main: top games, 310012: game stats

    cover_img_width, cover_img_height = 1080, 1920
    cover_img = Image.open(image_path)
    draw = ImageDraw.Draw(cover_img)
    try:
        cover_font_main = ImageFont.truetype("Arimo-Regular.ttf", 75)
        cover_font_sub = ImageFont.truetype("Arimo-Regular.ttf", 55)
    except:
        url = "https://github.com/google/fonts/raw/refs/heads/main/apache/arimo/Arimo%5Bwght%5D.ttf"
        r = requests.get(url)
        with open("Arimo-Regular.ttf", "wb") as f:
            f.write(r.content)
        cover_font_main = ImageFont.truetype("Arimo-Regular.ttf", 75)
        cover_font_sub = ImageFont.truetype("Arimo-Regular.ttf", 55)

    title_text = title
    year_week_text = subtitle
    #    box_coords = [
    #          50, cover_img_height/2 + 200,
    #        1030, cover_img_height/2 + 650
    #    ]
    #    draw.rectangle(box_coords, fill=(256,256,256,1))

    draw.text(
        (cover_img_width / 2, cover_img_height / 2 + 300),
        year_week_text,
        font=cover_font_sub,
        fill="white",
        anchor="mm",
    )
    draw.text(
        (cover_img_width / 2, cover_img_height / 2 + 450),
        title_text,
        font=cover_font_main,
        fill="white",
        anchor="mm",
    )

    return cover_img


def create_info_image(image_path):
    info_img_width, info_img_height = 1080, 1920
    info_img = Image.open(image_path)
    draw = ImageDraw.Draw(info_img)
    try:
        info_font_main = ImageFont.truetype("Arimo-Regular.ttf", 80)
        info_font_sub = ImageFont.truetype("Arimo-Regular.ttf", 60)
        info_font_subsub = ImageFont.truetype("Arimo-Regular.ttf", 50)
    except:
        url = "https://github.com/google/fonts/raw/refs/heads/main/apache/arimo/Arimo%5Bwght%5D.ttf"
        r = requests.get(url)
        with open("Arimo-Regular.ttf", "wb") as f:
            f.write(r.content)
        info_font_main = ImageFont.truetype("Arimo-Regular.ttf", 80)
        info_font_sub = ImageFont.truetype("Arimo-Regular.ttf", 60)
        info_font_subsub = ImageFont.truetype("Arimo-Regular.ttf", 50)

    text1 = f"Are you interested in more"
    draw.text(
        (info_img_width / 2, 900), text1, font=info_font_sub, fill="white", anchor="mm"
    )
    text1b = f"NFL analytics?"
    draw.text(
        (info_img_width / 2, 980), text1b, font=info_font_sub, fill="white", anchor="mm"
    )
    text2 = f"Do you enjoy Data Science?"
    draw.text(
        (info_img_width / 2, 1150), text2, font=info_font_sub, fill="white", anchor="mm"
    )
    text2b = f"(Machine Learning, GenAI, ...)"
    draw.text(
        (info_img_width / 2, 1230),
        text2b,
        font=info_font_subsub,
        fill="white",
        anchor="mm",
    )
    text3 = f"Then head over to"
    draw.text(
        (info_img_width / 2, 1400), text3, font=info_font_sub, fill="white", anchor="mm"
    )
    text4 = f"nfl-gameday.streamlit.app"
    draw.text(
        (info_img_width / 2, 1550),
        text4,
        font=info_font_main,
        fill="white",
        anchor="mm",
    )

    draw.line([(60, 1588), (183, 1588)], fill="white", width=4)
    draw.line([(235, 1588), (475, 1588)], fill="white", width=4)
    draw.line([(510, 1588), (909, 1588)], fill="white", width=4)
    draw.line([(934, 1588), (955, 1588)], fill="white", width=4)
    draw.line([(980, 1588), (1018, 1588)], fill="white", width=4)

    return info_img


def generate_top_games_posts(winners, year, week, games_df, teams_df):
    """
    Generates and displays social media posts for top games of the week.

    Args:
        winners (dict): Dictionary of top game categories and their data.
        year (int): The current year.
        week (int or str): The current week.
        games_df (pd.DataFrame): DataFrame containing game play data.
        teams_df (pd.DataFrame): DataFrame containing team information.
    """
    images_to_zip = []

    st.subheader("Social Media Posts")
    st.write("---")

    if type(week) is str:
        year_week_text = f"Season {year}/{year + 1} - {week}"
        week_str = week
    else:
        year_week_text = f"Season {year}/{year + 1} - Week {week}"
        week_str = f"week-{week:02d}"
    cover_img = create_cover_image(
        "streamlit/images/tt_cover.png", "Top Games of the Week", year_week_text
    )
    st.image(cover_img)

    cover_buffer = io.BytesIO()
    cover_img.save(cover_buffer, format="PNG")
    cover_buffer.seek(0)
    images_to_zip.append((f"01_cover_{week_str}.png", cover_buffer))
    img_ind = 2
    # --- 2. Category Pages ---
    for category, row in winners.items():
        if row is None:
            continue

        # Get data for plotting
        game_data = games_df.loc[games_df["game_id"] == row["game_id"]]
        home_team_name = row["home_team"]
        away_team_name = row["away_team"]
        home_color = teams_df.loc[teams_df["name"] == home_team_name, "color"].values[0]
        away_color = teams_df.loc[teams_df["name"] == away_team_name, "color"].values[0]
        home_abbreviation = teams_df.loc[
            teams_df["name"] == home_team_name, "abbreviation"
        ].values[0]
        away_abbreviation = teams_df.loc[
            teams_df["name"] == away_team_name, "abbreviation"
        ].values[0]

        # Create plots
        wp_plot = plot_win_probabilities(
            game_data["time_left"],
            game_data["home_wp"],
            home_color,
            away_color,
            home_team_name,
            away_team_name,
            show=False,
            ticks=True,
            postseason=(type(week) is str)
        )

        score_plot = plot_points(
            game_data["time_left"],
            game_data["home_score"],
            game_data["away_score"],
            home_color,
            away_color,
            home_team_name,
            away_team_name,
            show=False,
            right=False,
            postseason=(type(week) is str)
        )

        # Create a detailed string for the image
        details_text = (
            f"Game:  {away_abbreviation} @ {home_abbreviation}\n"
            f"Winner:  {row['winner']}\n"
            f"Final Score:  {away_abbreviation}  {row['away_score']}-{row['home_score']}  {home_abbreviation}"
        )

        # Create and display the combined image
        social_post_img = create_image_from_plots_and_text(
            title=year_week_text,
            subtitle=category,
            details=details_text,
            plot1_fig=wp_plot,
            plot2_fig=score_plot,
        )

        st.divider()
        st.image(social_post_img)

        img_buffer = io.BytesIO()
        social_post_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        filename = f"{img_ind:02d}_{category.replace(' ', '_').lower()}_{week_str}.png"
        images_to_zip.append((filename, img_buffer))

        plt.close("all")

        img_ind += 1

    # --- 3. Info Page ---

    info_img = create_info_image("streamlit/images/tt_info.png")

    st.image(info_img)

    info_buffer = io.BytesIO()
    info_img.save(info_buffer, format="PNG")
    info_buffer.seek(0)
    images_to_zip.append((f"info_{week_str}.png", info_buffer))

    if images_to_zip:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for filename, img_io in images_to_zip:
                zip_file.writestr(filename, img_io.getvalue())
        zip_buffer.seek(0)

        st.download_button(
            label="📥 Download All Posts as ZIP",
            data=zip_buffer,
            file_name=f"top_games_{week_str}.zip",
            mime="application/zip",
        )


def generate_game_stats_posts(year, week, games, teams_df):
    """
    Generates and displays social media posts for top games of the week.

    Args:
        year (int): The current year.
        week (int or str): The current week.
        games (list): List containing game data.
        teams_df (pd.DataFrame): DataFrame containing team information.
    """
    images_to_zip = []

    st.subheader("Social Media Posts")
    st.write("---")

    if type(week) is str:
        year_week_text = f"Season {year}/{year + 1} - {week}"
        week_str = week
    else:
        year_week_text = f"Season {year}/{year + 1} - Week {week}"
        week_str = f"week-{week:02d}"
    cover_img = create_cover_image(
        "streamlit/images/tt_cover_red.png", "Game stats", year_week_text
    )
    st.image(cover_img)

    cover_buffer = io.BytesIO()
    cover_img.save(cover_buffer, format="PNG")
    cover_buffer.seek(0)
    images_to_zip.append((f"01_cover_{week_str}.png", cover_buffer))
    img_ind = 2
    # --- 2. Category Pages ---
    for game in games:
        home_abbreviation = teams_df.loc[
            teams_df["team_id"] == game["home_team_id"], "abbreviation"
        ].values[0]
        away_abbreviation = teams_df.loc[
            teams_df["team_id"] == game["away_team_id"], "abbreviation"
        ].values[0]

        home_color = teams_df.loc[
            teams_df["team_id"] == game["home_team_id"], "color"
        ].values[0]
        away_color = teams_df.loc[
            teams_df["team_id"] == game["away_team_id"], "color"
        ].values[0]

        title = year_week_text
        subtitle = f"{away_abbreviation} @ {home_abbreviation}"

        social_post_img = create_image_from_stats(
            game, home_color, away_color, title, subtitle
        )

        st.divider()
        st.image(social_post_img)

        img_buffer = io.BytesIO()
        social_post_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        filename = (
            f"{img_ind:02d}_{away_abbreviation}-{home_abbreviation}_{week_str}.png"
        )
        images_to_zip.append((filename, img_buffer))

        plt.close("all")

        img_ind += 1

    # --- 3. Info Page ---

    info_img = create_info_image("streamlit/images/tt_info_red.png")

    st.image(info_img)

    info_buffer = io.BytesIO()
    info_img.save(info_buffer, format="PNG")
    info_buffer.seek(0)
    images_to_zip.append((f"info_{week_str}.png", info_buffer))

    if images_to_zip:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for filename, img_io in images_to_zip:
                zip_file.writestr(filename, img_io.getvalue())
        zip_buffer.seek(0)

        st.download_button(
            label="📥 Download All Posts as ZIP",
            data=zip_buffer,
            file_name=f"game_stats_{week_str}.zip",
            mime="application/zip",
        )
