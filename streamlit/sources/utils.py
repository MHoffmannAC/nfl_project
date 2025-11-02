import pandas as pd

import streamlit as st


def display_table(
    display_df: pd.DataFrame,
    highlight: int,
    highlight2: int | None = None,
    column_widths: list[int] | None = None,
) -> None:
    def _highlight_rows(row: pd.Series, num_rows: int, num_rows2: int) -> list[str]:
        return [
            "background-color: white; color: #00093a"
            if row.name < num_rows
            else "background-color: #00239c; color: white"
            if num_rows2 is not None and row.name < num_rows2
            else ""
            for _ in row
        ]

    styles = [
        {
            "selector": "table",
            "props": [("border-collapse", "collapse"), ("width", "400px")],
        },
        {
            "selector": "th, td",
            "props": [
                ("border", "1px solid #ddd"),
                ("padding", "8px"),
                ("text-align", "center"),
            ],
        },
        {
            "selector": "th",
            "props": [("background-color", "#800020"), ("color", "white")],
        },
    ]

    if column_widths is not None:
        styles += [
            {"selector": f".col{i}", "props": [("width", f"{width}px")]}
            for i, width in enumerate(column_widths)
        ]

    html = (
        display_df.reset_index()
        .style.set_table_styles(styles)
        .apply(_highlight_rows, axis=1, args=(highlight, highlight2))
        .hide(axis="index")
        .to_html()
    )

    # Center the table in a div
    st.markdown(
        f"""
        <div style="display:flex; justify-content:left;">
            <div style="width:600px;">
                {html}
        """,
        unsafe_allow_html=True,
    )
