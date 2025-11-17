# Cyclistic Bike-Share: Google Data Analytics Case Study

## Business Task

Increase annual memberships by converting casual riders based on how they use the system.

## Data

Divvy Tripdata from Oct 2024 to Sept 2025.
Rides shorter than 1 minute, longer than 24 hours, or missing station fields were removed.

## Process

* Combined 12 monthly CSV files into one dataset.
* Parsed timestamps and created month, weekday, season, and hour features.
* Cleaned station names and IDs, removed outliers, standardized member_casual labels.

## Detailed Findings

* Members account for 64 percent of all rides; casual riders make up 36 percent.
* Casual riders take longer trips (23 minutes vs. 12 minutes for members).
* Weekend riding is much heavier among casual riders (38 percent of their rides) compared to members (23 percent).
* Member usage peaks during commute windows, while casual riders peak later in the day.
* Holiday usage remains member-heavy at 63 percent.
* Members cluster around commuter corridors; casual riders lean toward leisure and tourist areas.

## Strategic Recommendations

### 1. Time-Based Membership Tiers

Create flexible passes: a commuter-focused peak-hour plan and a weekend leisure pass priced for long, casual trips.

### 2. High-Value Conversion Promotions

Run seasonal conversion pushes like a Summer Pass or holiday bundles that roll into discounted annual memberships.

### 3. Destination-Based Incentives

Partner with attractions, restaurants, and entertainment spots near top casual-rider stations to encourage on-site membership sign-ups.

### 4. Duration-Incentive Messaging

Speak directly to long-trip casual riders: highlight how members avoid high per-minute fees. Offer reduced pricing for member trips over 30 minutes to reinforce loyalty.

### 5. Geographic and Inventory Optimization

Shift bikes toward leisure hotspots on weekends and holidays. Reinforce commuter routes during weekday peaks to keep both groups satisfied.

## Actions

1. Launch a weekday commuter offer at top member hubs and track new memberships over the first 60 days.
2. Run a summer conversion campaign aimed at casual riders who spike on weekends.
3. Integrate promotions with high-traffic leisure destinations and measure sign-ups driven by these partnerships.

## Additional Resources

**Dataset:** [https://divvy-tripdata.s3.amazonaws.com/index.html](https://divvy-tripdata.s3.amazonaws.com/index.html)
