import pandas as pd
import numpy as np

import random

__all__ = ["do_preprocesing","calculate_score"]

# Preprocessing to generate additional datapoints

def carbon_footprint(df):
    # https://timeforchange.org/co2-emissions-for-shipping-of-goods/ 
    # Values per metric tonne of freight
    
    lowerBound = 500*df['AirDistance'].values + 60*df['RoadDistance'] +  30*df['RailDistance'] +  10*df['PortDistance']
    upperBound = 500*df['AirDistance'] + 150*df['RoadDistance'] + 100*df['RailDistance'] + 40*df['PortDistance']

    return lowerBound, upperBound

# Time is also important
def approximate_time(df):
    return df['TotalDistance'].values/60

def normalize_values(df):

    n_df = df.copy(deep=True)

    # Normalization by maximum
    maxDist = n_df["TotalDistance"].max()
    distances = ["TotalDistance","AirDistance","RoadDistance","RailDistance","PortDistance"]

    for col in distances:
        n_df[col] = n_df[col]/maxDist

    # Normalization by maximum
    maxCarb = n_df["UpperCarbonApprox"]
    n_df["UpperCarbonApprox"] = n_df["UpperCarbonApprox"]/maxCarb
    n_df["LowerCarbonApprox"] = n_df["LowerCarbonApprox"]/maxCarb

    return n_df

def do_preprocesing(df):

    # Process raw route data
    lowerBound, upperBound = carbon_footprint(df)
    approxTime = approximate_time(df)

    df["LowerCarbonApprox"] = lowerBound
    df["UpperCarbonApprox"] = upperBound
    df["TimeApprox"] = approxTime

    # Create ramps
    df["UsesRail"] = df["RailDistance"] > 0
    df["UsesAir"] = df["AirDistance"] > 0
    df["UsesPort"] = df["PortDistance"] > 0

    return df

# Inplace score calculation
def calculate_score(df, weights):

    score_df = pd.DataFrame()

    # Make values are within 0 and 1
    n_df = normalize_values(df)

    for col in weights.keys():
        score_df[col] = n_df[col] * weights[col]

    df["Score"] = score_df.sum(1)
