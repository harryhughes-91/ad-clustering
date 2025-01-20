# -*- coding: utf-8 -*-
"""app.py"""

import streamlit as st
import pandas as pd
import os
from PIL import Image
import io
import tempfile


# Set the page configuration as the very first Streamlit command
st.set_page_config(layout="wide", page_title="My App", page_icon="📊")

def process_uploaded_files(uploaded_csv, uploaded_images):
    """
    Process uploaded CSV and image files
    Returns DataFrame with image paths
    """
    try:
        temp_dir = tempfile.mkdtemp()
        images_path = os.path.join(temp_dir, "images")
        os.makedirs(images_path, exist_ok=True)

        #Save uploaded images to a temporary directory
        uploaded_image_names = []
        for uploaded_file in uploaded_images:
            file_path = os.path.join(images_path, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            uploaded_image_names.append(uploaded_file.name)

        df = pd.read_csv(uploaded_csv)
        # Validate the existence of 'ad_id' column
        if 'ad_id' not in df.columns:
            st.error("The uploaded CSV file must contain an 'ad_id' column.")
            return None

        # Filter the DataFrame to only include rows with uploaded images
        df['image_name'] = df['ad_id'].apply(lambda x: f"{x}.png")  # Assuming PNG format
        df = df[df['image_name'].isin(uploaded_image_names)]

        df['image_path'] = df['ad_id'].apply(lambda x: os.path.join(images_path, f"{x}.png"))
        return df
    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        return None

def display_brand_images(brand_df):
    """Display images for selected brand"""
    cols = st.columns(4)
    for idx, (_, row) in enumerate(brand_df.head(4).iterrows()):
        with cols[idx]:
            try:
                img = Image.open(row['image_path'])
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")

def display_image_attributes(selected_row):
    """Display attributes for selected image"""
    attributes = [
        'pagename',
        'dominant_background_colour',
        'logo_present',
        'cluster',
        'tier'
    ]
    # Check if all attributes exist
    missing_attrs = [attr for attr in attributes if attr not in selected_row.index]
    if missing_attrs:
        st.error(f"Missing attributes in the selected row: {', '.join(missing_attrs)}")
        return

    attr_df = pd.DataFrame({
        'Attribute': attributes,
        'Label': [selected_row[attr] for attr in attributes]
    })
    st.table(attr_df)

def display_cluster_images(df, selected_row, selected_image):
    """Display images from the same cluster"""
    if 'cluster' not in df.columns:
        st.error("The dataset must contain a 'Cluster' column to display cluster images.")
        return

    cluster = selected_row['cluster']
    cluster_df = df[
        (df['cluster'] == cluster) &
        (df['ad_id'] != selected_image)
    ].head(6)

    cols = st.columns(6)
    for idx, (_, row) in enumerate(cluster_df.iterrows()):
        with cols[idx]:
            try:
                img = Image.open(row['image_path'])
                st.image(img, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading image: {str(e)}")

def display_cluster_distribution(df):
    """Display table showing number of ads in each cluster for different advertisers"""
    if 'cluster' not in df.columns or 'pagename' not in df.columns:
        st.error("The dataset must contain both 'cluster' and 'pagename' columns to display cluster distribution.")
        return
    
    # Create pivot table of cluster distribution
    cluster_dist = pd.pivot_table(
        df,
        values='ad_id',
        index='pagename',
        columns='cluster',
        aggfunc='count',
        fill_value=0
    )
    
    # Add total column
    cluster_dist['Total'] = cluster_dist.sum(axis=1)
    
    # Sort by total number of ads descending
    cluster_dist = cluster_dist.sort_values('Total', ascending=False)
    
    # Format column names
    cluster_dist.columns = [f'Cluster {col}' if col != 'Total' else col for col in cluster_dist.columns]
    
    st.subheader("Number of Ads in Each Cluster")
    st.dataframe(cluster_dist, use_container_width=True)

def main():
    try:
        st.title("Brand Image Browser")

        uploaded_csv = st.file_uploader("Upload CSV file", type="csv")
        uploaded_images = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

        if uploaded_csv is None or not uploaded_images:
            st.warning("Please upload both CSV file and images to continue")
            return

        df = process_uploaded_files(uploaded_csv, uploaded_images)
        if df is None:
            return
        
        # Display cluster distribution table
        display_cluster_distribution(df)

        st.sidebar.header("Search By Brand")
        if 'pagename' not in df.columns:
            st.error("The dataset must contain a 'Brand' column.")
            return

        brands = sorted(df['pagename'].unique())
        selected_brand = st.sidebar.selectbox("Select Brand", brands)

        brand_df = df[df['pagename'] == selected_brand]

        st.subheader("Images By Brand")
        display_brand_images(brand_df)

        st.subheader("Image Preview")
        selected_image = st.selectbox(
            "Select image to preview",
            brand_df['ad_id'].tolist(),
            format_func=lambda x: f"Ad ID: {x}"
        )

        if selected_image:
            selected_row = brand_df[brand_df['ad_id'] == selected_image].iloc[0]
            try:
                img = Image.open(selected_row['image_path'])
                st.image(img, use_container_width=False, width = 300)

                st.subheader("Image Attributes")
                display_image_attributes(selected_row)

                st.subheader("Images in Same Cluster")
                display_cluster_images(df, selected_row, selected_image)

            except Exception as e:
                st.error(f"Error displaying selected image: {str(e)}")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
