import streamlit as st
import pandas as pd
from io import BytesIO
from rapidfuzz.fuzz import ratio
import time

st.title("Dataset Search Tool")

# File Uploads
uploaded_large = st.file_uploader("Upload Main Dataset (Excel)", type=["xlsx"])
uploaded_small = st.file_uploader("Upload Matching Dataset (Excel)", type=["xlsx"])

def find_people_in_dataset(large_file, small_file):
    try:
        # Load datasets
        df_large = pd.read_excel(large_file, dtype=str, engine="openpyxl")
        df_small = pd.read_excel(small_file, dtype=str, engine="openpyxl")

        # Standardize column names
        df_large.columns = df_large.columns.str.strip().str.upper()
        df_small.columns = df_small.columns.str.strip().str.upper()

        required_large_cols = ["LAST NAME", "FIRST NAME", "DATE OF BIRTH"]
        required_small_cols = ["FIRST NAME", "LAST NAME", "DATE OF BIRTH"]

        if not all(col in df_large.columns for col in required_large_cols):
            st.error(f"Large dataset is missing required columns: {required_large_cols}")
            return None
        if not all(col in df_small.columns for col in required_small_cols):
            st.error(f"Small dataset is missing required columns: {required_small_cols}")
            return None

        # Clean data (uppercase & strip whitespace)
        df_large["FIRST NAME"] = df_large["FIRST NAME"].str.strip().str.upper()
        df_large["LAST NAME"] = df_large["LAST NAME"].str.strip().str.upper()
        df_large["DATE OF BIRTH"] = pd.to_datetime(df_large["DATE OF BIRTH"], errors="coerce").dt.strftime("%Y-%m-%d")

        df_small["FIRST NAME"] = df_small["FIRST NAME"].str.strip().str.upper()
        df_small["LAST NAME"] = df_small["LAST NAME"].str.strip().str.upper()
        df_small["DATE OF BIRTH"] = pd.to_datetime(df_small["DATE OF BIRTH"], errors="coerce").dt.strftime("%Y-%m-%d")

        results = []
        summary_results = []

        # Loop through each entry in the small dataset
        for _, person in df_small.iterrows():
            target_first_name = person["FIRST NAME"]
            target_last_name = person["LAST NAME"]
            target_dob = person["DATE OF BIRTH"]

            st.write(f"🔍 Searching for: {target_first_name} {target_last_name}, DOB: {target_dob}")

            # Filter large dataset by DOB first (FAST SEARCH)
            dob_matches = df_large[df_large["DATE OF BIRTH"] == target_dob]
            exact_matches = []

            # Apply fuzzy matching on filtered data
            for _, row in dob_matches.iterrows():
                first_name_similarity = ratio(row["FIRST NAME"], target_first_name)
                last_name_similarity = ratio(row["LAST NAME"], target_last_name)

                if first_name_similarity >= 75 and last_name_similarity >= 75:
                    exact_matches.append(row)

            # Save results
            if exact_matches:
                results.extend(exact_matches)
                st.success(f"✅ Found {len(exact_matches)} exact matches for {target_first_name} {target_last_name}")
            else:
                st.warning(f"⚠️ No exact name match, but {len(dob_matches)} records have the same DOB.")

            # Save summary result
            summary_results.append({
                "FIRST NAME": target_first_name,
                "LAST NAME": target_last_name,
                "DATE OF BIRTH": target_dob,
                "DOB MATCH COUNT": len(dob_matches),
                "EXACT MATCH COUNT": len(exact_matches)
            })

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        summary_df = pd.DataFrame(summary_results)

        # Save to an Excel file in memory
        output = BytesIO()
        
        # Ensure data is properly written before saving
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if not results_df.empty:
                results_df.to_excel(writer, sheet_name="Matches", index=False)
            if not summary_df.empty:
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
        output.seek(0)  # Move the buffer position to the beginning

        return output

    except Exception as e:
        st.error(f"Error processing files: {e}")
        return None

if st.button("Search") and uploaded_large and uploaded_small:
    with st.spinner("Searching... This may take a few minutes."):
        excel_file = find_people_in_dataset(uploaded_large, uploaded_small)
        if excel_file:
            st.download_button(
                "Download Results", 
                excel_file, 
                file_name="search_results.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
