import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Versatile Statistical Process Control (SPC) Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title(
    "📊 Versatile SPC Control Chart Dashboard (Continuous, Attributes & Advanced)"
)
st.markdown(
    """
Upload your Excel file below. The application automatically detects data characteristics 
(continuous measurements, attribute counts, sample subgroups, or multivariate metrics) 
and populates the appropriate control chart tabs.
"""
)

# Sidebar: File Upload & Configuration
st.sidebar.header("📁 Data Ingestion")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel file (.xlsx, .xls)", type=["xlsx", "xls"]
)


@st.cache_data
def load_excel_data(file):
  xls = pd.ExcelFile(file)
  sheet_names = xls.sheet_names
  sheets_dict = {
      sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in sheet_names
  }
  return sheets_dict


if uploaded_file is not None:
  try:
    sheets_data = load_excel_data(uploaded_file)
    sheet_name = st.sidebar.selectbox(
        "Select Excel Sheet", list(sheets_data.keys())
    )
    df = sheets_data[sheet_name]

    st.subheader(f"Preview of Sheet: `{sheet_name}`")
    st.dataframe(df.head(10), use_container_width=True)

    # Column Selection
    numeric_cols = df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    # Tabs Setup
    tab_overview, tab_variables, tab_attributes, tab_advanced = st.tabs([
        "🔍 Data Profile & Auto-Detection",
        "📈 Variables Charts (Continuous)",
        "📋 Attributes Charts (Discrete)",
        "🔬 Specialized & Advanced",
    ])

    with tab_overview:
      st.markdown("### Dataset Summary & Statistical Profiling")
      col1, col2, col3 = st.columns(3)
      col1.metric("Total Rows", df.shape[0])
      col2.metric("Total Columns", df.shape[1])
      col3.metric("Numeric Features", len(numeric_cols))

      st.markdown("#### Column Statistics")
      st.dataframe(df.describe(), use_container_width=True)

      # Auto-detection logic recommendation
      st.markdown("### 🤖 SPC Chart Recommendation Engine")
      if len(numeric_cols) >= 2:
        st.success(
            "✔ Multi-column numeric data detected: Suitable for **Multivariate"
            " Hotelling's T²**, **X-bar/R**, or **X-bar/S** charts."
        )
      elif len(numeric_cols) == 1:
        st.success(
            "✔ Single-column numeric data detected: Suitable for **I-MR**,"
            " **CUSUM**, **EWMA**, or **Levey-Jennings** charts."
        )
      else:
        st.warning(
            "⚠️ Please ensure your dataset contains numeric columns for SPC"
            " analysis."
        )

    with tab_variables:
      st.markdown(
          "## Variables Control Charts (Continuous Data)"
      )
      st.markdown(
          "Monitor continuous physical properties (concentration, weight,"
          " temperature, dimension)."
      )

      var_chart_type = st.selectbox(
          "Select Variable Control Chart",
          [
              "I-MR (Individuals & Moving Range)",
              "CUSUM (Cumulative Sum)",
              "EWMA (Exponentially Weighted Moving Average)",
              "X-bar and R (Mean & Range)",
              "X-bar and S (Mean & Std Dev)",
          ],
      )

      if numeric_cols:
        selected_col = st.selectbox(
            "Select Measurement Column", numeric_cols, key="var_col"
        )
        data = df[selected_col].dropna().values

        if var_chart_type == "I-MR (Individuals & Moving Range)":
          st.markdown(
              "#### Individuals & Moving Range Chart"
          )
          mr = np.abs(np.diff(data))
          x_bar = np.mean(data)
          mr_bar = np.mean(mr)
          # Constants for n=2
          d2 = 1.128
          D3 = 0
          D4 = 3.267

          ucl_x = x_bar + 2.66 * mr_bar
          lcl_x = x_bar - 2.66 * mr_bar
          ucl_mr = D4 * mr_bar
          lcl_mr = D3 * mr_bar

          fig = make_subplots(
              rows=2,
              cols=1,
              subplot_titles=("Individuals Chart (X)", "Moving Range (MR)"),
          )
          # X Plot
          fig.add_trace(
              go.Scatter(
                  y=data,
                  mode="lines+markers",
                  name="Individual",
                  line=dict(color="blue"),
              ),
              row=1,
              col=1,
          )
          fig.add_hline(
              y=x_bar,
              line=dict(color="green", dash="solid"),
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

          # MR Plot
          fig.add_trace(
              go.Scatter(
                  y=mr,
                  mode="lines+markers",
                  name="Moving Range",
                  line=dict(color="purple"),
              ),
              row=2,
              col=1,
          )
          fig.add_hline(
              y=mr_bar,
              line=dict(color="green", dash="solid"),
              annotation_text=f"Mean MR: {mr_bar:.2f}",
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

          fig.update_layout(height=600, showlegend=False)
          st.plotly_chart(fig, use_container_width=True)

        elif var_chart_type == "CUSUM (Cumulative Sum)":
          st.markdown("#### Cumulative Sum (CUSUM) Chart")
          target = st.number_input(
              "Target Mean ($\mu_0$)", value=float(np.mean(data))
          )
          sigma = st.number_input(
              "Process Standard Deviation ($\sigma$)",
              value=float(np.std(data, ddof=1)),
          )
          k = st.slider(
              "Allowance (k) in terms of sigma", 0.25, 1.0, 0.5, 0.05
          )
          h = st.slider("Decision Interval (h)", 1.0, 10.0, 5.0, 0.5)

          standardized = (data - target) / sigma
          cusum_pos = np.zeros(len(data))
          cusum_neg = np.zeros(len(data))

          for i in range(1, len(data)):
            cusum_pos[i] = max(
                0, cusum_pos[i - 1] + standardized[i] - k
            )
            cusum_neg[i] = max(
                0, cusum_neg[i - 1] - standardized[i] - k
            )

          fig = go.Figure()
          fig.add_trace(
              go.Scatter(
                  y=cusum_pos,
                  mode="lines+markers",
                  name="CUSUM+",
                  line=dict(color="blue"),
              )
          )
          fig.add_trace(
              go.Scatter(
                  y=-cusum_neg,
                  mode="lines+markers",
                  name="CUSUM-",
                  line=dict(color="orange"),
              )
          )
          fig.add_hline(
              y=h, line=dict(color="red", dash="dash"), annotation_text="+h Limit"
          )
          fig.add_hline(
              y=-h, line=dict(color="red", dash="dash"), annotation_text="-h Limit"
          )
          fig.update_layout(
              title="CUSUM Chart for Small Shift Detection",
              yaxis_title="Cumulative Deviation",
              height=400,
          )
          st.plotly_chart(fig, use_container_width=True)

        elif var_chart_type == "EWMA (Exponentially Weighted Moving Average)":
          st.markdown(
              "#### Exponentially Weighted Moving Average (EWMA) Chart"
          )
          lam = st.slider("Weighting factor ($\lambda$)", 0.05, 1.0, 0.2, 0.05)
          mu0 = np.mean(data)
          sigma0 = np.std(data, ddof=1)

          ewma = np.zeros(len(data))
          ewma[0] = mu0
          for i in range(1, len(data)):
            ewma[i] = lam * data[i] + (1 - lam) * ewma[i - 1]

          # Control limits for EWMA
          L = 3
          sigma_ewma = (
              sigma0
              * np.sqrt(
                  (lam / (2 - lam))
                  * (1 - (1 - lam) ** (2 * np.arange(1, len(data) + 1)))
              )
          )
          ucl = mu0 + L * sigma_ewma
          lcl = mu0 - L * sigma_ewma

          fig = go.Figure()
          fig.add_trace(
              go.Scatter(
                  y=ewma,
                  mode="lines+markers",
                  name="EWMA",
                  line=dict(color="teal"),
              )
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
          fig.add_hline(
              y=mu0,
              line=dict(color="green", dash="solid"),
              annotation_text=f"Target: {mu0:.2f}",
          )
          fig.update_layout(
              title="EWMA Chart for Subtle Process Drift",
              yaxis_title="EWMA Value",
              height=400,
          )
          st.plotly_chart(fig, use_container_width=True)

        else:
          st.info(
              f"Configuration for **{var_chart_type}** is ready. Group"
              " subgroup size and calculate subgroup means/ranges/stdevs"
              " accordingly."
          )

    with tab_attributes:
      st.markdown(
          "## Attributes Control Charts (Discrete Data)"
      )
      st.markdown(
          "Track pass/fail counts, defect tallies, and non-conforming items."
      )

      attr_chart_type = st.selectbox(
          "Select Attribute Control Chart",
          [
              "p Chart (Proportion Non-Conforming)",
              "np Chart (Number Non-Conforming)",
              "c Chart (Count of Defects per Unit)",
              "u Chart (Defects Per Unit)",
          ],
      )

      col_defect = st.selectbox(
          "Select Defect / Count Column", numeric_cols, key="attr_col"
      )
      defects = df[col_defect].dropna().values

      if attr_chart_type == "c Chart (Count of Defects per Unit)":
        st.markdown(
            "#### c Chart: Total Defect Instances per Fixed Unit"
        )
        c_bar = np.mean(defects)
        ucl_c = c_bar + 3 * np.sqrt(c_bar)
        lcl_c = max(0, c_bar - 3 * np.sqrt(c_bar))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                y=defects,
                mode="lines+markers",
                name="Defect Count",
                line=dict(color="darkorange"),
            )
        )
        fig.add_hline(
            y=c_bar,
            line=dict(color="green", dash="solid"),
            annotation_text=f"Center Line (c̄): {c_bar:.2f}",
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
        fig.update_layout(
            title="c Control Chart",
            yaxis_title="Defect Count",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
      else:
        st.info(
            f"Selected **{attr_chart_type}**. Provide sample sizes and counts"
            " to compute control limits."
        )

    with tab_advanced:
      st.markdown(
          "## Specialized & Advanced Control Charts"
      )
      adv_chart_type = st.selectbox(
          "Select Advanced Chart",
          [
              "Levey-Jennings Chart (Clinical Lab QC)",
              "Hotelling's T² Chart (Multivariate)",
          ],
      )

      if adv_chart_type == "Levey-Jennings Chart (Clinical Lab QC)":
        st.markdown(
            "#### Levey-Jennings Chart with ±1SD, ±2SD, ±3SD Limits"
        )
        if numeric_cols:
          lj_col = st.selectbox("Select Assay Metric", numeric_cols, key="lj_col")
          lj_data = df[lj_col].dropna().values
          mean_lj = np.mean(lj_data)
          std_lj = np.std(lj_data, ddof=1)

          fig = go.Figure()
          fig.add_trace(
              go.Scatter(
                  y=lj_data,
                  mode="lines+markers",
                  name="Assay Value",
                  line=dict(color="royalblue"),
              )
          )
          fig.add_hline(
              y=mean_lj,
              line=dict(color="green", dash="solid"),
              annotation_text="Mean",
          )
          fig.add_hline(
              y=mean_lj + std_lj,
              line=dict(color="orange", dash="dot"),
              annotation_text="+1SD",
          )
          fig.add_hline(
              y=mean_lj - std_lj,
              line=dict(color="orange", dash="dot"),
              annotation_text="-1SD",
          )
          fig.add_hline(
              y=mean_lj + 2 * std_lj,
              line=dict(color="darkorange", dash="dash"),
              annotation_text="+2SD",
          )
          fig.add_hline(
              y=mean_lj - 2 * std_lj,
              line=dict(color="darkorange", dash="dash"),
              annotation_text="-2SD",
          )
          fig.add_hline(
              y=mean_lj + 3 * std_lj,
              line=dict(color="red", dash="dash"),
              annotation_text="+3SD (UCL)",
          )
          fig.add_hline(
              y=mean_lj - 3 * std_lj,
              line=dict(color="red", dash="dash"),
              annotation_text="-3SD (LCL)",
          )
          fig.update_layout(
              title="Levey-Jennings QC Chart",
              yaxis_title="Assay Value",
              height=450,
          )
          st.plotly_chart(fig, use_container_width=True)

      elif adv_chart_type == "Hotelling's T² Chart (Multivariate)":
        st.markdown(
            "#### Hotelling's T² Multivariate Process Monitoring"
        )
        if len(numeric_cols) >= 2:
          m_cols = st.multiselect(
              "Select 2 or more correlated variables",
              numeric_cols,
              default=numeric_cols[:2],
          )
          if len(m_cols) >= 2:
            m_data = df[m_cols].dropna().values
            # Simplified T-square calculation placeholder
            mean_vec = np.mean(m_data, axis=0)
            cov_matrix = np.cov(m_data, rowvar=False)
            inv_cov = np.linalg.pinv(cov_matrix)

            t2_vals = []
            for row in m_data:
              diff = row - mean_vec
              t2 = np.dot(np.dot(diff.T, inv_cov), diff)
              t2_vals.append(t2)

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    y=t2_vals,
                    mode="lines+markers",
                    name="Hotelling's T²",
                    line=dict(color="crimson"),
                )
            )
            # Approximate UCL threshold for T2
            fig.update_layout(
                title="Hotelling's T² Multivariate Control Chart",
                yaxis_title="T² Statistic",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)
          else:
            st.warning("Please select at least 2 variables for multivariate analysis.")
        else:
          st.warning("Dataset requires at least 2 numeric columns.")

  except Exception as e:
    st.error(f"Error reading Excel file: {e}")
else:
  st.info(
      "👈 Please upload an Excel file from the sidebar to activate the SPC"
      " Control Charts."
  )