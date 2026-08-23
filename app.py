import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import io
import os

# --- Page Setup ---
st.set_page_config(page_title="ARoHaN Lab - Multi-QC Chart Dashboard", layout="wide")

# --- Header Section with ARoHaN Lab Branding ---
col_logo, col_title = st.columns([1, 4])

# Path to logo (or uploaded image file)
logo_path = "AroHaN_Lab.png"

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=160)
    else:
        st.write("🔬 **ARoHaN Lab**")

with col_title:
    st.title("ARoHaN Lab - Quality Control Dashboard")
    st.markdown(
        """
        *Developed by **ARoHaN Lab** (Advance Research on Herbals and Naturals, Department of Pharmaceutical Sciences & Technology, BIT Mesra • PI: Dr. Manik Ghosh).*
        This interactive tool provides real-time quality assurance for weight variations and analytical batch metrics using **Shewhart/Westgard Rules**, **Individual-Moving Range (I-MR)**, and **Cumulative Sum (CUSUM)** control charts.
        """
    )

st.markdown("---")

# --- Interactive Spike Line Helper ---
def apply_interactive_spikelines(fig):
    """Adds vertical spike/crosshair line for matching values against limits on hover."""
    fig.update_layout(
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255, 255, 255, 0.9)", font_size=12)
    )
    fig.update_xaxes(
        showspikes=True,
        spikethickness=1.5,
        spikecolor="#D32F2F",
        spikemode="across",
        spikesnap="cursor"
    )
    return fig

# --- High-DPI 300 DPI Matplotlib Image Generators ---

def render_shewhart_matplotlib(df, col_name, mean, std_dev, dpi=300):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    ax.plot(df['Run Number'], df[col_name], color='lightgray', linewidth=1.5, zorder=1)
    
    color_map = {
        "Accept": "green", "Warning (1_2s)": "orange", "Reject (1_3s)": "red",
        "Reject (2_2s)": "darkred", "Reject (R_4s)": "purple", 
        "Reject (4_1s)": "magenta", "Reject (10_x)": "brown"
    }
    
    for decision, color in color_map.items():
        subset = df[df['Westgard_Decision'] == decision]
        if not subset.empty:
            ax.scatter(subset['Run Number'], subset[col_name], color=color, label=decision, zorder=2, edgecolors='black', s=50)
            
    ax.axhline(mean, color='green', linestyle='-', alpha=0.7, label=f'Mean ({mean:.2f})')
    ax.axhline(mean + 2*std_dev, color='orange', linestyle='--', alpha=0.7, label=f'+2 SD ({mean+2*std_dev:.2f})')
    ax.axhline(mean - 2*std_dev, color='orange', linestyle='--', alpha=0.7, label=f'-2 SD ({mean-2*std_dev:.2f})')
    ax.axhline(mean + 3*std_dev, color='red', linestyle='--', alpha=0.7, label=f'+3 SD ({mean+3*std_dev:.2f})')
    ax.axhline(mean - 3*std_dev, color='red', linestyle='--', alpha=0.7, label=f'-3 SD ({mean-3*std_dev:.2f})')
    
    ax.set_title("Shewhart Control Chart (Westgard Rules)", fontsize=14, fontweight='bold')
    ax.set_xlabel("Run Number", fontsize=11); ax.set_ylabel(col_name, fontsize=11)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left'); ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    
    png_buf, jpg_buf = io.BytesIO(), io.BytesIO()
    fig.savefig(png_buf, format='png', dpi=dpi, bbox_inches='tight')
    fig.savefig(jpg_buf, format='jpeg', dpi=dpi, bbox_inches='tight')
    png_buf.seek(0); jpg_buf.seek(0)
    plt.close(fig)
    return png_buf.getvalue(), jpg_buf.getvalue()

def render_imr_matplotlib(data, dpi=300):
    mr = np.abs(np.diff(data))
    mr = np.insert(mr, 0, np.nan)
    x_bar = np.mean(data)
    mr_bar = np.nanmean(mr)
    sigma_est = mr_bar / 1.128
    ucl_i, lcl_i = x_bar + 3 * sigma_est, x_bar - 3 * sigma_est
    ucl_mr = 3.267 * mr_bar
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), dpi=dpi, sharex=True)
    ax1.plot(range(1, len(data)+1), data, marker='o', color='royalblue')
    ax1.axhline(x_bar, color='green', label=f'Mean ({x_bar:.2f})')
    ax1.axhline(ucl_i, color='red', linestyle='--', label=f'UCL ({ucl_i:.2f})')
    ax1.axhline(lcl_i, color='red', linestyle='--', label=f'LCL ({lcl_i:.2f})')
    ax1.set_title("Individual Value (I) Chart", fontweight='bold'); ax1.set_ylabel("Value"); ax1.legend(loc='upper left'); ax1.grid(True, linestyle=':', alpha=0.6)

    ax2.plot(range(1, len(data)+1), mr, marker='s', color='purple')
    ax2.axhline(mr_bar, color='green', label=f'MR Mean ({mr_bar:.2f})')
    ax2.axhline(ucl_mr, color='red', linestyle='--', label=f'UCL ({ucl_mr:.2f})')
    ax2.set_title("Moving Range (MR) Chart", fontweight='bold'); ax2.set_xlabel("Run Number"); ax2.set_ylabel("Moving Range"); ax2.legend(loc='upper left'); ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    png_buf, jpg_buf = io.BytesIO(), io.BytesIO()
    fig.savefig(png_buf, format='png', dpi=dpi, bbox_inches='tight')
    fig.savefig(jpg_buf, format='jpeg', dpi=dpi, bbox_inches='tight')
    png_buf.seek(0); jpg_buf.seek(0)
    plt.close(fig)
    return png_buf.getvalue(), jpg_buf.getvalue()

def render_cusum_matplotlib(c_plus, c_minus, h_val, dpi=300):
    fig, ax = plt.subplots(figsize=(12, 6), dpi=dpi)
    runs = range(1, len(c_plus) + 1)
    ax.plot(runs, c_plus, marker='o', color='crimson', label='C+ (Upper Shift)')
    ax.plot(runs, -c_minus, marker='s', color='royalblue', label='C- (Lower Shift)')
    ax.axhline(h_val, color='red', linestyle='--', label=f'+H ({h_val:.2f})')
    ax.axhline(-h_val, color='red', linestyle='--', label=f'-H ({-h_val:.2f})')
    ax.axhline(0, color='gray', linewidth=1)
    ax.set_title("Cumulative Sum (CUSUM) Chart", fontsize=14, fontweight='bold'); ax.set_xlabel("Run Number"); ax.set_ylabel("Cumulative Sum"); ax.legend(loc='upper left'); ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    
    png_buf, jpg_buf = io.BytesIO(), io.BytesIO()
    fig.savefig(png_buf, format='png', dpi=dpi, bbox_inches='tight')
    fig.savefig(jpg_buf, format='jpeg', dpi=dpi, bbox_inches='tight')
    png_buf.seek(0); jpg_buf.seek(0)
    plt.close(fig)
    return png_buf.getvalue(), jpg_buf.getvalue()

# --- QC Algorithm Evaluators ---

def evaluate_westgard_rules(data, mean, std):
    data_list = list(data)
    results = ["Accept"] * len(data_list)
    for i in range(len(data_list)):
        val = data_list[i]
        if val > mean + 3*std or val < mean - 3*std:
            results[i] = "Reject (1_3s)"; continue 
        if i >= 1:
            prev = data_list[i-1]
            if (val > mean + 2*std and prev > mean + 2*std) or (val < mean - 2*std and prev < mean - 2*std):
                results[i] = "Reject (2_2s)"; continue
            if abs(val - prev) > 4 * std:
                results[i] = "Reject (R_4s)"; continue
        if i >= 3:
            last_4 = data_list[i-3:i+1]
            if all(v > mean + std for v in last_4) or all(v < mean - std for v in last_4):
                results[i] = "Reject (4_1s)"; continue
        if i >= 9:
            last_10 = data_list[i-9:i+1] 
            if all(v > mean for v in last_10) or all(v < mean for v in last_10):
                results[i] = "Reject (10_x)"; continue
        if val > mean + 2*std or val < mean - 2*std:
            results[i] = "Warning (1_2s)"; continue
    return results

def calculate_imr(data):
    data_array = np.array(data)
    mr = np.insert(np.abs(np.diff(data_array)), 0, np.nan)
    x_bar = np.mean(data_array)
    mr_bar = np.nanmean(mr)
    sigma_est = mr_bar / 1.128
    return mr, x_bar, mr_bar, x_bar + 3*sigma_est, x_bar - 3*sigma_est, 3.267*mr_bar, 0

def calculate_cusum(data, target=None, k_factor=0.5, h_factor=4.0):
    data_array = np.array(data)
    mu_0 = np.mean(data_array) if target is None else target
    sigma = np.std(data_array)
    k, h = k_factor * sigma, h_factor * sigma
    c_plus, c_minus = np.zeros(len(data_array)), np.zeros(len(data_array))
    status = ["Accept"] * len(data_array)
    for i in range(1, len(data_array)):
        c_plus[i] = max(0, c_plus[i-1] + (data_array[i] - mu_0 - k))
        c_minus[i] = max(0, c_minus[i-1] + (mu_0 - k - data_array[i]))
        if c_plus[i] > h or c_minus[i] > h:
            status[i] = "Out of Control"
    return c_plus, c_minus, h, mu_0, sigma, status

# --- File Processing & Display ---

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

plotly_300dpi_config = {
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'arohan_qc_chart',
        'height': 900,
        'width': 1600,
        'scale': 3.125
    }
}

if uploaded_file:
    try:
        xl = pd.ExcelFile(uploaded_file)
        col_s1, col_s2 = st.columns(2)
        selected_sheet = col_s1.selectbox("Select Excel Sheet:", xl.sheet_names, index=len(xl.sheet_names)-1)
        df_raw = xl.parse(selected_sheet)
        selected_col = col_s2.selectbox("Select column to analyze:", df_raw.columns)
        
        clean_series = pd.to_numeric(df_raw[selected_col], errors='coerce').dropna().reset_index(drop=True)
        
        if clean_series.empty:
            st.error("Selected column contains no valid numeric data.")
        else:
            data = clean_series
            df = pd.DataFrame({'Run Number': range(1, len(data) + 1), selected_col: data})
            
            tab1, tab2, tab3 = st.tabs(["Shewhart & Westgard", "I-MR Chart", "CUSUM Chart"])
            
            # --- TAB 1: SHEWHART ---
            with tab1:
                st.subheader("Shewhart Control Chart (Westgard Rules)")
                mean, std_dev = np.mean(data), np.std(data)
                df['Westgard_Decision'] = evaluate_westgard_rules(data, mean, std_dev)
                
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=df['Run Number'], y=data, mode='lines', name='Value', line=dict(color='lightgray', width=2)))
                
                colors = {"Accept": "green", "Warning (1_2s)": "orange", "Reject (1_3s)": "red", "Reject (2_2s)": "darkred", "Reject (R_4s)": "purple", "Reject (4_1s)": "magenta", "Reject (10_x)": "brown"}
                for dec, col in colors.items():
                    sub = df[df['Westgard_Decision'] == dec]
                    if not sub.empty:
                        fig1.add_trace(go.Scatter(x=sub['Run Number'], y=sub[selected_col], mode='markers', name=dec, marker=dict(color=col, size=10)))
                
                fig1.add_hline(y=mean, line_color="green", name="Mean", annotation_text=f"Mean ({mean:.2f})")
                fig1.add_hline(y=mean + 2*std_dev, line_dash="dash", line_color="orange", annotation_text=f"+2 SD ({mean+2*std_dev:.2f})")
                fig1.add_hline(y=mean - 2*std_dev, line_dash="dash", line_color="orange", annotation_text=f"-2 SD ({mean-2*std_dev:.2f})")
                fig1.add_hline(y=mean + 3*std_dev, line_dash="dash", line_color="red", annotation_text=f"+3 SD ({mean+3*std_dev:.2f})")
                fig1.add_hline(y=mean - 3*std_dev, line_dash="dash", line_color="red", annotation_text=f"-3 SD ({mean-3*std_dev:.2f})")
                
                fig1 = apply_interactive_spikelines(fig1)
                st.plotly_chart(fig1, use_container_width=True, config=plotly_300dpi_config)
                
                png_bytes, jpg_bytes = render_shewhart_matplotlib(df, selected_col, mean, std_dev, dpi=300)
                c1, c2, c3 = st.columns(3)
                c1.download_button("🖼️ Download 300 DPI PNG", png_bytes, "shewhart_300dpi.png", "image/png")
                c2.download_button("🖼️ Download 300 DPI JPEG", jpg_bytes, "shewhart_300dpi.jpg", "image/jpeg")
                c3.download_button("🌐 Download Interactive HTML", fig1.to_html(include_plotlyjs='cdn').encode('utf-8'), "shewhart.html", "text/html")

            # --- TAB 2: I-MR ---
            with tab2:
                st.subheader("Individuals & Moving Range (I-MR) Chart")
                mr, x_bar, mr_bar, ucl_i, lcl_i, ucl_mr, lcl_mr = calculate_imr(data)
                
                fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Individual Value (I)", "Moving Range (MR)"))
                fig2.add_trace(go.Scatter(x=df['Run Number'], y=data, mode='lines+markers', name='Individual Value', line=dict(color='blue')), row=1, col=1)
                fig2.add_hline(y=x_bar, line_color="green", annotation_text=f"Mean ({x_bar:.2f})", row=1, col=1)
                fig2.add_hline(y=ucl_i, line_dash="dash", line_color="red", annotation_text=f"UCL ({ucl_i:.2f})", row=1, col=1)
                fig2.add_hline(y=lcl_i, line_dash="dash", line_color="red", annotation_text=f"LCL ({lcl_i:.2f})", row=1, col=1)
                
                fig2.add_trace(go.Scatter(x=df['Run Number'], y=mr, mode='lines+markers', name='Moving Range', line=dict(color='purple')), row=2, col=1)
                fig2.add_hline(y=mr_bar, line_color="green", annotation_text=f"MR Mean ({mr_bar:.2f})", row=2, col=1)
                fig2.add_hline(y=ucl_mr, line_dash="dash", line_color="red", annotation_text=f"UCL ({ucl_mr:.2f})", row=2, col=1)
                
                fig2 = apply_interactive_spikelines(fig2)
                st.plotly_chart(fig2, use_container_width=True, config=plotly_300dpi_config)
                
                png_imr, jpg_imr = render_imr_matplotlib(data, dpi=300)
                c1, c2, c3 = st.columns(3)
                c1.download_button("🖼️ Download 300 DPI PNG", png_imr, "imr_300dpi.png", "image/png")
                c2.download_button("🖼️ Download 300 DPI JPEG", jpg_imr, "imr_300dpi.jpg", "image/jpeg")
                c3.download_button("🌐 Download Interactive HTML", fig2.to_html(include_plotlyjs='cdn').encode('utf-8'), "imr.html", "text/html")

            # --- TAB 3: CUSUM ---
            with tab3:
                st.subheader("Cumulative Sum (CUSUM) Control Chart")
                cp1, cp2 = st.columns(2)
                k_val = cp1.slider("Slack Factor (k):", 0.1, 2.0, 0.5, 0.1)
                h_val = cp2.slider("Decision Limit (h):", 1.0, 10.0, 4.0, 0.5)
                
                c_plus, c_minus, h_calc, _, _, cusum_status = calculate_cusum(data, k_factor=k_val, h_factor=h_val)
                df['CUSUM_Decision'] = cusum_status
                
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=df['Run Number'], y=c_plus, mode='lines+markers', name='C+ (Upper Shift)', line=dict(color='crimson')))
                fig3.add_trace(go.Scatter(x=df['Run Number'], y=-c_minus, mode='lines+markers', name='C- (Lower Shift)', line=dict(color='royalblue')))
                fig3.add_hline(y=h_calc, line_dash="dash", line_color="red", annotation_text=f"+H ({h_calc:.2f})")
                fig3.add_hline(y=-h_calc, line_dash="dash", line_color="red", annotation_text=f"-H ({-h_calc:.2f})")
                fig3.add_hline(y=0, line_dash="solid", line_color="gray")
                
                fig3 = apply_interactive_spikelines(fig3)
                st.plotly_chart(fig3, use_container_width=True, config=plotly_300dpi_config)
                
                png_cusum, jpg_cusum = render_cusum_matplotlib(c_plus, c_minus, h_calc, dpi=300)
                c1, c2, c3 = st.columns(3)
                c1.download_button("🖼️ Download 300 DPI PNG", png_cusum, "cusum_300dpi.png", "image/png")
                c2.download_button("🖼️ Download 300 DPI JPEG", jpg_cusum, "cusum_300dpi.jpg", "image/jpeg")
                c3.download_button("🌐 Download Interactive HTML", fig3.to_html(include_plotlyjs='cdn').encode('utf-8'), "cusum.html", "text/html")

    except Exception as e:
        st.error(f"Error processing file: {e}")
