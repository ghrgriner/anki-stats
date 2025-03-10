"""FSRS code
"""

import math
import pandas as pd

def add_current_retrievability(df: pd.DataFrame) -> pd.DataFrame:
    df['fsrs_base'] = (df.days_since_last_review / df.c_stability
                             * (19.0 / 85) + 1)
    df['fsrs_retrievability'] = df.fsrs_base.map(lambda x: math.pow(x, -0.5))

    return df

