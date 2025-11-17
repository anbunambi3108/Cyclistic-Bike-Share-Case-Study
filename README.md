# Cyclistic Bike-Share: Google Data Analytics Case Study
## Business Task
Increase annual memberships by converting casual riders based on usage patterns.

## Data
Divvy Tripdata (12 months, 2024-10 to 2025-09). Excluded rides <=1 min or >=24h and rows with blank station fields.

## Process
- Combined 12 monthly CSVs into a single dataset.
- Parsed timestamps; engineered `month`, `weekday`, `season`, and 12-hour `hour` features.
- Validated station names/IDs; removed outliers; standardized `member_casual` labels.

## Key Findings
- Members concentrate on weekday commute windows; casual riders peak on weekends and summer evenings.

## Actions
1. [Recommendation tied to a KPI + success metric, e.g., “Launch weekday commuter offer at top member hubs → target +X% new members in 60 days.”]
2. [Recommendation #2 with metric.]
3. [Recommendation #3 with metric.]

🗃️ **Dataset:** The dataset used in this analysis (Oct 2024 - Sept 2025) can be found[divvy-tripdata.s3.amazonaws.com](https://divvy-tripdata.s3.amazonaws.com/index.html)  
✒️ **Method & narrative:** Read my write-up: *From Data to Insights: Google’s Cyclistic Case Study* — [Medium article link](#)  
📝 **Background:** Program context and problem framing — [Cyclistic Case Study](#)
