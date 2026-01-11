"""
Geographic Clustering Utilities for Territory Design

This module provides functions for geographic-based territory design:
- Distance calculations between accounts
- Geographic clustering
- Territory compactness metrics
- Travel time estimation
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on earth (in miles).

    Uses the Haversine formula for accuracy.

    Parameters:
    -----------
    lat1, lon1 : float
        Latitude and longitude of first point (in degrees)
    lat2, lon2 : float
        Latitude and longitude of second point (in degrees)

    Returns:
    --------
    float : Distance in miles
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Radius of earth in miles
    r = 3956

    return c * r


def calculate_territory_center(accounts_df):
    """
    Calculate the geographic center of a territory (weighted by account value).

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude, estimated_annual_value columns

    Returns:
    --------
    tuple : (center_lat, center_lon)
    """
    if len(accounts_df) == 0:
        return None, None

    # Weight by account value
    total_value = accounts_df['estimated_annual_value'].sum()

    if total_value == 0:
        # If no value, use simple average
        center_lat = accounts_df['latitude'].mean()
        center_lon = accounts_df['longitude'].mean()
    else:
        # Weighted average by account value
        center_lat = (accounts_df['latitude'] * accounts_df['estimated_annual_value']).sum() / total_value
        center_lon = (accounts_df['longitude'] * accounts_df['estimated_annual_value']).sum() / total_value

    return center_lat, center_lon


def calculate_territory_radius(accounts_df, center_lat, center_lon):
    """
    Calculate the maximum distance from territory center to any account.

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude columns
    center_lat, center_lon : float
        Territory center coordinates

    Returns:
    --------
    float : Maximum distance in miles
    """
    if len(accounts_df) == 0 or center_lat is None:
        return 0

    distances = []
    for _, account in accounts_df.iterrows():
        dist = haversine_distance(
            center_lat, center_lon,
            account['latitude'], account['longitude']
        )
        distances.append(dist)

    return max(distances) if distances else 0


def calculate_average_distance_to_center(accounts_df, center_lat, center_lon):
    """
    Calculate average distance from accounts to territory center.

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude columns
    center_lat, center_lon : float
        Territory center coordinates

    Returns:
    --------
    float : Average distance in miles
    """
    if len(accounts_df) == 0 or center_lat is None:
        return 0

    distances = []
    for _, account in accounts_df.iterrows():
        dist = haversine_distance(
            center_lat, center_lon,
            account['latitude'], account['longitude']
        )
        distances.append(dist)

    return np.mean(distances) if distances else 0


def estimate_travel_time(distance_miles, city_driving=True):
    """
    Estimate travel time based on distance.

    Parameters:
    -----------
    distance_miles : float
        Distance in miles
    city_driving : bool
        If True, assumes city traffic (slower). If False, assumes highway.

    Returns:
    --------
    float : Estimated travel time in hours
    """
    if city_driving:
        # City driving: ~25 mph average (traffic, lights, parking)
        mph = 25
    else:
        # Highway: ~60 mph average
        mph = 60

    return distance_miles / mph


def calculate_total_territory_travel(accounts_df):
    """
    Calculate total annual travel distance for a territory.

    Assumes:
    - Rep visits each account quarterly (4 times/year)
    - Rep starts from territory center
    - Round trip (there and back)

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude columns

    Returns:
    --------
    dict : Travel metrics
        {
            'total_annual_miles': Total miles driven per year,
            'total_annual_hours': Total hours spent traveling,
            'avg_distance_per_visit': Average one-way distance
        }
    """
    if len(accounts_df) == 0:
        return {
            'total_annual_miles': 0,
            'total_annual_hours': 0,
            'avg_distance_per_visit': 0
        }

    # Calculate territory center
    center_lat, center_lon = calculate_territory_center(accounts_df)

    # Calculate distances
    distances = []
    for _, account in accounts_df.iterrows():
        dist = haversine_distance(
            center_lat, center_lon,
            account['latitude'], account['longitude']
        )
        distances.append(dist)

    avg_distance = np.mean(distances)

    # Assumptions
    VISITS_PER_YEAR = 4  # Quarterly visits
    ROUND_TRIP = 2  # There and back

    total_annual_miles = sum(distances) * VISITS_PER_YEAR * ROUND_TRIP
    total_annual_hours = sum([estimate_travel_time(d) for d in distances]) * VISITS_PER_YEAR * ROUND_TRIP

    return {
        'total_annual_miles': total_annual_miles,
        'total_annual_hours': total_annual_hours,
        'avg_distance_per_visit': avg_distance
    }


def analyze_geographic_balance(accounts_df, owner_column='current_owner'):
    """
    Analyze geographic distribution and travel metrics for all territories.

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude, and owner columns
    owner_column : str
        Column name for territory owner

    Returns:
    --------
    DataFrame : Geographic metrics by rep
    """
    reps = accounts_df[owner_column].unique()
    results = []

    for rep in reps:
        rep_accounts = accounts_df[accounts_df[owner_column] == rep]

        # Calculate center
        center_lat, center_lon = calculate_territory_center(rep_accounts)

        # Calculate geographic metrics
        max_radius = calculate_territory_radius(rep_accounts, center_lat, center_lon)
        avg_distance = calculate_average_distance_to_center(rep_accounts, center_lat, center_lon)
        travel_metrics = calculate_total_territory_travel(rep_accounts)

        # Get region distribution
        regions = rep_accounts['region'].value_counts().to_dict()
        primary_region = rep_accounts['region'].mode()[0] if len(rep_accounts) > 0 else None
        region_concentration = (rep_accounts['region'] == primary_region).sum() / len(rep_accounts) if len(rep_accounts) > 0 else 0

        results.append({
            'rep': rep,
            'num_accounts': len(rep_accounts),
            'center_lat': center_lat,
            'center_lon': center_lon,
            'max_radius_miles': max_radius,
            'avg_distance_miles': avg_distance,
            'total_annual_travel_miles': travel_metrics['total_annual_miles'],
            'total_annual_travel_hours': travel_metrics['total_annual_hours'],
            'primary_region': primary_region,
            'region_concentration_pct': region_concentration * 100,
            'regions': regions
        })

    return pd.DataFrame(results)


def calculate_geographic_compactness(accounts_df):
    """
    Calculate how geographically compact a territory is.

    Compactness score:
    - 100 = Perfect (all accounts in same location)
    - 0 = Very spread out (accounts across country)

    Uses ratio of average distance to max possible distance.

    Parameters:
    -----------
    accounts_df : DataFrame
        Accounts with latitude, longitude columns

    Returns:
    --------
    float : Compactness score (0-100)
    """
    if len(accounts_df) <= 1:
        return 100

    center_lat, center_lon = calculate_territory_center(accounts_df)
    avg_distance = calculate_average_distance_to_center(accounts_df, center_lat, center_lon)

    # Max possible distance in continental US is ~3000 miles (coast to coast)
    MAX_DISTANCE = 3000

    # Score: higher when average distance is lower
    compactness = max(0, 100 * (1 - avg_distance / MAX_DISTANCE))

    return compactness


def find_nearest_accounts(account, accounts_df, n=5):
    """
    Find the N nearest accounts to a given account.

    Parameters:
    -----------
    account : Series
        Account with latitude, longitude
    accounts_df : DataFrame
        All accounts with latitude, longitude
    n : int
        Number of nearest accounts to find

    Returns:
    --------
    DataFrame : N nearest accounts with distances
    """
    distances = []
    for idx, other_account in accounts_df.iterrows():
        if account.name != idx:  # Skip self
            dist = haversine_distance(
                account['latitude'], account['longitude'],
                other_account['latitude'], other_account['longitude']
            )
            distances.append({
                'account_name': other_account['account_name'],
                'distance_miles': dist,
                'city': other_account['city'],
                'state': other_account['state']
            })

    # Sort by distance and return top N
    distances_df = pd.DataFrame(distances).sort_values('distance_miles')
    return distances_df.head(n)


def print_geographic_summary(geo_metrics_df):
    """
    Print a formatted summary of geographic metrics.

    Parameters:
    -----------
    geo_metrics_df : DataFrame
        Output from analyze_geographic_balance()
    """
    print("\n" + "="*80)
    print("GEOGRAPHIC TERRITORY ANALYSIS")
    print("="*80)

    for _, row in geo_metrics_df.iterrows():
        print(f"\n{row['rep']}:")
        print(f"  Accounts: {row['num_accounts']}")
        print(f"  Primary Region: {row['primary_region']} ({row['region_concentration_pct']:.1f}% of accounts)")
        print(f"  Territory Center: ({row['center_lat']:.2f}, {row['center_lon']:.2f})")
        print(f"  Max Radius: {row['max_radius_miles']:.1f} miles")
        print(f"  Avg Distance to Center: {row['avg_distance_miles']:.1f} miles")
        print(f"  Annual Travel: {row['total_annual_travel_miles']:,.0f} miles ({row['total_annual_travel_hours']:.0f} hours)")

    # Team summary
    print("\n" + "="*80)
    print("TEAM SUMMARY")
    print("="*80)
    print(f"Total Annual Travel: {geo_metrics_df['total_annual_travel_miles'].sum():,.0f} miles")
    print(f"Total Annual Travel Time: {geo_metrics_df['total_annual_travel_hours'].sum():,.0f} hours")
    print(f"Average Territory Radius: {geo_metrics_df['max_radius_miles'].mean():.1f} miles")
    print(f"Most Compact: {geo_metrics_df.loc[geo_metrics_df['avg_distance_miles'].idxmin(), 'rep']}")
    print(f"Most Spread Out: {geo_metrics_df.loc[geo_metrics_df['avg_distance_miles'].idxmax(), 'rep']}")


if __name__ == "__main__":
    # Test with geographic accounts data
    print("Loading accounts with geography...")
    df = pd.read_csv('accounts_with_geography.csv')

    print(f"Loaded {len(df)} accounts")

    # Analyze current geographic distribution
    geo_metrics = analyze_geographic_balance(df)
    print_geographic_summary(geo_metrics)

    # Save metrics
    geo_metrics.to_csv('geographic_metrics.csv', index=False)
    print("\n✓ Geographic metrics saved to geographic_metrics.csv")
