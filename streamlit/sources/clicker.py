import streamlit as st
import time
import json
import pandas as pd
from sqlalchemy import MetaData, Table, Column, String, Integer, Text, TIMESTAMP, func, select, insert, update, delete, text
from sqlalchemy.orm import Session

from sources.sql import create_sql_engine
sql_engine = create_sql_engine()

import streamlit.components.v1 as components

def run_game():

    metadata = MetaData()

    leaderboard_table = Table(
        'leaderboard', metadata,
        Column('user_id', Integer, primary_key=True),
        Column('username', String(100), nullable=False),
        Column('money', Integer, default=1000),
        Column('fans', Integer, default=0),
        Column('prestige_level', Integer, default=0),
    )

    save_data_table = Table(
        'save_data', metadata,
        Column('username', String(100), primary_key=True),
        Column('state_json', Text, nullable=False),
        Column('last_saved', TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    )

    metadata.create_all(sql_engine)

    def save_progress(username, state):
        state_json = json.dumps(state)
        fans = state.get("fans", 0)

        with Session(sql_engine) as session:
            # Save game state
            stmt_save = insert(save_data_table).values(
                username=username,
                state_json=state_json
            ).prefix_with("IGNORE")

            # Save leaderboard info
            stmt_leader = insert(leaderboard_table).values(
                username=username,
                fans=fans
            ).prefix_with("IGNORE")

            session.execute(stmt_save)
            session.execute(stmt_leader)
            session.commit()

    def load_progress(username):
        with Session(sql_engine) as session:
            stmt = select(save_data_table.c.state_json).where(save_data_table.c.username == username)
            result = session.execute(stmt).fetchone()
            return json.loads(result[0]) if result else None

    def reset_progress(username):
        with Session(sql_engine) as session:
            session.execute(delete(save_data_table).where(save_data_table.c.username == username))
            session.execute(delete(leaderboard_table).where(leaderboard_table.c.username == username))
            session.commit()

    def show_leaderboard():
        with sql_engine.connect() as connection:
            df = pd.read_sql(text("SELECT username, fans FROM leaderboard ORDER BY fans DESC LIMIT 10"), connection)
        st.header("Leaderboard")
        st.table(df)

    def calculate_money_per_second():
        total_income = 0
        for name in income_sources:
            if gs["managers"][name] > 0:
                total_income += income_sources[name]["base_income"] * gs["income_items"][name]['level'] * manager_factor ** (gs["managers"][name] - 1)
        return total_income

    def update_game():
        gs["income_per_second"] = calculate_money_per_second()
        now = time.time()
        delta = now - gs["last_money_update"]
        gs["money"] += round(gs["income_per_second"] * delta)
        gs["total_money"] += round(gs["income_per_second"] * delta)
        gs["last_money_update"] = now

    # Start game
    username = st.text_input("Enter your username", key="username")
    if not username:
        st.stop()

    base_prices = [25*7**i for i in range(11)]

    manager_factor = 3

    income_sources = {
        "Hot Dog Stand": {"base_price": base_prices[0], "price_exp": 1.11, "base_income": 1, "cooldown": 5},
        "Merch Store": {"base_price": base_prices[1], "price_exp": 1.15, "base_income": 4, "cooldown": 10},
        "Tailgate Booth": {"base_price": base_prices[2], "price_exp": 1.2, "base_income": 16, "cooldown": 15},
        "Fan Club": {"base_price": base_prices[3], "price_exp": 1.25, "base_income": 64, "cooldown": 20},
        "Training Camp": {"base_price": base_prices[4], "price_exp": 1.3, "base_income": 256, "cooldown": 30},
        "Junior League": {"base_price": base_prices[5], "price_exp": 1.35, "base_income": 1_024, "cooldown": 45},
        "TV Deal": {"base_price": base_prices[6], "price_exp": 1.4, "base_income": 4_096, "cooldown": 60},
        "Merch Megastore": {"base_price": base_prices[7], "price_exp": 1.45, "base_income": 16_384, "cooldown": 75},
        "Stadium Expansion": {"base_price": base_prices[8], "price_exp": 1.5, "base_income": 65_536, "cooldown": 90},
        "Global Tour": {"base_price": base_prices[9], "price_exp": 1.55, "base_income": 262_144, "cooldown": 120},
        "NFL Team": {"base_price": base_prices[10], "price_exp": 1.55, "base_income": 262_144, "cooldown": 120},
        
    }
    
    manager_levels = [10] + [i*25 for i in range(1,21)]

    if "game_state" not in st.session_state:
        #saved = load_progress(username)
        #st.session_state.game_state = saved if saved else {
        st.session_state.game_state = {
            "money": 25,
            "total_money": 25,
            "fans": 0,
            "income_items": {k: {"level": 0, "last_collected": 0} for k in income_sources},
            "income_per_second": 0,
            "last_money_update": time.time(),
            "last_saved": time.time(),
            "prestige": 0,
            "managers": {k: 0 for k in income_sources}
        }

    gs = st.session_state.game_state

    st.title("🏈 NFL Idle Game")

    # Top control buttons
    col1, col2, col3 = st.columns(3)
    #if col1.button("💾 Save"):
    #    save_progress(username, gs)
    #    st.success("Saved!")

    with col2.popover("🗑 Reset"):
        st.write("Reset progress")
        if st.button("🗑 Reset"):
            reset_progress(username)
            st.session_state.pop("game_state", None)
            st.rerun()

    with col3.popover("🌟 Prestige"):
        st.write("Reset progress and earn benefits for next season (currently not implemented)")
        if st.button("🌟 Prestige"):
            update_game()
            gained_fans = gs["total_money"] // 1000
            if gained_fans > 0:
                st.success(f"Prestiged for {gained_fans} fans!")
                gs["fans"] += gained_fans
                gs["money"] = 20
                gs["total_money"] = 20
                for item in gs["income_items"].values():
                    item["level"] = 0
                    item["last_collected"] = 0

    update_game()

    st.divider()
    
    def display_counters_html(fontsize, height, sep):
        return components.html(f"""
    <div id="money-display" style="
    font-size: {fontsize}px;
    font-weight: bold;
    color: white;
    text-align: left;
    margin: 30px 0;">
        💰 Money: {gs["money"]:,}$  {sep} 💵 Total Earnings: {gs["total_money"]:.2e}$  {sep} 🎉 Fans: {gs["fans"]:,}  {sep} ⭐ Prestige: {gs["prestige"]:,}
    </div>

    <script>
        let money = {gs["money"]};
        let total_money = {gs["total_money"]};
        const fans = {gs["fans"]};
        const prestige = {gs["prestige"]};
        const incomePerSecond = {gs["income_per_second"]};

        function updateDisplay() {{
            money += incomePerSecond;
            total_money += incomePerSecond;
            document.getElementById("money-display").innerHTML =
                `💰 Money: ${{money.toLocaleString('en-US')}}$  {sep} 💵 Total Earnings: ${{total_money.toExponential(2)}}$  {sep} 🎉 Fans: ${{fans.toLocaleString('en-US')}}  {sep} ⭐ Prestige: ${{prestige.toLocaleString('en-US')}}`;
        }}

        setInterval(updateDisplay, 1000);
    </script>
    """, height=height)
    
    display_counters_html(35,80,"   |   ")
    with st.sidebar:
        display_counters_html(20,150,"<br>")

    st.divider()

    # Income sources UI
    cols = st.columns([3,1])
    cols[0].header("Income Sources")
    buy_n_items = cols[1].segmented_control("Buy up to ... items:", ["1x", "5x", "10x", "25x", "Max"], default="1x", )
    
    def display_income(name):
        if gs["managers"][name] == 0:
            time_passed = time.time() - gs["income_items"][name]["last_collected"]      
            cooldown = income_sources[name]["cooldown"]

            income = income_sources[name]["base_income"] * gs["income_items"][name]["level"] * cooldown
            if st.button(f"Collect **{income:,}$** from {name}", key=f"collect_{name}"):
                if time_passed > cooldown:
                    gs["money"] += income
                    gs["total_money"] += income
                    gs["income_items"][name]["last_collected"] = time.time()
                    st.rerun()
                else:
                    st.toast(f"{name} not ready yet!")

            init_percent = min(100, (time_passed / cooldown) * 100)

            html_code = f"""
                <style>
                .progress-container {{
                    width: 220px;
                    background-color: #ddd;
                    border-radius: 4px;
                    margin-bottom: 15px;
                }}

                .progress-bar {{
                    height: 24px;
                    width: {init_percent}%;
                    background-color: #4CAF50;
                    text-align: center;
                    line-height: 24px;
                    color: white;
                    border-radius: 4px;
                }}
                </style>
            
            <div class="progress-container">
            <div id="bar1" class="progress-bar">{int(init_percent)}%</div>
            </div>
            <script>
            function animateProgressBar(id, initialPercent, totalDurationSec) {{
            let elem = document.getElementById(id);
            let width = initialPercent;
            let remainingPercent = 100 - width;

            if (remainingPercent <= 0) {{
                elem.style.width = "100%";
                elem.textContent = "100%";
                return;
            }}

            // Calculate interval delay in ms per 1% increment
            let remainingTimeMs = totalDurationSec * 1000 * (remainingPercent / 100);
            let intervalDelay = remainingTimeMs / remainingPercent;

            let interval = setInterval(() => {{
                if (width >= 100) {{
                clearInterval(interval);
                elem.style.width = "100%";
                elem.textContent = "100%";
                }} else {{
                width++;
                elem.style.width = width + '%';
                elem.textContent = width + '%';
                }}
            }}, intervalDelay);
            }}

            // Start animation: init percent and total duration
            animateProgressBar("bar1", {init_percent:.0f}, {cooldown});
            </script>
            """
            
            components.html(html_code, height=40)
    
    for name in gs["income_items"]:
        price = round(income_sources[name]["base_price"] * (income_sources[name]["price_exp"] ** gs["income_items"][name]['level']))
        if (price < 2 * gs["total_money"]):
            income = income_sources[name]["base_income"] * (gs["income_items"][name]['level']) * manager_factor ** max(gs["managers"][name] - 1, 0)

            st.subheader(f"**{name}** - Level: {gs['income_items'][name]['level']}")
            colA, colB, colC, colD = st.columns([1, 1, 1, 1], gap="large")
            colA.write(f"Income: {income:,}/s  \n Next: {price:,}$ (+{income_sources[name]['base_income'] * manager_factor ** max(gs['managers'][name] - 1, 0)}/s income)")

            with colB:
                if gs["income_items"][name]['level'] > 0 and gs["managers"][name] == 0:
                    display_income(name)

            if buy_n_items == "Max":
                if colC.button(f"Buy {buy_n_items} {name}", key=f"buy_{name}"):
                    bought = 0
                    while True:
                        price = round(income_sources[name]["base_price"] * (income_sources[name]["price_exp"] ** gs["income_items"][name]['level']))
                        update_game()
                        if gs["money"] >= price:
                            gs["money"] -= price
                            gs["income_items"][name]['level'] += 1
                            st.toast(f"Upgraded {name} to level {gs['income_items'][name]['level']}!")
                            if gs["income_items"][name]['level'] == 1:
                                gs["income_items"][name]["last_collected"] = time.time()
                            bought += 1
                        else:
                            break
                    if bought > 0:
                        st.rerun()
                    else:
                        st.toast("Not enough money!")
                colC.write(f"min. needed: {price:,}$")
            else:
                buy_n_items_num = int(buy_n_items[:-1])
                total_price = 0
                for i in range(buy_n_items_num):
                    total_price += round(income_sources[name]["base_price"] * (income_sources[name]["price_exp"] ** gs["income_items"][name]['level'] + i))
                if colC.button(f"Buy {buy_n_items} {name}", key=f"buy_{name}"):
                    update_game()
                    if gs["money"] >= total_price:
                        gs["money"] -= total_price
                        gs["income_items"][name]['level'] += buy_n_items_num
                        st.toast(f"Upgraded {name} to level {gs['income_items'][name]['level']}!")
                        if gs["income_items"][name]['level'] == 1:
                            gs["income_items"][name]["last_collected"] = time.time()
                        st.rerun()
                    else:
                        st.toast(f"Not enough money! {total_price:,}$ needed.")
                colC.write(f"needed: {total_price:,}$")

            if gs["managers"][name] == 0:
                if gs["income_items"][name]['level'] >= manager_levels[0]:
                    if colD.button(f"Hire Manager", key=f"mgr_{name}"):
                        gs["managers"][name] = 1
                        st.toast(f"Manager hired for {name}!")
                        st.rerun()
                else:
                    colD.write(f"Reach lvl. {manager_levels[0]} to hire manager!")
            else:
                if gs["income_items"][name]['level'] >= manager_levels[gs["managers"][name]]:
                    if colD.button(f"Improve Manager (income x{manager_factor})", key=f"mgr_{name}"):
                        gs["managers"][name] += 1
                        st.toast(f"Manager hired for {name}!")
                        st.rerun()
                else:
                    colD.write(f"Reach lvl. {manager_levels[gs['managers'][name]]} to upgrade manager!")

    # Leaderboard & auto-save
    #show_leaderboard()
    #if time.time() - gs.get("last_saved", 0) > 300:
    #    save_progress(username, gs)
    #    gs["last_saved"] = time.time()
