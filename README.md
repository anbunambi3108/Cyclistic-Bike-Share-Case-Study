# 🚲 Cyclistic Bike Share Analysis

Data driven membership conversion strategy using rider behavior analysis

A comprehensive data analytics case study analyzing Cyclistic bike share usage patterns to identify how casual riders differ from members and how those differences can be used to increase annual memberships.

## 📌 Overview

Cyclistic aims to grow annual memberships by converting casual riders. This project analyzes one year of Divvy Tripdata from October 2024 through September 2025 to understand how members and casual riders use the system differently. By examining trip duration, timing, geography, and seasonal behavior, the analysis surfaces actionable insights that inform pricing, promotions, and operational decisions designed to drive membership conversion.

## ✨ Key Highlights

* Analyzed over a full year of bike share trips to capture seasonal and behavioral patterns
* Identified clear differences in trip duration, timing, and geography between rider types
* Quantified weekend and leisure driven usage among casual riders
* Mapped commuter focused patterns among annual members
* Translated behavioral insights into concrete business recommendations

## 🧩 Features

| Component           | Description                                             | Status   |
| ------------------- | ------------------------------------------------------- | -------- |
| Data Aggregation    | Combined 12 monthly trip files into a unified dataset   | Complete |
| Feature Engineering | Created time based and seasonal features                | Complete |
| Data Cleaning       | Standardized labels, removed outliers, cleaned stations | Complete |
| Behavioral Analysis | Compared usage patterns by rider type                   | Complete |
| Geographic Insights | Analyzed station usage by rider intent                  | Complete |
| Business Strategy   | Developed conversion focused recommendations            | Complete |

## 🧪 Methodology

### 1. Data Collection

* Divvy Tripdata from October 2024 to September 2025
* Monthly CSV files consolidated into a single dataset

### 2. Data Processing

* Parsed timestamps into month, weekday, hour, and season
* Standardized member and casual rider labels
* Cleaned station names and IDs
* Removed extreme outliers and invalid records

### 3. Analysis

* Compared trip counts and ride duration by rider type
* Analyzed weekday vs weekend behavior
* Evaluated hourly usage patterns
* Examined holiday usage trends
* Identified geographic clustering of ride activity

### 4. Insight Validation

* Cross checked patterns across time, duration, and geography
* Focused on repeatable behaviors rather than one off spikes

## 📊 Key Results

### Usage Patterns

* Members account for the majority of total rides, while casual riders represent a significant minority
* Casual riders take nearly twice as long per trip compared to members
* Weekend usage is substantially higher for casual riders
* Member activity peaks during weekday commute hours
* Casual rider demand peaks later in the day

### Business Implications

* Casual riders behave like leisure and tourism users
* Members primarily use bikes as part of a commuting routine
* Pricing and messaging should reflect these fundamentally different use cases

## 🛠️ Technologies

### Tools

| Technology       | Purpose                         |
| ---------------- | ------------------------------- |
| SQL              | Data validation and aggregation |
| Python           | Data cleaning and analysis      |
| Pandas           | Feature engineering             |
| NumPy            | Numerical operations            |
| Matplotlib       | Trend visualization             |
| Seaborn          | Comparative analysis            |
| Jupyter Notebook | Analysis workflow               |

### Libraries Used

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

## 🧠 Skills Demonstrated

* Data cleaning and feature engineering at scale
* Behavioral segmentation analysis
* Time series and seasonality analysis
* Translating data insights into business strategy
* Stakeholder focused recommendation framing

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* Jupyter Notebook

### Usage

```bash
git clone https://github.com/your-username/cyclistic-bike-share-analysis.git
cd cyclistic-bike-share-analysis
jupyter notebook
```

Run notebooks in sequence to reproduce the analysis.

## 📎 Additional Resources

**Dataset:**
[https://divvy-tripdata.s3.amazonaws.com/index.html](https://divvy-tripdata.s3.amazonaws.com/index.html)

