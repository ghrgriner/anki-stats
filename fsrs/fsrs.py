"""FSRS code
"""

import math
import pandas as pd

FACTOR = 19 / 81
DECAY = -0.5

def add_current_retrievability(df: pd.DataFrame) -> pd.DataFrame:
    df['fsrs_base'] = (df.days_since_last_review / df.c_stability
                             * FACTOR + 1)
    df['fsrs_retrievability'] = df.fsrs_base.map(lambda x: math.pow(x, DECAY))

    return df

