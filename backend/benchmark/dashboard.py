import streamlit as st
import pandas as pd
import subprocess
import sys
from pathlib import Path
import time
import glob
import altair as alt

st.set_page_config(page_title="Watermarking Benchmark Dashboard", layout="wide")

st.title("Digital Watermarking: Block Size Benchmark")
st.markdown("""
This dashboard allows you to run the robustness benchmark and visualize the trade-offs between 
**Block Size**, **Success Rate**, and **Image Quality (PSNR)**.
""")

# --- Sidebar: Controls ---
st.sidebar.header("Controls")

# Removed "Run Benchmark Now" button as requested

# --- Main Content: Analysis ---

# Find all CSV files matching the pattern
# Search in current directory and backend/benchmark/ subdirectory to be flexible
patterns = [
    "benchmark_results_*.csv",
    "empirical_benchmark_*.csv",
    "backend/benchmark/benchmark_results_*.csv",
    "backend/benchmark/empirical_benchmark_*.csv"
]
found_files = []
for p in patterns:
    found_files.extend(glob.glob(p))

csv_files = sorted(list(set(found_files)), reverse=True)

if not csv_files:
    st.info("No benchmark results found. Click 'Run Benchmark Now' in the sidebar.")
else:
    selected_file = st.selectbox("Select Result File:", csv_files)
    
    if selected_file:
        df = pd.read_csv(selected_file)
        
        # Normalize column names for compatibility with different benchmark scripts
        # (e.g. handle empirical_benchmark vs run_block_size output)
        df = df.rename(columns={
            "PSNR_dB": "PSNR",
            "Duration_s": "Duration",
            "MarginUsed": "Margin",
            "ErrorCode": "Error"
        })
        
        # Handle Optimization column if it exists
        if "Optimization" in df.columns:
            st.info("Optimization Data Detected: Splitting results by Optimization State")
            opt_filter = st.radio("Filter by Optimization:", ["All", "Optimization ON (True)", "Optimization OFF (False)"], index=0)
            
            if opt_filter == "Optimization ON (True)":
                df = df[df["Optimization"] == True]
            elif opt_filter == "Optimization OFF (False)":
                df = df[df["Optimization"] == False]
        
        # Basic Stats
        st.header(f"Analysis: {selected_file}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Tests", len(df))
        c2.metric("Overall Success Rate", f"{(df['Success'].mean() * 100):.1f}%")
        c3.metric("Avg PSNR (Success)", f"{df[df['Success']==True]['PSNR'].mean():.2f} dB")
        c4.metric("Avg Duration", f"{df['Duration'].mean():.3f}s")

        # --- Visualizations ---
        
        st.subheader("Trade-off Analysis")
        
        # Create separate aggregations to handle PSNR zeros correctly
        # 1. Success Rate uses all data
        success_grouped = df.groupby("BlockSize")["Success"].mean() * 100
        
        # 2. PSNR uses ONLY successful tests (or non-zero PSNR)
        # Using PSNR > 0 filters out skips and major failures
        psnr_clean_df = df[df["PSNR"] > 0]
        psnr_grouped = psnr_clean_df.groupby("BlockSize")["PSNR"].mean()
        
        # 3. Duration uses all data
        duration_grouped = df.groupby("BlockSize")["Duration"].mean()
        
        # Combine into one DataFrame for charting
        grouped = pd.DataFrame({
            "Success %": success_grouped,
            "PSNR": psnr_grouped,
            "Duration": duration_grouped
        }).reset_index()
        
        tab1, tab2, tab3 = st.tabs(["Success Rate", "Image Quality (PSNR)", "Raw Data"])
        
        with tab1:
            st.markdown("##### Success Rate vs. Block Size")
            st.markdown("Larger blocks usually mean more robustness (higher success rate), but lower capacity.")
            
            if "Optimization" in df.columns and opt_filter == "All":
                 # If we have optimization data and showing all, group by both BlockSize and Optimization
                 chart_data = df.groupby(["BlockSize", "Optimization"])["Success"].mean().reset_index()
                 chart_data["Success"] *= 100
                 
                 chart = alt.Chart(chart_data).mark_line(point=True).encode(
                     x='BlockSize',
                     y='Success',
                     color='Optimization:N',
                     tooltip=['BlockSize', 'Success', 'Optimization']
                 ).interactive()
                 st.altair_chart(chart, use_container_width=True)
            else:
                 st.line_chart(grouped, x="BlockSize", y="Success %")
            
        with tab2:
            st.markdown("##### PSNR vs. Block Size (Successful Tests Only)")
            st.markdown("Higher PSNR means better image quality. Only tests with valid output are shown here.")
            # Drop NaN values for the chart if some block sizes had 0 successes
            
            if "Optimization" in df.columns and opt_filter == "All":
                 psnr_clean = df[df["PSNR"] > 0]
                 chart_data = psnr_clean.groupby(["BlockSize", "Optimization"])["PSNR"].mean().reset_index()
                 
                 chart = alt.Chart(chart_data).mark_line(point=True).encode(
                     x='BlockSize',
                     y=alt.Y('PSNR', scale=alt.Scale(zero=False)),
                     color='Optimization:N',
                     tooltip=['BlockSize', 'PSNR', 'Optimization']
                 ).interactive()
                 st.altair_chart(chart, use_container_width=True)
            else:
                st.line_chart(grouped.dropna(subset=["PSNR"]), x="BlockSize", y="PSNR")
            
        with tab3:
            st.dataframe(df)

        # --- Advanced View ---
        st.subheader("Detailed Breakdown by Image")
        
        # Select an image to see details
        images = df["Image"].unique()
        selected_image = st.selectbox("Filter by Image:", ["All"] + list(images))
        
        if selected_image != "All":
            filtered_df = df[df["Image"] == selected_image]
        else:
            filtered_df = df
            
        # Filter out 0 PSNR or failures for better visualization scale
        plot_df = filtered_df[filtered_df["PSNR"] > 0].copy()
            
        if not plot_df.empty:
            # Use Altair for better control over Y-axis scaling (zoom in)
            x_min = plot_df["BlockSize"].min()
            x_max = plot_df["BlockSize"].max()
            
            # Dynamic tooltip based on available columns
            tooltip_cols = ['Image', 'BlockSize', 'PSNR', 'Duration', 'Success', 'Margin']
            if "Optimization" in plot_df.columns:
                tooltip_cols.append("Optimization")

            chart = alt.Chart(plot_df).mark_circle(size=100, opacity=0.7).encode(
                x=alt.X('BlockSize', 
                        scale=alt.Scale(domain=[x_min - 1, x_max + 1]), 
                        axis=alt.Axis(tickMinStep=1)),
                # zero=False allow the axis to start near min value (e.g. 30) instead of 0
                y=alt.Y('PSNR', scale=alt.Scale(zero=False, padding=1)),
                color=alt.Color('Success', scale=alt.Scale(domain=[True, False], range=['#1f77b4', '#d62728'])), # Blue for Success, Red for Failure
                size='Duration',
                tooltip=tooltip_cols
            ).interactive()
            
            if "Optimization" in plot_df.columns and opt_filter == "All":
                 # Use shape to distinguish Optimization if viewing all
                 chart = chart.encode(
                     shape='Optimization:N'
                 )

            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No valid PSNR data to display for this selection.")
        
        if len(filtered_df) != len(plot_df):
            st.caption(f"*Note: {len(filtered_df) - len(plot_df)} failed/skipped tests (PSNR=0) are hidden from this chart to improve readability.*")
