import pandas as pd
import numpy as np


def calculate_rel_volume(df, current_period=10, ref_period=50):
    df = df.copy()
    df['curr_volume'] = df['volume'].rolling(current_period).mean()
    df['ref_volume'] = df['volume'].rolling(ref_period).mean()
    df['rel_volume'] = df['curr_volume'] / df['ref_volume']
    return df['rel_volume'].to_list()