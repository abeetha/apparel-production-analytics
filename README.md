
# Apparel Production Planning & Efficiency Analytics

An interactive data analytics application for monitoring
apparel manufacturing production performance.

## Project Overview

This project analyses apparel production data to help
production managers monitor factory performance,
identify production inefficiencies and investigate
quality and downtime issues.

The application uses Python, Pandas and Streamlit to
transform production records into interactive dashboards
and management reports.

## Key Features

- Production CSV file upload
- Data cleaning and validation
- Missing and invalid data identification
- Duplicate record detection
- Production KPI calculations
- Production target vs actual analysis
- Labour efficiency analysis
- Defect percentage analysis
- Production downtime analysis
- Interactive date and production line filters
- Automatic management insights
- Consolidated Excel management reports

## Technology Stack

- Python
- Pandas
- NumPy
- Streamlit
- Matplotlib
- OpenPyXL
- Jupyter Notebook

## Production KPIs

### Production Achievement

Actual Production / Production Target * 100

### Labour Efficiency

Earned Minutes / Available Labour Minutes * 100

### Defect Percentage

Total Defects / Actual Production * 100

### Downtime Percentage

Total Downtime Minutes / Total Shift Minutes * 100

### Good Production

Actual Production - Defects

## Data Validation Rules

- Production date must be valid.
- Production line and style cannot be empty.
- Target quantity must be greater than zero.
- Actual production cannot be negative.
- SMV must be greater than zero.
- Shift duration must be greater than zero.
- Downtime cannot exceed shift duration.
- Defects cannot exceed actual production.
- Operator count must be greater than zero.
- Duplicate records are identified for review.

## Project Structure

apparel-production-analytics/
    app.py
    requirements.txt
    README.md
    .gitignore
    data/
    notebooks/
    output/
    .streamlit/

## Installation

Clone the repository:

    git clone https://github.com/abeetha/apparel-production-analytics.git

Navigate to the project folder:

    cd apparel-production-analytics

Install dependencies:

    python -m pip install -r requirements.txt

Run the application:

    python -m streamlit run app.py

Open:

    http://localhost:8501

## Business Value

The application helps production managers:

- Monitor production target achievement.
- Identify low-efficiency production lines.
- Investigate quality problems.
- Monitor production downtime.
- Compare daily production performance.
- Generate management reports.

## Project Status

Developed as a portfolio project demonstrating
Python data analysis, data cleaning, data visualization
and interactive dashboard development.

## Author

Abeetha Abeysundera
