# ======================================================
# APPAREL PRODUCTION PLANNING & EFFICIENCY ANALYTICS
# LESSON 9 - DATA CLEANING AND VALIDATION
# ======================================================
import streamlit as st
import pandas as pd
from io import BytesIO

# ======================================================
# 1. PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="Apparel Production Analytics",
    page_icon="ðŸ‘•",
    layout="wide"
)

# ======================================================
# 2. REQUIRED DATASET COLUMNS
# ======================================================
REQUIRED_COLUMNS = [
    "Date",
    "Production_Line",
    "Style",
    "Target_Qty",
    "Actual_Qty",
    "SMV",
    "Shift_Minutes",
    "Downtime_Minutes",
    "Defects_Qty",
    "Operators_Count"
]

# ======================================================
# 3. COLUMN TYPES
# ======================================================
TEXT_COLUMNS = [
    "Production_Line",
    "Style"
]

NUMERIC_COLUMNS = [
    "Target_Qty",
    "Actual_Qty",
    "SMV",
    "Shift_Minutes",
    "Downtime_Minutes",
    "Defects_Qty",
    "Operators_Count"
]

INTEGER_COLUMNS = [
    "Target_Qty",
    "Actual_Qty",
    "Shift_Minutes",
    "Downtime_Minutes",
    "Defects_Qty",
    "Operators_Count"
]

# ======================================================
# 4. DATA CLEANING AND VALIDATION FUNCTION
# ======================================================
def clean_and_validate_data(raw_df):
    """Clean production data and separate valid and rejected rows.
    The original DataFrame is not modified. Exact duplicate rows are
    identified separately; they are not automatically removed.
    """
    # Create a copy of uploaded data.
    # Never modify the original uploaded DataFrame.
    cleaned_df = raw_df.copy().reset_index(drop=True)

    # Add the original CSV row number for tracking rejected rows.
    # Choose a unique column name in case the uploaded CSV already
    # contains Source_Row or a previously generated source-row column.
    source_row_column = "Source_Row"
    while source_row_column in cleaned_df.columns:
        source_row_column = f"Uploaded_{source_row_column}"

    cleaned_df.insert(
        0,
        source_row_column,
        range(2, len(cleaned_df) + 2)
    )

    # Store validation issues for each record.
    row_issues = [
        [] for _ in range(len(cleaned_df))
    ]

    # --------------------------------------------------
    # HELPER FUNCTION TO RECORD VALIDATION ISSUES
    # --------------------------------------------------
    def add_issue(mask, message):
        mask = pd.Series(mask).fillna(False).tolist()
        for row_index, is_invalid in enumerate(mask):
            if is_invalid:
                row_issues[row_index].append(message)

    # ==================================================
    # 4.1 CHECK TEXT COLUMNS
    # ==================================================
    for column in TEXT_COLUMNS:
        cleaned_values = (
            cleaned_df[column]
            .astype("string")
            .str.strip()
        )
        missing_mask = (
            cleaned_values.isna() |
            cleaned_values.eq("")
        )
        add_issue(
            missing_mask,
            f"{column} is missing or empty."
        )
        cleaned_df[column] = cleaned_values

    # ==================================================
    # 4.2 VALIDATE DATE COLUMN
    # ==================================================
    cleaned_df["Date"] = pd.to_datetime(
        cleaned_df["Date"],
        errors="coerce"
    )
    invalid_date_mask = cleaned_df["Date"].isna()
    add_issue(
        invalid_date_mask,
        "Date is missing or invalid."
    )

    # ==================================================
    # 4.3 CONVERT NUMERIC COLUMNS
    # ==================================================
    for column in NUMERIC_COLUMNS:
        numeric_values = pd.to_numeric(
            cleaned_df[column],
            errors="coerce"
        )
        invalid_numeric_mask = numeric_values.isna()
        add_issue(
            invalid_numeric_mask,
            f"{column} is missing or not numeric."
        )
        cleaned_df[column] = numeric_values

    # ==================================================
    # 4.4 CHECK WHOLE NUMBER FIELDS
    # ==================================================
    for column in INTEGER_COLUMNS:
        fractional_mask = (
            cleaned_df[column].notna() &
            (cleaned_df[column] % 1 != 0)
        )
        add_issue(
            fractional_mask,
            f"{column} must be a whole number."
        )

    # ==================================================
    # 4.5 BUSINESS RULE VALIDATION
    # ==================================================
    # Target quantity must be greater than zero.
    add_issue(
        cleaned_df["Target_Qty"].notna() &
        (cleaned_df["Target_Qty"] <= 0),
        "Target_Qty must be greater than zero."
    )

    # Actual production cannot be negative.
    add_issue(
        cleaned_df["Actual_Qty"].notna() &
        (cleaned_df["Actual_Qty"] < 0),
        "Actual_Qty cannot be negative."
    )

    # SMV must be greater than zero.
    add_issue(
        cleaned_df["SMV"].notna() &
        (cleaned_df["SMV"] <= 0),
        "SMV must be greater than zero."
    )

    # Shift minutes must be greater than zero.
    add_issue(
        cleaned_df["Shift_Minutes"].notna() &
        (cleaned_df["Shift_Minutes"] <= 0),
        "Shift_Minutes must be greater than zero."
    )

    # Downtime cannot be negative.
    add_issue(
        cleaned_df["Downtime_Minutes"].notna() &
        (cleaned_df["Downtime_Minutes"] < 0),
        "Downtime_Minutes cannot be negative."
    )

    # Downtime cannot exceed shift duration.
    downtime_exceeds_shift = (
        cleaned_df["Downtime_Minutes"].notna() &
        cleaned_df["Shift_Minutes"].notna() &
        (
            cleaned_df["Downtime_Minutes"] >
            cleaned_df["Shift_Minutes"]
        )
    )
    add_issue(
        downtime_exceeds_shift,
        "Downtime cannot exceed Shift_Minutes."
    )

    # Defects cannot be negative.
    add_issue(
        cleaned_df["Defects_Qty"].notna() &
        (cleaned_df["Defects_Qty"] < 0),
        "Defects_Qty cannot be negative."
    )

    # Defects cannot exceed actual production.
    defects_exceed_actual = (
        cleaned_df["Defects_Qty"].notna() &
        cleaned_df["Actual_Qty"].notna() &
        (
            cleaned_df["Defects_Qty"] >
            cleaned_df["Actual_Qty"]
        )
    )
    add_issue(
        defects_exceed_actual,
        "Defects_Qty cannot exceed Actual_Qty."
    )

    # Operators must be greater than zero.
    add_issue(
        cleaned_df["Operators_Count"].notna() &
        (cleaned_df["Operators_Count"] <= 0),
        "Operators_Count must be greater than zero."
    )

    # ==================================================
    # 4.6 IDENTIFY DUPLICATE RECORDS
    # ==================================================
    # Keep the first occurrence. Later exact matches are listed
    # in duplicate_df, but are not automatically deleted.
    duplicate_mask = cleaned_df.duplicated(
        subset=REQUIRED_COLUMNS,
        keep="first"
    )
    duplicate_df = cleaned_df.loc[
        duplicate_mask
    ].copy()

    # ==================================================
    # 4.7 SEPARATE VALID AND REJECTED RECORDS
    # ==================================================
    cleaned_df["Validation_Issues"] = [
        "; ".join(issues)
        for issues in row_issues
    ]

    valid_mask = [
        len(issues) == 0
        for issues in row_issues
    ]

    valid_df = cleaned_df.loc[
        valid_mask
    ].copy()
    rejected_df = cleaned_df.loc[
        [not is_valid for is_valid in valid_mask]
    ].copy()

    # Convert whole number columns to integer types.
    if not valid_df.empty:
        for column in INTEGER_COLUMNS:
            valid_df[column] = valid_df[column].astype("int64")

    return valid_df, rejected_df, duplicate_df

# ======================================================
# 5. APPLICATION HEADER
# ======================================================
st.title("ðŸ‘• Apparel Production Analytics Dashboard")
st.write(
    "Production Planning, Data Cleaning "
    "and Efficiency Analysis"
)
st.divider()

# ======================================================
# 6. SIDEBAR - CSV UPLOAD
# ======================================================
st.sidebar.header("Production Data Upload")
uploaded_file = st.sidebar.file_uploader(
    "Upload Production CSV File",
    type=["csv"],
    help="Upload your original or previously prepared production CSV."
)

# ======================================================
# 7. PROCESS UPLOADED DATA
# ======================================================
if uploaded_file is not None:
    # --------------------------------------------------
    # 7.1 READ THE CSV FILE
    # --------------------------------------------------
    try:
        uploaded_file.seek(0)
        raw_df = pd.read_csv(
            uploaded_file,
            encoding="utf-8-sig"
        )
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty.")
        st.stop()
    except pd.errors.ParserError:
        st.error("Unable to parse the uploaded CSV file.")
        st.stop()
    except UnicodeDecodeError:
        st.error("Please upload a UTF-8 encoded CSV file.")
        st.stop()
    except OSError as error:
        st.error(f"Unable to read the uploaded CSV file: {error}")
        st.stop()

    # ==================================================
    # 8. CHECK DATASET STRUCTURE
    # ==================================================
    # Remove accidental spaces around column names.
    raw_df.columns = (
        raw_df.columns.astype(str).str.strip()
    )

    if raw_df.empty:
        st.warning("The CSV contains no production records.")
        st.stop()

    # Check duplicate column names.
    if raw_df.columns.duplicated().any():
        duplicate_columns = raw_df.columns[
            raw_df.columns.duplicated()
        ].tolist()
        st.error(
            f"Duplicate column names detected: {duplicate_columns}"
        )
        st.stop()

    # Check required columns.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in raw_df.columns
    ]
    if missing_columns:
        st.error(
            "The uploaded dataset is missing required columns."
        )
        st.write("Missing columns:")
        st.write(missing_columns)
        st.stop()

    # ==================================================
    # 9. EXECUTE DATA CLEANING AND VALIDATION
    # ==================================================
    try:
        valid_df, rejected_df, duplicate_df = (
            clean_and_validate_data(raw_df)
        )
    except Exception as error:
        st.error(f"Data validation failed: {error}")
        st.stop()

    # ==================================================
    # 10. DATA QUALITY SUMMARY
    # ==================================================
    st.header("Data Cleaning and Validation Summary")

    total_records = len(raw_df)
    valid_records = len(valid_df)
    rejected_records = len(rejected_df)
    duplicate_records = len(duplicate_df)

    # Display summary metrics.
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Original Records",
        f"{total_records:,}"
    )
    col2.metric(
        "Valid Records",
        f"{valid_records:,}"
    )
    col3.metric(
        "Rejected Records",
        f"{rejected_records:,}"
    )
    col4.metric(
        "Duplicate Records",
        f"{duplicate_records:,}"
    )
    st.divider()

    # ==================================================
    # 11. VALIDATION STATUS
    # ==================================================
    if rejected_records == 0:
        st.success(
            "All production records passed validation!"
        )
    else:
        st.warning(
            f"{rejected_records} record(s) failed validation. "
            "Please review the rejection report."
        )

    # Explain duplicate handling.
    if duplicate_records > 0:
        st.warning(
            f"{duplicate_records} exact duplicate record(s) "
            "were detected. They are flagged for review and "
            "have not been automatically deleted. Duplicate "
            "rows remain in the valid dataset and KPI calculations "
            "until they are reviewed."
        )

    # ==================================================
    # 12. INTERACTIVE PRODUCTION KPI DASHBOARD
    # ==================================================
    if not valid_df.empty:
        # ==============================================
        # 12.1 CALCULATE TOTAL PRODUCTION
        # ==============================================
        total_target = valid_df["Target_Qty"].sum()
        total_actual = valid_df["Actual_Qty"].sum()
        total_defects = valid_df["Defects_Qty"].sum()

        total_good_qty = (
            valid_df["Actual_Qty"] -
            valid_df["Defects_Qty"]
        ).sum()

        production_gap = total_target - total_actual

        # ==============================================
        # 12.2 PRODUCTION ACHIEVEMENT
        # ==============================================
        achievement_pct = (
            (total_actual / total_target) * 100
            if total_target > 0 else 0
        )

        # ==============================================
        # 12.3 LABOUR EFFICIENCY
        # ==============================================
        total_earned_minutes = (
            (
                (valid_df["Actual_Qty"] -
                 valid_df["Defects_Qty"]) *
                valid_df["SMV"]
            ).sum()
        )

        total_available_labour_minutes = (
            valid_df["Operators_Count"] *
            valid_df["Shift_Minutes"]
        ).sum()

        efficiency_pct = (
            (total_earned_minutes /
             total_available_labour_minutes) * 100
            if total_available_labour_minutes > 0 else 0
        )

        # ==============================================
        # 12.4 DEFECT PERCENTAGE
        # ==============================================
        defect_pct = (
            (total_defects / total_actual) * 100
            if total_actual > 0 else 0
        )

        # ==============================================
        # 12.5 DOWNTIME PERCENTAGE
        # ==============================================
        total_downtime = valid_df["Downtime_Minutes"].sum()
        total_shift_minutes = valid_df["Shift_Minutes"].sum()

        downtime_pct = (
            (total_downtime / total_shift_minutes) * 100
            if total_shift_minutes > 0 else 0
        )

        # ==============================================
        # 12.6 DISPLAY DASHBOARD TITLE
        # ==============================================
        st.divider()
        st.header("ðŸ“Š Production Management KPIs")
        st.caption(
            "Performance calculations use validated production records only."
        )

        # ==============================================
        # 12.7 FIRST ROW - PRODUCTION KPIs
        # ==============================================
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Total Production Target",
            f"{total_target:,.0f}"
        )
        col2.metric(
            "Total Actual Production",
            f"{total_actual:,.0f}"
        )
        col3.metric(
            "Production Gap",
            f"{production_gap:,.0f}"
        )

        # ==============================================
        # 12.8 SECOND ROW - ACHIEVEMENT AND QUALITY
        # ==============================================
        col4, col5, col6 = st.columns(3)
        col4.metric(
            "Production Achievement",
            f"{achievement_pct:.2f}%"
        )
        col5.metric(
            "Good Production",
            f"{total_good_qty:,.0f}"
        )
        col6.metric(
            "Total Defects",
            f"{total_defects:,.0f}"
        )

        # ==============================================
        # 12.9 THIRD ROW - EFFICIENCY AND DOWNTIME
        # ==============================================
        col7, col8, col9 = st.columns(3)
        col7.metric(
            "Labour Efficiency",
            f"{efficiency_pct:.2f}%"
        )
        col8.metric(
            "Defect Percentage",
            f"{defect_pct:.2f}%"
        )
        col9.metric(
            "Downtime Percentage",
            f"{downtime_pct:.2f}%"
        )

        # ======================================================
        # LESSON 9 - STEP 6
        # INTERACTIVE PRODUCTION CHARTS
        # ======================================================
        st.divider()
        st.header("ðŸ“ˆ Interactive Production Analysis")

        # ======================================================
        # 1. CREATE DATE AND PRODUCTION LINE FILTERS
        # ======================================================
        st.subheader("Dashboard Filters")
        filter_col1, filter_col2 = st.columns(2)

        # Prepare production dates
        date_series = pd.to_datetime(
            valid_df["Date"],
            errors="coerce"
        )
        available_dates = date_series.dropna()

        if available_dates.empty:
            st.error("No valid production dates available.")
        else:
            min_date = available_dates.min().date()
            max_date = available_dates.max().date()

        with filter_col1:
            selected_dates = st.date_input(
                "Select production date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

        # Production line selection
        available_lines = sorted(
            valid_df["Production_Line"].unique().tolist()
        )
        with filter_col2:
            selected_lines = st.multiselect(
                "Select production lines",
                options=available_lines,
                default=available_lines
            )

        # Handle date selection
        if isinstance(selected_dates, (tuple, list)):
            if len(selected_dates) == 2:
                start_date, end_date = selected_dates
            else:
                start_date = min_date
                end_date = max_date
        else:
            start_date = selected_dates
            end_date = selected_dates

        # ==================================================
        # 2. FILTER PRODUCTION DATA
        # ==================================================
        date_mask = (
            date_series.dt.date >= start_date
        ) & (
            date_series.dt.date <= end_date
        )
        line_mask = valid_df[
            "Production_Line"
        ].isin(selected_lines)

        filtered_df = valid_df.loc[
            date_mask & line_mask
        ].copy()

        st.divider()

        # ==================================================
        # 3. CHECK FILTERED DATA
        # ==================================================
        if filtered_df.empty:
            st.warning(
                "No production records found for the selected filters."
            )
        else:
            st.write(
                f"Showing {len(filtered_df)} production records."
            )

            # ==================================================
            # 4. CALCULATE LINE-LEVEL SUMMARY
            # ==================================================
            chart_df = filtered_df.copy()

            chart_df["Good_Qty"] = (
                chart_df["Actual_Qty"] -
                chart_df["Defects_Qty"]
            )

            chart_df["Earned_Minutes"] = (
                chart_df["Good_Qty"] *
                chart_df["SMV"]
            )

            chart_df["Available_Labour_Minutes"] = (
                chart_df["Operators_Count"] *
                chart_df["Shift_Minutes"]
            )

            line_chart_summary = (
                chart_df
                .groupby(
                    "Production_Line",
                    as_index=False
                )
                .agg(
                    Total_Target=("Target_Qty", "sum"),
                    Total_Actual=("Actual_Qty", "sum"),
                    Total_Defects=("Defects_Qty", "sum"),
                    Total_Earned_Minutes=(
                        "Earned_Minutes", "sum"
                    ),
                    Total_Available_Labour_Minutes=(
                        "Available_Labour_Minutes", "sum"
                    ),
                    Total_Downtime=(
                        "Downtime_Minutes", "sum"
                    ),
                    Total_Shift_Minutes=(
                        "Shift_Minutes", "sum"
                    )
                )
            )

            # ==================================================
            # 5. CALCULATE PERCENTAGES
            # ==================================================
            line_chart_summary["Efficiency_Pct"] = (
                line_chart_summary["Total_Earned_Minutes"] /
                line_chart_summary["Total_Available_Labour_Minutes"]
            ) * 100

            line_chart_summary["Defect_Pct"] = (
                line_chart_summary.apply(
                    lambda row:
                    (
                        row["Total_Defects"] /
                        row["Total_Actual"] * 100
                    )
                    if row["Total_Actual"] > 0 else 0,
                    axis=1
                )
            )

            line_chart_summary["Downtime_Pct"] = (
                line_chart_summary["Total_Downtime"] /
                line_chart_summary["Total_Shift_Minutes"]
            ) * 100

            # ==================================================
            # 6. CHART 1 - TARGET VS ACTUAL
            # ==================================================
            st.subheader(
                "1. Production Target vs Actual"
            )
            production_chart = (
                line_chart_summary
                .set_index("Production_Line")[
                    ["Total_Target", "Total_Actual"]
                ]
            )
            production_chart.columns = [
                "Production Target",
                "Actual Production"
            ]
            st.bar_chart(
                production_chart
            )

            # ==================================================
            # 7. CHART 2 - LABOUR EFFICIENCY
            # ==================================================
            st.subheader(
                "2. Labour Efficiency by Production Line"
            )
            efficiency_chart = (
                line_chart_summary
                .set_index("Production_Line")[
                    ["Efficiency_Pct"]
                ]
            )
            efficiency_chart.columns = [
                "Labour Efficiency (%)"
            ]
            st.bar_chart(
                efficiency_chart
            )

            # ==================================================
            # 8. CHART 3 - DEFECT PERCENTAGE
            # ==================================================
            st.subheader(
                "3. Defect Percentage by Production Line"
            )
            defect_chart = (
                line_chart_summary
                .set_index("Production_Line")[
                    ["Defect_Pct"]
                ]
            )
            defect_chart.columns = [
                "Defect Percentage (%)"
            ]
            st.bar_chart(
                defect_chart
            )

            # ==================================================
            # 9. CHART 4 - DOWNTIME PERCENTAGE
            # ==================================================
            st.subheader(
                "4. Downtime Percentage by Production Line"
            )
            downtime_chart = (
                line_chart_summary
                .set_index("Production_Line")[
                    ["Downtime_Pct"]
                ]
            )
            downtime_chart.columns = [
                "Downtime Percentage (%)"
            ]
            st.bar_chart(
                downtime_chart
            )

            # ==================================================
            # 10. CHART 5 - DAILY PRODUCTION TREND
            # ==================================================
            st.subheader(
                "5. Daily Production Trends"
            )
            daily_chart_summary = (
                chart_df
                .groupby("Date")
                .agg(
                    Daily_Target=("Target_Qty", "sum"),
                    Daily_Actual=("Actual_Qty", "sum")
                )
                .sort_index()
            )

            daily_trend_chart = daily_chart_summary.copy()
            daily_trend_chart.columns = [
                "Daily Target",
                "Daily Actual"
            ]
            daily_chart_summary.index = (
            pd.to_datetime(daily_chart_summary.index)
            .strftime("%Y-%m-%d")
            )
            st.line_chart(
                daily_trend_chart
            )

            # ==================================================
            # LESSON 9 - STEP 7
            # AUTOMATIC MANAGEMENT INSIGHTS
            # ==================================================
            st.divider()
            st.subheader(
                "ðŸ’¡ Automatic Management Insights"
            )
            st.caption(
                "Insights are generated from the currently "
                "selected production dates and lines."
            )

            # ==================================================
            # 1. CALCULATE PRODUCTION GAP
            # ==================================================
            line_chart_summary["Production_Gap"] = (
                line_chart_summary["Total_Target"] -
                line_chart_summary["Total_Actual"]
            )

            # ==================================================
            # 2. CALCULATE DAILY ACHIEVEMENT
            # ==================================================
            daily_chart_summary["Daily_Achievement_Pct"] = (
                daily_chart_summary["Daily_Actual"] /
                daily_chart_summary["Daily_Target"]
            ) * 100

            # ==================================================
            # 3. IDENTIFY BEST AND WORST LABOUR EFFICIENCY
            # ==================================================
            best_efficiency = line_chart_summary.loc[
                line_chart_summary["Efficiency_Pct"].idxmax()
            ]
            worst_efficiency = line_chart_summary.loc[
                line_chart_summary["Efficiency_Pct"].idxmin()
            ]

            # ==================================================
            # 4. IDENTIFY HIGHEST DEFECT PERCENTAGE
            # ==================================================
            highest_defect = line_chart_summary.loc[
                line_chart_summary["Defect_Pct"].idxmax()
            ]

            # ==================================================
            # 5. IDENTIFY HIGHEST DOWNTIME PERCENTAGE
            # ==================================================
            highest_downtime = line_chart_summary.loc[
                line_chart_summary["Downtime_Pct"].idxmax()
            ]

            # ==================================================
            # 6. IDENTIFY LARGEST PRODUCTION GAP
            # ==================================================
            largest_gap = line_chart_summary.loc[
                line_chart_summary["Production_Gap"].idxmax()
            ]
            maximum_gap = largest_gap["Production_Gap"]

            # ==================================================
            # 7. IDENTIFY BEST AND WORST PRODUCTION DAYS
            # ==================================================
            best_day_date = (
                daily_chart_summary["Daily_Achievement_Pct"].idxmax()
            )
            worst_day_date = (
                daily_chart_summary["Daily_Achievement_Pct"].idxmin()
            )

            best_day_achievement = (
                daily_chart_summary.loc[
                    best_day_date,
                    "Daily_Achievement_Pct"
                ]
            )
            worst_day_achievement = (
                daily_chart_summary.loc[
                    worst_day_date,
                    "Daily_Achievement_Pct"
                ]
            )

            # ==================================================
            # 8. DISPLAY PRODUCTION LINE INSIGHTS
            # ==================================================
            st.markdown("#### Production Line Performance")
            insight_col1, insight_col2, insight_col3 = (
                st.columns(3)
            )

            with insight_col1:
                st.metric(
                    "Best Labour Efficiency",
                    f"{best_efficiency['Efficiency_Pct']:.2f}%"
                )
                st.caption(
                    best_efficiency["Production_Line"]
                )

            with insight_col2:
                st.metric(
                    "Lowest Labour Efficiency",
                    f"{worst_efficiency['Efficiency_Pct']:.2f}%"
                )
                st.caption(
                    worst_efficiency["Production_Line"]
                )

            with insight_col3:
                st.metric(
                    "Highest Defect Percentage",
                    f"{highest_defect['Defect_Pct']:.2f}%"
                )
                st.caption(
                    highest_defect["Production_Line"]
                )

            # ==================================================
            # 9. DISPLAY DOWNTIME AND PRODUCTION GAP
            # ==================================================
            insight_col4, insight_col5 = st.columns(2)

            with insight_col4:
                st.metric(
                    "Highest Downtime Percentage",
                    f"{highest_downtime['Downtime_Pct']:.2f}%"
                )
                st.caption(
                    highest_downtime["Production_Line"]
                )

            with insight_col5:
                if maximum_gap > 0:
                    st.metric(
                        "Largest Production Shortfall",
                        f"{maximum_gap:,.0f} garments"
                    )
                    st.caption(
                        largest_gap["Production_Line"]
                    )
                else:
                    st.metric(
                        "Production Shortfall",
                        "0 garments"
                    )
                    st.caption(
                        "All selected production lines achieved their targets."
                    )

            # ==================================================
            # 10. DISPLAY DAILY PERFORMANCE INSIGHTS
            # ==================================================
            st.markdown("#### Daily Production Performance")
            day_col1, day_col2 = st.columns(2)

            with day_col1:
                st.metric(
                    "Best Production Day",
                    f"{best_day_achievement:.2f}%"
                )
                st.caption(
                    pd.Timestamp(best_day_date).strftime("%Y-%m-%d")
                )

            with day_col2:
                st.metric(
                    "Worst Production Day",
                    f"{worst_day_achievement:.2f}%"
                )
                st.caption(
                    pd.Timestamp(worst_day_date).strftime("%Y-%m-%d")
                )

            # ==================================================
            # 11. GENERATE MANAGEMENT RECOMMENDATIONS
            # ==================================================
            st.markdown("#### Management Recommendations")

            st.info(
                f"Efficiency review: Investigate "
                f"{worst_efficiency['Production_Line']} "
                f"because it has the lowest labour efficiency."
            )

            st.warning(
                f"Quality review: Investigate defect patterns "
                f"and inspection results for "
                f"{highest_defect['Production_Line']}."
            )

            st.warning(
                f"Downtime review: Examine machine breakdowns, "
                f"material shortages and downtime records for "
                f"{highest_downtime['Production_Line']}."
            )

            if maximum_gap > 0:
                st.info(
                    f"Production planning review: "
                    f"{largest_gap['Production_Line']} has "
                    f"a shortfall of {maximum_gap:,.0f} garments."
                )
            else:
                st.success(
                    "All selected production lines achieved "
                    "or exceeded their production targets."
                )

            st.caption(
                "Recommendations identify areas for investigation. "
                "Actual root causes require further production data."
            )

            # ==================================================
            # 12. CREATE MANAGEMENT INSIGHTS REPORT
            # ==================================================
            insights_records = [
                {
                    "Category": "Best Labour Efficiency",
                    "Finding": best_efficiency["Production_Line"],
                    "Value": best_efficiency["Efficiency_Pct"],
                    "Unit": "%"
                },
                {
                    "Category": "Lowest Labour Efficiency",
                    "Finding": worst_efficiency["Production_Line"],
                    "Value": worst_efficiency["Efficiency_Pct"],
                    "Unit": "%"
                },
                {
                    "Category": "Highest Defect Percentage",
                    "Finding": highest_defect["Production_Line"],
                    "Value": highest_defect["Defect_Pct"],
                    "Unit": "%"
                },
                {
                    "Category": "Highest Downtime Percentage",
                    "Finding": highest_downtime["Production_Line"],
                    "Value": highest_downtime["Downtime_Pct"],
                    "Unit": "%"
                },
                {
                    "Category": "Largest Production Gap",
                    "Finding": (
                        largest_gap["Production_Line"]
                        if maximum_gap > 0
                        else "All selected lines achieved target"
                    ),
                    "Value": max(0, maximum_gap),
                    "Unit": "Garments"
                },
                {
                    "Category": "Best Production Day",
                    "Finding": pd.Timestamp(
                        best_day_date
                    ).strftime("%Y-%m-%d"),
                    "Value": best_day_achievement,
                    "Unit": "%"
                },
                {
                    "Category": "Worst Production Day",
                    "Finding": pd.Timestamp(
                        worst_day_date
                    ).strftime("%Y-%m-%d"),
                    "Value": worst_day_achievement,
                    "Unit": "%"
                }
            ]

            management_insights_df = pd.DataFrame(
                insights_records
            )

            # ==================================================
            # 13. DISPLAY INSIGHTS TABLE
            # ==================================================
            with st.expander(
                "View Complete Management Insights Report"
            ):
                st.dataframe(
                    management_insights_df,
                    width="stretch"
                )

            # ==================================================
            # 14. DOWNLOAD MANAGEMENT INSIGHTS
            # ==================================================
            insights_csv = (
                management_insights_df
                .to_csv(index=False)
                .encode("utf-8-sig")
            )

            st.download_button(
                label="Download Management Insights CSV",
                data=insights_csv,
                file_name="management_insights.csv",
                mime="text/csv",
                key="download_management_insights"
            )

            st.success(
                "Automatic management insights generated successfully!"
            )

            # ==================================================
            # LESSON 9 - STEP 8
            # CONSOLIDATED PRODUCTION REPORTS
            # ==================================================

            st.divider()

            st.header("ðŸ“¥ Consolidated Production Reports")

            st.write(
                "Download all production management reports "
                "in one Excel workbook."
            )


            # ==================================================
            # 1. CREATE REPORT OVERVIEW
            # ==================================================

            report_overview_df = pd.DataFrame({

                "Report Information": [
                    "Report Name",
                    "Generated Date",
                    "Selected Start Date",
                    "Selected End Date",
                    "Selected Production Lines",
                    "Total Uploaded Records",
                    "Valid Records",
                    "Rejected Records",
                    "Duplicate Records"
                ],

                "Value": [
                    "Apparel Production Management Report",
                    pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    str(start_date),
                    str(end_date),
                    ", ".join(selected_lines),
                    len(raw_df),
                    len(valid_df),
                    len(rejected_df),
                    len(duplicate_df)
                ]
            })


            # ==================================================
            # 2. CREATE VALIDATION SUMMARY
            # ==================================================

            validation_summary_df = pd.DataFrame({

                "Category": [
                    "Original Records",
                    "Valid Records",
                    "Rejected Records",
                    "Duplicate Records"
                ],

                "Count": [
                    len(raw_df),
                    len(valid_df),
                    len(rejected_df),
                    len(duplicate_df)
                ]
            })


            # ==================================================
            # 3. CREATE OVERALL KPI REPORT
            # ==================================================

            overall_kpi_df = pd.DataFrame({

                "KPI": [
                    "Total Production Target",
                    "Total Actual Production",
                    "Production Gap",
                    "Production Achievement (%)",
                    "Good Production",
                    "Total Defects",
                    "Labour Efficiency (%)",
                    "Defect Percentage (%)",
                    "Downtime Percentage (%)",
                    "Total Downtime Minutes",
                    "Total Earned Minutes",
                    "Total Available Labour Minutes"
                ],

                "Value": [
                    total_target,
                    total_actual,
                    production_gap,
                    achievement_pct,
                    total_good_qty,
                    total_defects,
                    efficiency_pct,
                    defect_pct,
                    downtime_pct,
                    total_downtime,
                    total_earned_minutes,
                    total_available_labour_minutes
                ]
            })


            # ==================================================
            # 4. PREPARE PRODUCTION LINE REPORT
            # ==================================================

            production_line_report_df = (
                line_chart_summary.copy()
            )


            # ==================================================
            # 5. PREPARE DAILY PERFORMANCE REPORT
            # ==================================================

            daily_performance_report_df = (
                daily_chart_summary
                .rename_axis("Date")
                .reset_index()
            )


            # ==================================================
            # 6. PREPARE VALID RECORDS REPORT
            # ==================================================

            valid_records_report_df = valid_df.drop(
                columns=["Validation_Issues"],
                errors="ignore"
            ).copy()


            # ==================================================
            # 7. PREPARE FILTERED RECORDS REPORT
            # ==================================================

            filtered_records_report_df = filtered_df.drop(
                columns=["Validation_Issues"],
                errors="ignore"
            ).copy()


            # ==================================================
            # 8. CREATE EXCEL WORKBOOK IN MEMORY
            # ==================================================

            excel_buffer = BytesIO()

            try:

                with pd.ExcelWriter(
                    excel_buffer,
                    engine="openpyxl",
                    datetime_format="yyyy-mm-dd"
                ) as writer:


                    # ==========================================
                    # SHEET 1 - REPORT OVERVIEW
                    # ==========================================

                    report_overview_df.to_excel(
                        writer,
                        sheet_name="Report_Overview",
                        index=False
                    )


                    # ==========================================
                    # SHEET 2 - VALIDATION SUMMARY
                    # ==========================================

                    validation_summary_df.to_excel(
                        writer,
                        sheet_name="Validation_Summary",
                        index=False
                    )


                    # ==========================================
                    # SHEET 3 - OVERALL KPIs
                    # ==========================================

                    overall_kpi_df.to_excel(
                        writer,
                        sheet_name="Overall_KPIs",
                        index=False
                    )


                    # ==========================================
                    # SHEET 4 - PRODUCTION LINE REPORT
                    # ==========================================

                    production_line_report_df.to_excel(
                        writer,
                        sheet_name="Production_Lines",
                        index=False
                    )


                    # ==========================================
                    # SHEET 5 - DAILY PERFORMANCE
                    # ==========================================

                    daily_performance_report_df.to_excel(
                        writer,
                        sheet_name="Daily_Performance",
                        index=False
                    )


                    # ==========================================
                    # SHEET 6 - MANAGEMENT INSIGHTS
                    # ==========================================

                    management_insights_df.to_excel(
                        writer,
                        sheet_name="Management_Insights",
                        index=False
                    )


                    # ==========================================
                    # SHEET 7 - ORIGINAL UPLOADED DATA
                    # ==========================================

                    raw_df.to_excel(
                        writer,
                        sheet_name="Uploaded_Data",
                        index=False
                    )


                    # ==========================================
                    # SHEET 8 - VALID RECORDS
                    # ==========================================

                    valid_records_report_df.to_excel(
                        writer,
                        sheet_name="Valid_Records",
                        index=False
                    )


                    # ==========================================
                    # SHEET 9 - REJECTED RECORDS
                    # ==========================================

                    rejected_df.to_excel(
                        writer,
                        sheet_name="Rejected_Records",
                        index=False
                    )


                    # ==========================================
                    # SHEET 10 - DUPLICATE RECORDS
                    # ==========================================

                    duplicate_df.to_excel(
                        writer,
                        sheet_name="Duplicate_Records",
                        index=False
                    )


                    # ==========================================
                    # SHEET 11 - FILTERED RECORDS
                    # ==========================================

                    filtered_records_report_df.to_excel(
                        writer,
                        sheet_name="Filtered_Records",
                        index=False
                    )


                    # ==========================================
                    # 9. FORMAT ALL EXCEL WORKSHEETS
                    # ==========================================

                    for worksheet in writer.book.worksheets:

                        # Keep column headers visible
                        worksheet.freeze_panes = "A2"

                        # Enable Excel column filters
                        if worksheet.max_row >= 1:

                            worksheet.auto_filter.ref = (
                                worksheet.dimensions
                            )

                        # Adjust column widths automatically
                        for column_cells in worksheet.columns:

                            max_length = max(
                                (
                                    len(str(cell.value))
                                    if cell.value is not None
                                    else 0
                                )
                                for cell in column_cells
                            )

                            column_letter = (
                                column_cells[0].column_letter
                            )

                            worksheet.column_dimensions[
                                column_letter
                            ].width = min(max_length + 3, 45)


                # ==========================================
                # 10. DOWNLOAD CONSOLIDATED WORKBOOK
                # ==========================================

                excel_data = excel_buffer.getvalue()

                st.download_button(

                    label="ðŸ“¥ Download Complete Production Report",

                    data=excel_data,

                    file_name="apparel_production_management_report.xlsx",

                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),

                    key="download_consolidated_production_report"
                )

                st.success(
                    "Consolidated production report generated successfully!"
                )

                st.caption(
                    "The Excel workbook contains 11 worksheets "
                    "covering production, validation, KPIs "
                    "and management insights."
                )


            except ImportError:

                st.error(
                    "Excel export library is missing. "
                    "Run: python -m pip install openpyxl"
                )


            except Exception as error:

                st.error(
                    f"Unable to generate Excel report: {error}"
                )


    # ==================================================
    # 13. VALID PRODUCTION RECORDS
    # ==================================================
    st.divider()
    st.header("Valid Production Records")
    st.write(
        "These records passed all configured validation rules."
    )

    valid_display_df = valid_df.drop(
        columns=["Validation_Issues"],
        errors="ignore"
    )

    if not valid_display_df.empty:
        st.dataframe(
            valid_display_df,
            width="stretch"
        )
    else:
        st.info("There are no valid production records to display.")

    # ==================================================
    # 14. REJECTED PRODUCTION RECORDS
    # ==================================================
    st.header("Rejected Production Records")

    if not rejected_df.empty:
        st.write(
            "The following records failed one or more validation rules."
        )
        st.dataframe(
            rejected_df,
            width="stretch"
        )
    else:
        st.info("No rejected production records were found.")

    # ==================================================
    # 15. DUPLICATE RECORD REVIEW
    # ==================================================
    with st.expander("Review Duplicate Records"):
        if not duplicate_df.empty:
            st.write(
                "These rows repeat an earlier record based on the "
                "required production columns. They have not been deleted."
            )
            st.dataframe(
                duplicate_df,
                width="stretch"
            )
        else:
            st.success("No exact duplicate records detected.")

    # ==================================================
    # 16. DOWNLOAD VALIDATION REPORTS
    # ==================================================
    st.header("Download Validation Reports")
    download_col1, download_col2 = st.columns(2)

    # Prepare the valid production data for download.
    cleaned_download_df = valid_display_df
    cleaned_csv = cleaned_download_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    rejected_csv = rejected_df.to_csv(
        index=False
    ).encode("utf-8-sig")

    with download_col1:
        st.download_button(
            label="Download Cleaned Production Data",
            data=cleaned_csv,
            file_name="cleaned_production_data.csv",
            mime="text/csv",
            disabled=valid_df.empty
        )

    with download_col2:
        st.download_button(
            label="Download Rejected Records Report",
            data=rejected_csv,
            file_name="rejected_production_records.csv",
            mime="text/csv",
            disabled=rejected_df.empty
        )

    # ==================================================
    # 17. SAVE CLEAN DATA FOR FUTURE ANALYSIS
    # ==================================================
    st.session_state["cleaned_production_df"] = (
        cleaned_download_df.copy()
    )
    st.session_state["rejected_production_df"] = (
        rejected_df.copy()
    )

    st.success(
        "Production data cleaning and validation completed!"
    )

# ======================================================
# 18. INITIAL APPLICATION MESSAGE
# ======================================================
else:
    st.info(
        "Please upload a production CSV file using the sidebar."
    )

    st.subheader("Application Features")
    st.write(
        """
        1. Production CSV Upload
        2. Data Cleaning
        3. Missing Value Validation
        4. Numeric Data Validation
        5. Apparel Manufacturing Business Rules
        6. Duplicate Record Detection
        7. Valid and Rejected Data Separation
        8. Downloadable Validation Reports
        9. Interactive Production KPI Dashboard
        """
    )
