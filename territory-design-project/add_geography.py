"""
Add Geographic Data to Accounts

This script adds realistic geographic information to accounts.csv:
- City
- State
- ZIP code
- Latitude/Longitude

This enables geographic clustering and travel distance calculations.
"""

import pandas as pd
import random

# Realistic US cities with coordinates (major business hubs)
US_CITIES = [
    # West Coast
    {'city': 'San Francisco', 'state': 'CA', 'zip': '94102', 'lat': 37.7749, 'lon': -122.4194, 'region': 'West'},
    {'city': 'Los Angeles', 'state': 'CA', 'zip': '90012', 'lat': 34.0522, 'lon': -118.2437, 'region': 'West'},
    {'city': 'San Diego', 'state': 'CA', 'zip': '92101', 'lat': 32.7157, 'lon': -117.1611, 'region': 'West'},
    {'city': 'San Jose', 'state': 'CA', 'zip': '95113', 'lat': 37.3382, 'lon': -121.8863, 'region': 'West'},
    {'city': 'Seattle', 'state': 'WA', 'zip': '98101', 'lat': 47.6062, 'lon': -122.3321, 'region': 'West'},
    {'city': 'Portland', 'state': 'OR', 'zip': '97201', 'lat': 45.5152, 'lon': -122.6784, 'region': 'West'},

    # Mountain
    {'city': 'Denver', 'state': 'CO', 'zip': '80202', 'lat': 39.7392, 'lon': -104.9903, 'region': 'Mountain'},
    {'city': 'Phoenix', 'state': 'AZ', 'zip': '85004', 'lat': 33.4484, 'lon': -112.0740, 'region': 'Mountain'},
    {'city': 'Salt Lake City', 'state': 'UT', 'zip': '84101', 'lat': 40.7608, 'lon': -111.8910, 'region': 'Mountain'},

    # Midwest
    {'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'lat': 41.8781, 'lon': -87.6298, 'region': 'Midwest'},
    {'city': 'Minneapolis', 'state': 'MN', 'zip': '55401', 'lat': 44.9778, 'lon': -93.2650, 'region': 'Midwest'},
    {'city': 'Detroit', 'state': 'MI', 'zip': '48201', 'lat': 42.3314, 'lon': -83.0458, 'region': 'Midwest'},
    {'city': 'Cleveland', 'state': 'OH', 'zip': '44101', 'lat': 41.4993, 'lon': -81.6944, 'region': 'Midwest'},
    {'city': 'Columbus', 'state': 'OH', 'zip': '43215', 'lat': 39.9612, 'lon': -82.9988, 'region': 'Midwest'},

    # South
    {'city': 'Austin', 'state': 'TX', 'zip': '78701', 'lat': 30.2672, 'lon': -97.7431, 'region': 'South'},
    {'city': 'Dallas', 'state': 'TX', 'zip': '75201', 'lat': 32.7767, 'lon': -96.7970, 'region': 'South'},
    {'city': 'Houston', 'state': 'TX', 'zip': '77002', 'lat': 29.7604, 'lon': -95.3698, 'region': 'South'},
    {'city': 'Atlanta', 'state': 'GA', 'zip': '30303', 'lat': 33.7490, 'lon': -84.3880, 'region': 'South'},
    {'city': 'Miami', 'state': 'FL', 'zip': '33131', 'lat': 25.7617, 'lon': -80.1918, 'region': 'South'},
    {'city': 'Nashville', 'state': 'TN', 'zip': '37201', 'lat': 36.1627, 'lon': -86.7816, 'region': 'South'},
    {'city': 'Charlotte', 'state': 'NC', 'zip': '28202', 'lat': 35.2271, 'lon': -80.8431, 'region': 'South'},

    # Northeast
    {'city': 'New York', 'state': 'NY', 'zip': '10001', 'lat': 40.7128, 'lon': -74.0060, 'region': 'Northeast'},
    {'city': 'Boston', 'state': 'MA', 'zip': '02101', 'lat': 42.3601, 'lon': -71.0589, 'region': 'Northeast'},
    {'city': 'Philadelphia', 'state': 'PA', 'zip': '19102', 'lat': 39.9526, 'lon': -75.1652, 'region': 'Northeast'},
    {'city': 'Washington', 'state': 'DC', 'zip': '20001', 'lat': 38.9072, 'lon': -77.0369, 'region': 'Northeast'},
    {'city': 'Baltimore', 'state': 'MD', 'zip': '21201', 'lat': 39.2904, 'lon': -76.6122, 'region': 'Northeast'},
]

def add_geography_to_accounts(input_file='accounts.csv', output_file='accounts_with_geography.csv'):
    """
    Add geographic data to accounts CSV file.

    Distribution strategy:
    - Larger accounts tend to cluster in major metros (NY, SF, Chicago, Boston)
    - Smaller accounts more distributed
    - Create some natural clustering for realistic territories
    """

    print("Loading accounts...")
    df = pd.read_csv(input_file)

    # Create weighted distribution (more accounts in major metros)
    # Weight by typical business concentration
    city_weights = []
    for city in US_CITIES:
        if city['city'] in ['New York', 'San Francisco', 'Chicago', 'Boston', 'Los Angeles']:
            weight = 3.0  # Major tech/business hubs get 3x accounts
        elif city['city'] in ['Seattle', 'Austin', 'Denver', 'Atlanta']:
            weight = 2.0  # Growing tech hubs get 2x
        else:
            weight = 1.0
        city_weights.append(weight)

    # Normalize weights
    total_weight = sum(city_weights)
    city_probs = [w / total_weight for w in city_weights]

    # Assign cities to accounts
    print("Assigning geographic locations...")
    assigned_cities = random.choices(US_CITIES, weights=city_probs, k=len(df))

    # Add geography columns
    df['city'] = [c['city'] for c in assigned_cities]
    df['state'] = [c['state'] for c in assigned_cities]
    df['zip_code'] = [c['zip'] for c in assigned_cities]
    df['latitude'] = [c['lat'] for c in assigned_cities]
    df['longitude'] = [c['lon'] for c in assigned_cities]
    df['region'] = [c['region'] for c in assigned_cities]

    # Save updated file
    print(f"Saving to {output_file}...")
    df.to_csv(output_file, index=False)

    # Print summary
    print("\n" + "="*80)
    print("GEOGRAPHIC DISTRIBUTION SUMMARY")
    print("="*80)

    print("\nAccounts by Region:")
    print(df['region'].value_counts().sort_index())

    print("\nTop 10 Cities by Account Count:")
    print(df['city'].value_counts().head(10))

    print("\nAccounts by State:")
    print(df['state'].value_counts().sort_values(ascending=False).head(10))

    print("\n" + "="*80)
    print(f"✓ Successfully added geography to {len(df)} accounts")
    print(f"✓ Saved to: {output_file}")
    print("="*80)

    return df


if __name__ == "__main__":
    # Add geography to accounts
    df = add_geography_to_accounts()

    # Show sample
    print("\nSample accounts with geography:")
    print(df[['account_name', 'city', 'state', 'estimated_annual_value', 'current_owner']].head(10))
