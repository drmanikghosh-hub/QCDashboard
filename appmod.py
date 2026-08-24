import base64
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="ARoHaN Lab - Advanced SPC & Quality Control Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for ARoHaN Lab Header and Styling
st.markdown(
    """
    <style>
    .arohan-header {
        background: linear-gradient(135deg, #002B49 0%, #104E8B 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .arohan-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .arohan-subtitle {
        font-size: 15px;
        color: #E0E0E0;
    }
    .key-takeaway-box {
        background-color: #F0F7FF;
        border-left: 5px solid #0056B3;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper function to generate crosshair plotly config
def apply_crosshair_layout(fig, height=500, title=""):
  fig.update_layout(
      title=title,
      height=height,
      hovermode="x unified",
      legend=dict(
          orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
      ),
      margin=dict(l=40, r=40, t=60, b=40),
  )
  fig.update_xaxes(
      showspikes=True,
      spikethickness=1,
      spikecolor="gray",
      spikemode="across",
      spikesnap="cursor",
  )
  fig.update_yaxes(
      showspikes=True, spikethickness=1, spikecolor="gray", spikemode="across"
  )
  return fig

# Helper function for Publication-Ready Downloads
def add_download_options(fig, filename):
    st.markdown("###### Publication-Ready Downloads")
    dl_col1, dl_col2, dl_col3 = st.columns(3)
    
    # 1. Interactive HTML Export
    html_buffer = io.StringIO()
    fig.write_html(html_buffer, include_plotlyjs="cdn")
    html_bytes = html_buffer.getvalue().encode()
    dl_col1.download_button(
        label="🌐 Download Interactive HTML",
        data=html_bytes,
        file_name=f"{filename}.html",
        mime="text/html",
        key=f"{filename}_html"
    )

    # 2. High-Resolution PNG & SVG (Requires 'kaleido' library)
    try:
        # scale=3 acts as a multiplier to approximate 300+ DPI output
        png_bytes = fig.to_image(format="png", width=1000, height=600, scale=3)
        dl_col2.download_button(
            label="🖼️ Download High-Res PNG (300 DPI)",
            data=png_bytes,
            file_name=f"{filename}.png",
            mime="image/png",
            key=f"{filename}_png"
        )
        
        svg_bytes = fig.to_image(format="svg", width=1000, height=600)
        dl_col3.download_button(
            label="📈 Download Vector SVG",
            data=svg_bytes,
            file_name=f"{filename}.svg",
            mime="image/svg+xml",
            key=f"{filename}_svg"
        )
    except Exception as e:
        dl_col2.info("💡 Note: Please run `pip install -U kaleido` to enable SVG and High-Res PNG exports.")


# --- QC Algorithm Evaluators ---
def evaluate_westgard_rules(data, mean, std):
    """Evaluates multi-rule Westgard criteria for a sequence of values."""
    data_list = list(data)
    results = ["Accept"] * len(data_list)
    for i in range(len(data_list)):
        val = data_list[i]
        # Rule 1_3s
        if val > mean + 3*std or val < mean - 3*std:
            results[i] = "Reject (1_3s)"; continue 
        
        if i >= 1:
            prev = data_list[i-1]
            # Rule 2_2s
            if (val > mean + 2*std and prev > mean + 2*std) or (val < mean - 2*std and prev < mean - 2*std):
                results[i] = "Reject (2_2s)"; continue
            # Rule R_4s
            if abs(val - prev) > 4 * std:
                results[i] = "Reject (R_4s)"; continue
                
        if i >= 3:
            last_4 = data_list[i-3:i+1]
            # Rule 4_1s
            if all(v > mean + std for v in last_4) or all(v < mean - std for v in last_4):
                results[i] = "Reject (4_1s)"; continue
                
        if i >= 9:
            last_10 = data_list[i-9:i+1] 
            # Rule 10_x
            if all(v > mean for v in last_10) or all(v < mean for v in last_10):
                results[i] = "Reject (10_x)"; continue
                
        # Rule 1_2s (Warning)
        if val > mean + 2*std or val < mean - 2*std:
            results[i] = "Warning (1_2s)"; continue
            
    return results


# 2. Official ARoHaN Lab Branding Header
col_logo, col_info = st.columns([1, 5])
# Path to logo
logo_path = "AroHaN_Lab.png"

with col_logo:
  # Load the ARoHaN Lab PNG Logo
  try:
      st.image(logo_path, width=110)
  except Exception:
      st.error(f"Logo file `{logo_path}` not found in the directory.")

with col_info:
  st.markdown(
      """
    <div class="arohan-header">
        <div class="arohan-title">🔬 ARoHaN Lab - Statistical Process Control (SPC) Platform</div>
        <div class="arohan-subtitle">
            <b>Department of Pharmaceutical Sciences & Technology</b> | Birla Institute of Technology (BIT) Mesra, Ranchi<br/>
            <b>Principal Investigator (PI):</b> Dr. Manik Ghosh | Quality Assurance & QC Computational Diagnostics
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# 3. Key Takeaways Box
st.markdown(
    """
<div class="key-takeaway-box">
    <h4 style="margin-top:0; color:#003366;">💡 Key Takeaways & Core Capabilities</h4>
    <ul style="margin-bottom:0; padding-left:20px;">
        <li><b>Automated Westgard Evaluation:</b> Built-in detection for rules <i>1₃ₛ, 2₂ₛ, R₄ₛ, 4₁ₛ, 10ₓ</i> to identify systematic and random errors in clinical/pharma assays.</li>
        <li><b>Crosshair Interactive Tracking:</b> Synchronized vertical alignment line across subplots to evaluate individual batch values directly against control limits (UCL, LCL, Target).</li>
        <li><b>Publication-Ready Downloads:</b> High-resolution image exports (300+ DPI SVG/PNG) and standalone interactive HTML files for QC report submissions.</li>
        <li><b>Tailored Pharmaceutical Metrics:</b> Comprehensive coverage of continuous parameters (weight, concentration, dissolution) and discrete defect counts (p, np, c, u charts).</li>
    </ul>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar: File Data Upload
st.sidebar.header("📁 Data Ingestion")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel file (.xlsx, .xls)", type=["xlsx", "xls"]
)


@st.cache_data
def load_excel(file):
  xls = pd.ExcelFile(file)
  return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}


if uploaded_file is not None:
  try:
    sheets = load_excel(uploaded_file)
    selected_sheet = st.sidebar.selectbox("Select Excel Sheet", list(sheets.keys()))
    df = sheets[selected_sheet]

    st.subheader(f"Data Preview: Sheet `{selected_sheet}`")
    st.dataframe(df.head(6), use_container_width=True)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    # Main Control Tabs
    tab_overview, tab_variables, tab_attributes, tab_advanced = st.tabs([
        "🔍 Data Profile & Intelligence",
        "📈 Variables Control Charts (Continuous)",
        "📋 Attributes Control Charts (Discrete)",
        "🔬 Specialized & Advanced (Westgard / Hotelling)",
    ])

    # --- TAB 1: OVERVIEW ---
    with tab_overview:
      st.markdown("### Dataset Summary & Auto-Classification")
      c1, c2, c3 = st.columns(3)
      c1.metric("Total Records", df.shape[0])
      c2.metric("Total Variables", df.shape[1])
      c3.metric("Numeric Features", len(numeric_cols))

      st.markdown("#### Descriptive Statistics")
      st.dataframe(df.describe(), use_container_width=True)

    # --- TAB 2: VARIABLES CHARTS ---
    with tab_variables:
      st.markdown("## Variables Control Charts (Continuous Measurement)")
      var_chart = st.selectbox(
          "Select Variable Chart Type",
          [
              "I-MR (Individuals & Moving Range)",
              "CUSUM (Cumulative Sum)",
              "EWMA (Exponentially Weighted Moving Average)",
              "X-bar and R (Mean & Range)",
              "X-bar and S (Mean & Standard Deviation)",
          ],
      )

      if numeric_cols:
        val_col = st.selectbox("Select Continuous Variable Column", numeric_cols, key="var_col")
        data = df[val_col].dropna().values

        if var_chart == "I-MR (Individuals & Moving Range)":
          mr = np.abs(np.diff(data))
          mr = np.insert(mr, 0, np.nan)  # align length
          x_bar = np.nanmean(data)
          mr_bar = np.nanmean(mr)

          ucl_x = x_bar + 2.66 * mr_bar
          lcl_x = x_bar - 2.66 * mr_bar
          ucl_mr = 3.267 * mr_bar
          lcl_mr = 0

          fig = make_subplots(
              rows=2,
              cols=1,
              shared_xaxes=True,
              subplot_titles=("Individuals Chart (X)", "Moving Range (MR)"),
          )
          fig.add_trace(
              go.Scatter(
                  y=data,
                  mode="lines+markers",
                  name="Value",
                  line=dict(color="#0056B3"),
              ),
              row=1,
              col=1,
          )
          fig.add_hline(
              y=x_bar,
              line=dict(color="green"),
              annotation_text=f"Mean: {x_bar:.2f}",
              row=1,
              col=1,
          )
          fig.add_hline(
              y=ucl_x,
              line=dict(color="red", dash="dash"),
              annotation_text=f"UCL: {ucl_x:.2f}",
              row=1,
              col=1,
          )
          fig.add_hline(
              y=lcl_x,
              line=dict(color="red", dash="dash"),
              annotation_text=f"LCL: {lcl_x:.2f}",
              row=1,
              col=1,
          )

          fig.add_trace(
              go.Scatter(
                  y=mr,
                  mode="lines+markers",
                  name="Moving Range",
                  line=dict(color="#8E44AD"),
              ),
              row=2,
              col=1,
          )
          fig.add_hline(
              y=mr_bar,
              line=dict(color="green"),
              annotation_text=f"MR Mean: {mr_bar:.2f}",
              row=2,
              col=1,
          )
          fig.add_hline(
              y=ucl_mr,
              line=dict(color="red", dash="dash"),
              annotation_text=f"UCL: {ucl_mr:.2f}",
              row=2,
              col=1,
          )

          apply_crosshair_layout(fig, height=600, title="I-MR Control Chart")
          st.plotly_chart(fig, use_container_width=True)
          add_download_options(fig, "IMR_Control_Chart")

        elif var_chart == "CUSUM (Cumulative Sum)":
          target = st.number_input("Target Mean (μ₀)", value=float(np.mean(data)))
          sigma = st.number_input("Sigma (σ)", value=float(np.std(data, ddof=1)))
          k = st.slider("Allowance Factor (k)", 0.1, 1.0, 0.5)
          h = st.slider("Decision Limit (h)", 1.0, 10.0, 5.0)

          std_data = (data - target) / sigma
          cp, cn = np.zeros(len(data)), np.zeros(len(data))
          for i in range(1, len(data)):
            cp[i] = max(0, cp[i - 1] + std_data[i] - k)
            cn[i] = max(0, cn[i - 1] - std_data[i] - k)

          fig = go.Figure()
          fig.add_trace(
              go.Scatter(y=cp, mode="lines+markers", name="CUSUM+", line=dict(color="blue"))
          )
          fig.add_trace(
              go.Scatter(y=-cn, mode="lines+markers", name="CUSUM-", line=dict(color="orange"))
          )
          fig.add_hline(y=h, line=dict(color="red", dash="dash"), annotation_text="+h Threshold")
          fig.add_hline(y=-h, line=dict(color="red", dash="dash"), annotation_text="-h Threshold")
          apply_crosshair_layout(fig, height=450, title="CUSUM Control Chart")
          st.plotly_chart(fig, use_container_width=True)
          add_download_options(fig, "CUSUM_Chart")

        elif var_chart == "EWMA (Exponentially Weighted Moving Average)":
          lam = st.slider("Weighting Factor (λ)", 0.05, 1.0, 0.2)
          mu0 = np.mean(data)
          s0 = np.std(data, ddof=1)
          ewma = np.zeros(len(data))
          ewma[0] = mu0
          for i in range(1, len(data)):
            ewma[i] = lam * data[i] + (1 - lam) * ewma[i - 1]

          i_seq = np.arange(1, len(data) + 1)
          ucl = mu0 + 3 * s0 * np.sqrt((lam / (2 - lam)) * (1 - (1 - lam) ** (2 * i_seq)))
          lcl = mu0 - 3 * s0 * np.sqrt((lam / (2 - lam)) * (1 - (1 - lam) ** (2 * i_seq)))

          fig = go.Figure()
          fig.add_trace(
              go.Scatter(y=ewma, mode="lines+markers", name="EWMA", line=dict(color="teal"))
          )
          fig.add_trace(
              go.Scatter(
                  y=ucl,
                  mode="lines",
                  name="UCL",
                  line=dict(color="red", dash="dash"),
              )
          )
          fig.add_trace(
              go.Scatter(
                  y=lcl,
                  mode="lines",
                  name="LCL",
                  line=dict(color="red", dash="dash"),
              )
          )
          fig.add_hline(y=mu0, line=dict(color="green"), annotation_text="Target")
          apply_crosshair_layout(fig, height=450, title="EWMA Control Chart")
          st.plotly_chart(fig, use_container_width=True)
          add_download_options(fig, "EWMA_Chart")

        elif var_chart in ["X-bar and R (Mean & Range)", "X-bar and S (Mean & Standard Deviation)"]:
          subgroup_size = st.number_input("Subgroup Size (n)", min_value=2, max_value=25, value=5)
          num_subgroups = len(data) // subgroup_size
          if num_subgroups < 2:
            st.error("Not enough data points for the specified subgroup size.")
          else:
            reshaped = data[: num_subgroups * subgroup_size].reshape(
                num_subgroups, subgroup_size
            )
            means = np.mean(reshaped, axis=1)
            x_double_bar = np.mean(means)

            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                subplot_titles=(
                    "Subgroup Means (X-bar)",
                    "Subgroup Dispersion",
                ),
            )
            fig.add_trace(
                go.Scatter(
                    y=means,
                    mode="lines+markers",
                    name="Subgroup Mean",
                    line=dict(color="#0056B3"),
                ),
                row=1,
                col=1,
            )
            fig.add_hline(y=x_double_bar, line=dict(color="green"), row=1, col=1)

            if "Range" in var_chart:
              ranges = np.ptp(reshaped, axis=1)
              r_bar = np.mean(ranges)
              fig.add_trace(
                  go.Scatter(
                      y=ranges,
                      mode="lines+markers",
                      name="Range (R)",
                      line=dict(color="chocolate"),
                  ),
                  row=2,
                  col=1,
              )
              fig.add_hline(
                  y=r_bar,
                  line=dict(color="green"),
                  annotation_text=f"R-bar: {r_bar:.2f}",
                  row=2,
                  col=1,
              )
            else:
              stdevs = np.std(reshaped, axis=1, ddof=1)
              s_bar = np.mean(stdevs)
              fig.add_trace(
                  go.Scatter(
                      y=stdevs,
                      mode="lines+markers",
                      name="Std Dev (S)",
                      line=dict(color="darkcyan"),
                  ),
                  row=2,
                  col=1,
              )
              fig.add_hline(
                  y=s_bar,
                  line=dict(color="green"),
                  annotation_text=f"S-bar: {s_bar:.2f}",
                  row=2,
                  col=1,
              )

            apply_crosshair_layout(fig, height=600, title=var_chart)
            st.plotly_chart(fig, use_container_width=True)
            add_download_options(fig, "Xbar_Chart")

    # --- TAB 3: ATTRIBUTES CHARTS (Discrete Data) ---
    with tab_attributes:
      st.markdown("## Attributes Control Charts (Discrete Data)")
      st.markdown(
          "Monitor counts of defectives, non-conforming items, or specific"
          " defects per inspection unit."
      )

      attr_chart = st.selectbox(
          "Select Attribute Control Chart",
          [
              "p Chart (Proportion Non-Conforming)",
              "np Chart (Number Non-Conforming)",
              "c Chart (Count of Defects per Unit)",
              "u Chart (Defects Per Unit)",
          ],
      )

      col_defect = st.selectbox(
          "Select Defect / Non-Conforming Count Column",
          numeric_cols,
          key="attr_defect_col",
      )
      defects = df[col_defect].dropna().values

      # Helper for Sample Size selection
      use_subgroup_col = st.checkbox(
          "Use a Column for Varying Subgroup / Inspection Unit Sizes",
          value=False,
      )

      if use_subgroup_col:
        col_size = st.selectbox(
            "Select Subgroup / Inspection Size Column",
            [c for c in numeric_cols if c != col_defect],
            key="attr_size_col",
        )
        n_sizes = df[col_size].dropna().values
      else:
        fixed_n = st.number_input(
            "Enter Constant Subgroup / Unit Size (n)",
            min_value=1,
            value=100,
            step=1,
        )
        n_sizes = np.full(len(defects), fixed_n)

      # Ensure aligned lengths
      min_len = min(len(defects), len(n_sizes))
      defects = defects[:min_len]
      n_sizes = n_sizes[:min_len]

      # Chart Implementations
      if attr_chart == "p Chart (Proportion Non-Conforming)":
        p_i = defects / n_sizes
        p_bar = np.sum(defects) / np.sum(n_sizes)

        ucl_p = p_bar + 3 * np.sqrt((p_bar * (1 - p_bar)) / n_sizes)
        lcl_p = np.maximum(0, p_bar - 3 * np.sqrt((p_bar * (1 - p_bar)) / n_sizes))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=p_i,
                mode="lines+markers",
                name="Proportion (p)",
                line=dict(color="#1F77B4"),
            )
        )
        fig.add_trace(
            go.Scatter(
                y=ucl_p,
                mode="lines",
                name="UCL",
                line=dict(color="red", dash="dash"),
            )
        )
        fig.add_trace(
            go.Scatter(
                y=lcl_p,
                mode="lines",
                name="LCL",
                line=dict(color="red", dash="dash"),
            )
        )
        fig.add_hline(
            y=p_bar,
            line=dict(color="green", dash="solid"),
            annotation_text=f"p-bar: {p_bar:.4f}",
        )
        apply_crosshair_layout(
            fig, height=450, title="p Control Chart (Proportion Non-Conforming)"
        )
        st.plotly_chart(fig, use_container_width=True)
        add_download_options(fig, "p_Chart")

      elif attr_chart == "np Chart (Number Non-Conforming)":
        if len(set(n_sizes)) > 1:
          st.warning(
              "⚠️ np-Chart assumes constant sample size. Average sample size"
              " will be used for control limit baseline."
          )
        n_const = np.mean(n_sizes)
        p_bar = np.sum(defects) / (len(defects) * n_const)
        np_bar = n_const * p_bar

        ucl_np = np_bar + 3 * np.sqrt(np_bar * (1 - p_bar))
        lcl_np = max(0, np_bar - 3 * np.sqrt(np_bar * (1 - p_bar)))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=defects,
                mode="lines+markers",
                name="Defective Count (np)",
                line=dict(color="#2CA02C"),
            )
        )
        fig.add_hline(
            y=np_bar,
            line=dict(color="green", dash="solid"),
            annotation_text=f"np-bar: {np_bar:.2f}",
        )
        fig.add_hline(
            y=ucl_np,
            line=dict(color="red", dash="dash"),
            annotation_text=f"UCL: {ucl_np:.2f}",
        )
        fig.add_hline(
            y=lcl_np,
            line=dict(color="red", dash="dash"),
            annotation_text=f"LCL: {lcl_np:.2f}",
        )
        apply_crosshair_layout(
            fig, height=450, title="np Control Chart (Number Non-Conforming)"
        )
        st.plotly_chart(fig, use_container_width=True)
        add_download_options(fig, "np_Chart")

      elif attr_chart == "c Chart (Count of Defects per Unit)":
        c_bar = np.mean(defects)
        ucl_c = c_bar + 3 * np.sqrt(c_bar)
        lcl_c = max(0, c_bar - 3 * np.sqrt(c_bar))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=defects,
                mode="lines+markers",
                name="Defects Count (c)",
                line=dict(color="#FF7F0E"),
            )
        )
        fig.add_hline(
            y=c_bar,
            line=dict(color="green", dash="solid"),
            annotation_text=f"c-bar: {c_bar:.2f}",
        )
        fig.add_hline(
            y=ucl_c,
            line=dict(color="red", dash="dash"),
            annotation_text=f"UCL: {ucl_c:.2f}",
        )
        fig.add_hline(
            y=lcl_c,
            line=dict(color="red", dash="dash"),
            annotation_text=f"LCL: {lcl_c:.2f}",
        )
        apply_crosshair_layout(
            fig, height=450, title="c Control Chart (Total Defects)"
        )
        st.plotly_chart(fig, use_container_width=True)
        add_download_options(fig, "c_Chart")

      elif attr_chart == "u Chart (Defects Per Unit)":
        u_i = defects / n_sizes
        u_bar = np.sum(defects) / np.sum(n_sizes)

        ucl_u = u_bar + 3 * np.sqrt(u_bar / n_sizes)
        lcl_u = np.maximum(0, u_bar - 3 * np.sqrt(u_bar / n_sizes))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=u_i,
                mode="lines+markers",
                name="Defects/Unit (u)",
                line=dict(color="#D62728"),
            )
        )
        fig.add_trace(
            go.Scatter(
                y=ucl_u,
                mode="lines",
                name="UCL",
                line=dict(color="red", dash="dash"),
            )
        )
        fig.add_trace(
            go.Scatter(
                y=lcl_u,
                mode="lines",
                name="LCL",
                line=dict(color="red", dash="dash"),
            )
        )
        fig.add_hline(
            y=u_bar,
            line=dict(color="green", dash="solid"),
            annotation_text=f"u-bar: {u_bar:.4f}",
        )
        apply_crosshair_layout(
            fig, height=450, title="u Control Chart (Defects per Unit)"
        )
        st.plotly_chart(fig, use_container_width=True)
        add_download_options(fig, "u_Chart")

    # --- TAB 4: ADVANCED CHARTS & WESTGARD ---
    with tab_advanced:
      st.markdown(
          "## Specialized & Advanced Control Charts (Pharma QC Diagnostics)"
      )
      adv_chart = st.selectbox(
          "Select Advanced Quality Chart",
          [
              "Levey-Jennings Chart (with Westgard Rule Checks)",
              "Hotelling's T² Chart (Multivariate Process Control)",
          ],
      )

      if adv_chart == "Levey-Jennings Chart (with Westgard Rule Checks)":
        if numeric_cols:
          lj_col = st.selectbox("Select Assay Metric Column", numeric_cols, key="lj_col")
          lj_data = df[lj_col].dropna().values

          mean_lj = np.mean(lj_data)
          s_lj = np.std(lj_data, ddof=1)

          # Get Westgard violations evaluation using the updated function
          westgard_decisions = evaluate_westgard_rules(lj_data, mean_lj, s_lj)

          fig = go.Figure()
          
          # Plot the underlying process trend line
          fig.add_trace(
              go.Scatter(
                  y=lj_data,
                  mode="lines",
                  name="Assay Value (Trend)",
                  line=dict(color="lightgray", width=2),
              )
          )

          # Color mappings specifically for each rule detection 
          color_map = {
              "Accept": "green", "Warning (1_2s)": "orange", "Reject (1_3s)": "red",
              "Reject (2_2s)": "darkred", "Reject (R_4s)": "purple", 
              "Reject (4_1s)": "magenta", "Reject (10_x)": "brown"
          }

          df_lj = pd.DataFrame({'Run Number': range(len(lj_data)), 'Value': lj_data, 'Decision': westgard_decisions})
          
          # Plot scatter markers over the trend line matching the corresponding violation colors
          for decision, color in color_map.items():
              subset = df_lj[df_lj['Decision'] == decision]
              if not subset.empty:
                  fig.add_trace(
                      go.Scatter(
                          x=subset['Run Number'], 
                          y=subset['Value'], 
                          mode='markers', 
                          name=decision, 
                          marker=dict(color=color, size=10, line=dict(color='black', width=1))
                      )
                  )

          # Standard deviations lines
          for mult, clr, style in [
              (1, "gold", "dot"),
              (2, "orange", "dash"),
              (3, "red", "dash"),
          ]:
            fig.add_hline(
                y=mean_lj + mult * s_lj,
                line=dict(color=clr, dash=style),
                annotation_text=f"+{mult}SD",
            )
            fig.add_hline(
                y=mean_lj - mult * s_lj,
                line=dict(color=clr, dash=style),
                annotation_text=f"-{mult}SD",
            )

          fig.add_hline(
              y=mean_lj,
              line=dict(color="green", dash="solid"),
              annotation_text=f"Target Mean ({mean_lj:.2f})",
          )

          apply_crosshair_layout(
              fig, height=550, title="Levey-Jennings QC Chart with Westgard Rules"
          )
          st.plotly_chart(fig, use_container_width=True)
          add_download_options(fig, "Levey_Jennings_Chart")

          rejections = [d for d in westgard_decisions if "Reject" in d]
          if rejections:
            st.error(f"🚨 Detected {len(rejections)} Westgard Rule Out-of-Control points! Check the chart legend for specific rejection types.")
          else:
            st.success("✔ Assay within valid control limits across all runs.")

      elif adv_chart == "Hotelling's T² Chart (Multivariate Process Control)":
        if len(numeric_cols) >= 2:
          m_cols = st.multiselect(
              "Select 2 or more Correlated Process Metrics",
              numeric_cols,
              default=numeric_cols[:2],
          )
          if len(m_cols) >= 2:
            m_data = df[m_cols].dropna().values
            mean_vec = np.mean(m_data, axis=0)
            cov_matrix = np.cov(m_data, rowvar=False)
            inv_cov = np.linalg.pinv(cov_matrix)

            t2_vals = [
                np.dot(np.dot((row - mean_vec).T, inv_cov), (row - mean_vec))
                for row in m_data
            ]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=t2_vals,
                    mode="lines+markers",
                    name="T² Statistic",
                    line=dict(color="#8C564B"),
                )
            )
            apply_crosshair_layout(
                fig, height=450, title="Hotelling's T² Multivariate SPC Chart"
            )
            st.plotly_chart(fig, use_container_width=True)
            add_download_options(fig, "Hotellings_T2_Chart")
          else:
            st.warning("Please select at least 2 metrics.")

  except Exception as e:
    st.error(f"Error processing upload: {e}")
else:
  st.info("👈 Please upload an Excel sheet from the sidebar to initialize the dashboard.")
