import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from rapidfuzz.fuzz import ratio
from datetime import datetime

st.title("Dataset Search Tool")

# File Upload
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

# User Inputs
first_name = st.text_input("Enter First Name")
last_name = st.text_input("Enter Last Name")
date_of_birth = st.text_input("Enter Date of Birth (MM/DD/YYYY)")

def find_person_in_dataset(file, first_name, last_name, dob):
    try:
        target_dob = datetime.strptime(dob.strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
        target_first_name = first_name.strip().upper()
        target_last_name = last_name.strip().upper()

        df = pd.read_excel(file, dtype=str, engine="openpyxl")
        df.columns = df.columns.str.strip().str.upper()

        required_columns = ["FIRST NAME", "LAST NAME", "DATE OF BIRTH"]
        if not all(col in df.columns for col in required_columns):
            st.error(f"Missing one or more required columns: {required_columns}")
            return None

        matches = []
        potential_dob_matches = []

        df["FIRST NAME"] = df["FIRST NAME"].str.strip().str.upper()
        df["LAST NAME"] = df["LAST NAME"].str.strip().str.upper()
        df["DATE OF BIRTH"] = pd.to_datetime(df["DATE OF BIRTH"], errors="coerce").dt.strftime("%Y-%m-%d")

        for _, row in df.iterrows():
            if pd.isna(row["DATE OF BIRTH"]) or pd.isna(row["FIRST NAME"]) or pd.isna(row["LAST NAME"]):
                continue

            if str(row["DATE OF BIRTH"]).strip() == target_dob:
                potential_dob_matches.append(row)
                first_name_similarity = ratio(row["FIRST NAME"], target_first_name)
                last_name_similarity = ratio(row["LAST NAME"], target_last_name)

                if first_name_similarity >= 75 and last_name_similarity >= 75:
                    matches.append(row)

        return matches, potential_dob_matches

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

if st.button("Search") and uploaded_file and first_name and last_name and date_of_birth:
    with st.spinner("Searching..."):
        results, dob_matches = find_person_in_dataset(uploaded_file, first_name, last_name, date_of_birth)

        if results:
            st.success(f"✅ Found {len(results)} exact matches!")
            st.write(pd.DataFrame(results))
        elif dob_matches:
            st.warning(f"⚠️ No exact name matches, but {len(dob_matches)} records have the same DOB.")
            st.write(pd.DataFrame(dob_matches))
        else:
            st.error("❌ No matches found.")
