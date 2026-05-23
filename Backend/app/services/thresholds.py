# Row volume: compare latest run to historical average (status) or prior run (alerts)
ROW_COUNT_WARNING_RATIO = 0.8
ROW_COUNT_CRITICAL_RATIO = 0.5

# Null completeness: relative increase in null rate vs previous run
NULL_RATE_WARNING_INCREASE = 0.20
NULL_RATE_CRITICAL_INCREASE = 0.50
NULL_RATE_MIN_DELTA = 0.01  # ignore noise below 1 percentage point

# Numeric columns: mean shift vs prior run std
MEAN_SHIFT_STD_MULTIPLIER = 3.0
MEAN_MIN_STD = 1e-9
