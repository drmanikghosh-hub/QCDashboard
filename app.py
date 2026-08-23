import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io

# --- Helper Functions ---

def evaluate_westgard_rules(data, mean, std):
    """Evaluates a sequence of data points against standard Westgard rules."""
    data_list = list(data)
    results = ["Accept"] * len(data_list)
    
    for i in range(len(data_list)):
        val = data_list[i]
        
        # 1. 1_3s Rule (Reject)
        if val > mean + 3*std or val < mean - 3*std:
            results[i] = "Reject (1_3s)"
            continue 
            
        # 2. 2_2s Rule (Reject)
        if i >= 1:
            prev_val = data_list[i-1]
            if (val > mean + 2*std and prev_val > mean + 2*std) or \
               (val < mean - 2*std and prev_val < mean - 2*std):
                results[i] = "Reject (2_2s)"
                continue
                
        # 3. R_4s Rule (Reject)
        if i >= 1:
            prev_val = data_list[i-1]
            if abs(val - prev_val) > 4 * std:
                results[i] = "Reject (R_4s)"
                continue
                
        # 4. 4_1s Rule (Reject)
        if i >= 3:
            last_4 = data_list[i-3:i+1]
            if all(v > mean + std for v in last_4) or all(v < mean - std for v in last_4):
                results[i] = "Reject (4_1s)"
                continue
                
        # 5. 10_x Rule (Reject)
        if i >= 9:
            last_10 = data_list[i-9:i+1] 
            if all(v > mean for v in last_10) or all(v < mean for v in last_10):
                results[i] = "Reject (10_x)"
                continue
                
        # 6. 1_2s Rule (Warning)
        if val > mean + 2*std or val < mean - 2*std:
            results[i] = "Warning (1_2s)"
            continue

    return results

def calculate_imr(data):
    """Calculates Individuals and Moving Range statistics and limits."""
    data_array = np.array(data)
    mr = np.abs(np.diff(data_array))
    mr = np.insert(mr, 0, np.nan)  # Pad first value with NaN
    
    x_bar = np.mean(data_array)
    mr_bar = np.nanmean(mr)
    
    # Statistical constants for n=2
    d2 = 1.128
    d4 = 3.267
    
    sigma_est = mr_bar / d2
    
    # Individuals limits
    ucl_i = x_bar + 3 * sigma_est
    lcl_i = x_bar - 3 * sigma_est
    
    # Moving range limits
    ucl_mr = d4 * mr_bar
    lcl_mr = 0
    
    return mr, x_bar, mr_bar, ucl_i, lcl_i, ucl_mr, lcl_mr

def calculate_cusum(data, target=None, k_factor=0.5, h_factor=4.0):
    """Calculates tabular CUSUM statistics."""
    data_array = np.array(data)
    mu_0 = np.mean(data_array) if target is None else target
    sigma = np.std(data_array)
    
    k = k_factor * sigma
    h = h_factor * sigma
    
    c_plus = np.zeros(len(data_array))
    c_minus = np.zeros(len(data_array))
    status = ["Accept"] * len(data_array)
    
    for i in range(1, len(data_array)):
        c_plus[i] = max(0, c_plus[i-1] + (data_array[i] - mu_0 - k))
        c_minus[i] = max(0, c_minus[i-1] + (mu_0 - k - data_array[i]))
        
        if c_plus[i] > h or c_minus[i] > h:
            status[i] = "Out of Control"
            
    return c_plus, c_minus, h, mu_0, sigma, status

# --- Streamlit UI Configuration ---
st.set_page_config(page_title="Multi-QC Chart Dashboard", layout="wide")
st.title("Comprehensive Quality Control Dashboard")
st.write("Upload an Excel file to evaluate data across Shewhart/Westgard, I-MR, and CUSUM control charts.")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.write("**Data Preview:**")
        st.dataframe(df.head())
        
        default_index = list(df.columns).index('Value') if 'Value' in df.columns else 0
        column_to_analyze = st.selectbox("Select column to analyze:", df.columns, index=default_index)
        data = df[column_to_analyze]
        
        # --- Create Tabs ---
        tab1, tab2, tab3 = st.tabs(["Shewhart & Westgard", "I-MR Chart", "CUSUM Chart"])
        
        # ==========================================
        # TAB 1: SHEWHART & WESTGARD
        # ==========================================
        with tab1:
            st.subheader("Shewhart Control Chart (Westgard Rules)")
            mean = np.mean(data)
            std_dev = np.std(data)
            
            df['Westgard_Decision'] = evaluate_westgard_rules(data, mean, std_dev)
            
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(y=data, mode='lines', line=dict(color='lightgray', width=2), showlegend=False))
            
            color_map = {
                "Accept": "green", "Warning (1_2s)": "orange", "Reject (1_3s)": "red",
                "Reject (2_2s)": "darkred", "Reject (R_4s)": "purple", 
                "Reject (4_1s)": "magenta", "Reject (10_x)": "brown"
            }
            
            for decision, color in color_map.items():
                subset = df[df['Westgard_Decision'] == decision]
                if not subset.empty:
                    fig1.add_trace(go.Scatter(
                        x=subset.index, y=subset[column_to_analyze], mode='markers',
                        name=decision, marker=dict(color=color, size=10, line=dict(color='black', width=1))
                    ))
            
            fig1.add_hline(y=mean, line_dash="solid", annotation_text="Mean", line_color="green", opacity=0.5)
            fig1.add_hline(y=mean + 2*std_dev, line_dash="dash", annotation_text="+2 SD", line_color="orange", opacity=0.5)
            fig1.add_hline(y=mean - 2*std_dev, line_dash="dash", annotation_text="-2 SD", line_color="orange", opacity=0.5)
            fig1.add_hline(y=mean + 3*std_dev, line_dash="dash", annotation_text="+3 SD", line_color="red", opacity=0.5)
            fig1.add_hline(y=mean - 3*std_dev, line_dash="dash", annotation_text="-3 SD", line_color="red", opacity=0.5)
            
            fig1.update_layout(xaxis_title="Run Number", yaxis_title=column_to_analyze, hovermode="x unified")
            st.plotly_chart(fig1, use_container_width=True)
            
            # Downloads for Tab 1
            col_a, col_b = st.columns(2)
            try:
                col_a.download_button("🖼️ Download Chart (PNG)", fig1.to_image(format="png", width=1200, height=600, scale=2), "shewhart_chart.png", "image/png")
            except Exception:
                col_a.info("Install 'kaleido' for PNG export.")
            col_b.download_button("🌐 Download Interactive Chart (HTML)", fig1.to_html(include_plotlyjs='cdn').encode('utf-8'), "shewhart_chart.html", "text/html")
        
        # ==========================================
        # TAB 2: I-MR CHART
        # ==========================================
        with tab2:
            st.subheader("Individuals & Moving Range (I-MR) Chart")
            mr, x_bar, mr_bar, ucl_i, lcl_i, ucl_mr, lcl_mr = calculate_imr(data)
            
            fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                                 subplot_titles=("Individual Value (I) Chart", "Moving Range (MR) Chart"))
            
            # Individual Plot
            fig2.add_trace(go.Scatter(y=data, mode='lines+markers', name='Individual Value', line=dict(color='blue')), row=1, col=1)
            fig2.add_hline(y=x_bar, line_dash="solid", annotation_text=f"Mean: {x_bar:.2f}", line_color="green", row=1, col=1)
            fig2.add_hline(y=ucl_i, line_dash="dash", annotation_text=f"UCL: {ucl_i:.2f}", line_color="red", row=1, col=1)
            fig2.add_hline(y=lcl_i, line_dash="dash", annotation_text=f"LCL: {lcl_i:.2f}", line_color="red", row=1, col=1)
            
            # Moving Range Plot
            fig2.add_trace(go.Scatter(y=mr, mode='lines+markers', name='Moving Range', line=dict(color='purple')), row=2, col=1)
            fig2.add_hline(y=mr_bar, line_dash="solid", annotation_text=f"MR Mean: {mr_bar:.2f}", line_color="green", row=2, col=1)
            fig2.add_hline(y=ucl_mr, line_dash="dash", annotation_text=f"UCL: {ucl_mr:.2f}", line_color="red", row=2, col=1)
            fig2.add_hline(y=lcl_mr, line_dash="dash", annotation_text=f"LCL: {lcl_mr:.2f}", line_color="red", row=2, col=1)
            
            fig2.update_layout(height=700, hovermode="x unified")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Downloads for Tab 2
            col_a, col_b = st.columns(2)
            try:
                col_a.download_button("🖼️ Download I-MR Chart (PNG)", fig2.to_image(format="png", width=1200, height=700, scale=2), "imr_chart.png", "image/png")
            except Exception:
                col_a.info("Install 'kaleido' for PNG export.")
            col_b.download_button("🌐 Download Interactive I-MR (HTML)", fig2.to_html(include_plotlyjs='cdn').encode('utf-8'), "imr_chart.html", "text/html")

        # ==========================================
        # TAB 3: CUSUM CHART
        # ==========================================
        with tab3:
            st.subheader("Cumulative Sum (CUSUM) Control Chart")
            
            col_param1, col_param2 = st.columns(2)
            k_input = col_param1.slider("Slack/Allowance Factor (k in SD units):", 0.1, 2.0, 0.5, 0.1)
            h_input = col_param2.slider("Decision Limit Factor (h in SD units):", 1.0, 10.0, 4.0, 0.5)
            
            c_plus, c_minus, h_val, mu_0, sigma, cusum_status = calculate_cusum(data, k_factor=k_input, h_factor=h_input)
            df['CUSUM_Decision'] = cusum_status
            
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(y=c_plus, mode='lines+markers', name='C+ (Upper Shift)', line=dict(color='crimson')))
            fig3.add_trace(go.Scatter(y=-c_minus, mode='lines+markers', name='C- (Lower Shift)', line=dict(color='royalblue')))
            
            fig3.add_hline(y=h_val, line_dash="dash", annotation_text=f"+H ({h_val:.2f})", line_color="red")
            fig3.add_hline(y=-h_val, line_dash="dash", annotation_text=f"-H ({-h_val:.2f})", line_color="red")
            fig3.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5)
            
            fig3.update_layout(title="Two-Sided CUSUM Chart", xaxis_title="Run Number", yaxis_title="Cumulative Sum", hovermode="x unified")
            st.plotly_chart(fig3, use_container_width=True)
            
            # Downloads for Tab 3
            col_a, col_b = st.columns(2)
            try:
                col_a.download_button("🖼️ Download CUSUM Chart (PNG)", fig3.to_image(format="png", width=1200, height=600, scale=2), "cusum_chart.png", "image/png")
            except Exception:
                col_a.info("Install 'kaleido' for PNG export.")
            col_b.download_button("🌐 Download Interactive CUSUM (HTML)", fig3.to_html(include_plotlyjs='cdn').encode('utf-8'), "cusum_chart.html", "text/html")

        # ==========================================
        # GLOBAL EXPORT SECTION
        # ==========================================
        st.markdown("---")
        st.subheader("Data Table & Export Flagged Points")
        
        flagged_df = df[(df['Westgard_Decision'] != "Accept") | (df.get('CUSUM_Decision') == "Out of Control")]
        
        st.dataframe(df)
        
        if not flagged_df.empty:
            exp_col1, exp_col2 = st.columns(2)
            csv_data = flagged_df.to_csv(index=False).encode('utf-8')
            exp_col1.download_button("📥 Download Flagged Data (CSV)", csv_data, "qc_flagged_report.csv", "text/csv")
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                flagged_df.to_excel(writer, index=False, sheet_name='QC Violations')
            exp_col2.download_button("📊 Download Flagged Data (Excel)", buffer.getvalue(), "qc_flagged_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.success("All points across evaluated charts are within normal limits!")

    except Exception as e:
        st.error(f"Error processing file: {e}")