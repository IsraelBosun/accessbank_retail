import streamlit as st
import pandas as pd
from datetime import datetime

# Columns to drop from display
columns_to_drop = [
    'PRODUCT_NAME', 'ADJ_FACILITY_TYPE', 'CBN_SUB_SECTOR', 'CBN_SECTOR_ADJUSTED',
    'DPD', 'SIMULATED EOM MAY', 'EOM APRIL', 'RATE'
]

# Load and clean the data
@st.cache_data
def load_data():
    df = pd.read_excel("retaill.xlsx", sheet_name = "Direct")
    df.columns = df.columns.str.strip()  # Remove leading/trailing spaces
    return df

df = load_data()

# Helper function to format DataFrame for display (numbers with commas, dates without time),
# and drop specified columns if they exist
def format_df_for_display(display_df):
    df_to_show = display_df.copy()

    # Drop unwanted columns if they exist
    cols_to_drop_existing = [col for col in columns_to_drop if col in df_to_show.columns]
    df_to_show = df_to_show.drop(columns=cols_to_drop_existing)

    # Format numeric columns with commas and two decimals
    for col in df_to_show.select_dtypes(include=["number"]).columns:
        df_to_show[col] = df_to_show[col].map(lambda x: f"{x:,.2f}" if pd.notnull(x) else "")

    # Format datetime columns to date only (no time)
    for col in df_to_show.select_dtypes(include=["datetime64"]).columns:
        df_to_show[col] = df_to_show[col].dt.strftime("%Y-%m-%d")

    return df_to_show

# Create tabs
tab1, tab2, tab3 = st.tabs(["📊 Maturing Obligations", "❗ Expired/Unauthorized Facilities", "⚠️ Overlimit & Unpaid Panels"])

# -------------------- TAB 1: Maturing Obligations --------------------
with tab1:
    st.title("📊 Maturing Obligations Dashboard")

    if "RANGE" not in df.columns:
        st.error("'RANGE' column not found.")
        st.write("Available columns:", df.columns.tolist())
    else:
        category_labels = {
            "PERF": "🟩 Green (PERF)",
            "90+DPD": "🔵 Blue (90+ DPD)",
            "61-90DPD": "🟨 Yellow (61–90 DPD)",
            "31-60DPD": "🌸 Pink (31–60 DPD)",
            "1-30DPD": "🟥 Red (1–30 DPD)"
        }

        st.markdown("""
        ### View obligations categorized by DPD (Days Past Due):
        - 🟩 **Green**: PERF (Performing)
        - 🔵 **Blue**: 90+ DPD
        - 🟨 **Yellow**: 61–90 DPD
        - 🌸 **Pink**: 31–60 DPD
        - 🟥 **Red**: 1–30 DPD
        """)

        selected_range = st.selectbox(
            "📌 Select DPD Category",
            options=list(category_labels.keys()),
            format_func=lambda x: category_labels[x]
        )

        filtered_df = df[df["RANGE"] == selected_range]

        st.subheader(f"Results for: {category_labels[selected_range]}")

        df_display = format_df_for_display(filtered_df)
        st.dataframe(df_display, use_container_width=True)
        st.success(f"Total records: {len(filtered_df)}")

# -------------------- TAB 2: Expired/Unauthorized Facilities --------------------
with tab2:
    st.title("❗ Expired/Unauthorized Facilities")

    if "MATURITY_DATE" not in df.columns:
        st.error("'MATURITY_DATE' column not found.")
        st.write("Available columns:", df.columns.tolist())
    else:
        df["MATURITY_DATE"] = pd.to_datetime(df["MATURITY_DATE"], errors="coerce")
        today = pd.to_datetime(datetime.today().date())

        expired_df = df[df["MATURITY_DATE"] < today]

        st.markdown("### Accounts that have exceeded their maturity date without renewal or are outside approved limits.")

        df_display = format_df_for_display(expired_df)
        st.dataframe(df_display, use_container_width=True)
        st.warning(f"Total expired/unauthorized records: {len(expired_df)}")

# -------------------- TAB 3: Overlimit & Unpaid Panels --------------------
with tab3:
    st.title("⚠️ Overlimit & Unpaid Panels")

    missing_cols = []
    for col in ["OVERLIMIT", "UNPAID"]:
        if col not in df.columns:
            missing_cols.append(col)
    if missing_cols:
        st.error(f"Columns missing in data: {missing_cols}")
        st.write("Available columns:", df.columns.tolist())
    else:
        # Convert to numeric, coerce errors to NaN (to handle possible non-numeric data)
        df["OVERLIMIT"] = pd.to_numeric(df["OVERLIMIT"], errors='coerce').fillna(0)
        df["UNPAID"] = pd.to_numeric(df["UNPAID"], errors='coerce').fillna(0)

        # Filter rows where OVERLIMIT is less than 0 (negative values)
        overlimit_df = df[df["OVERLIMIT"] < 0]

        # Filter rows where UNPAID is greater than 0
        unpaid_df = df[df["UNPAID"] > 0]

        st.subheader("Records with Overlimit (less than 0)")
        df_display = format_df_for_display(overlimit_df)
        st.dataframe(df_display, use_container_width=True)
        st.info(f"Total Overlimit records: {len(overlimit_df)}")

        st.subheader("Records with Unpaid (greater than 0)")
        df_display = format_df_for_display(unpaid_df)
        st.dataframe(df_display, use_container_width=True)
        st.info(f"Total Unpaid records: {len(unpaid_df)}")
