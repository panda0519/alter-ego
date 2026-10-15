import numpy as np
import datetime

# Physics constants from the Alter Ego guide
Sy = 0.10
alpha = 0.15
beta = 0.10
K = 5.0 # m/day

n_wells = 80
n_days = 900

print(f"Simulating {n_wells} wells over {n_days} days using guide physics...")

# Generate fake locations (roughly matching Uttar Pradesh coords) and elevations
lats = np.random.uniform(25.0, 27.0, n_wells)
lons = np.random.uniform(79.0, 81.0, n_wells)
elev = np.random.uniform(100, 150, n_wells)

# Generate 900 days of dates
start_date = datetime.date(2023, 1, 1)
dates = np.array([(start_date + datetime.timedelta(days=i)).isoformat() for i in range(n_days)])

# Generate weather (seasonal rain and ET)
days_array = np.arange(n_days)
# Sine wave for seasonality (peak monsoon)
season = np.sin(2 * np.pi * days_array / 365.25 - np.pi/2)
rain_prob = np.clip(season, 0, 1)[:, None]

# Rain and evaporation arrays (days x wells)
rain = np.random.binomial(1, rain_prob * 0.3, (n_days, n_wells)) * np.random.exponential(0.02, (n_days, n_wells))
et = np.random.uniform(0.002, 0.006, (n_days, n_wells)) * (1 + season[:, None]*0.5)

# Initialize depth array and fixed pumping rates per well
depth = np.zeros((n_days, n_wells))
depth[0] = np.random.uniform(10, 30, n_wells) # Starting depth between 10m and 30m
pumping = np.random.uniform(0.001, 0.003, n_wells) 

# Step forward in time using the exact water balance physics rule
for t in range(1, n_days):
    # Minor random neighbour flow that sums near zero
    neighbour_flow = np.random.normal(0, 0.0005, n_wells) 
    
    # Change in head = (water in - water out) / Sy
    delta_head = (alpha * rain[t] - beta * et[t] + neighbour_flow - pumping) / Sy
    
    # Head = Ground - Depth. Therefore, Change in Depth = - Change in Head
    depth[t] = depth[t-1] - delta_head

# Randomly drop 5% of readings to simulate broken sensors (NaN)
mask = np.random.rand(n_days, n_wells) < 0.05
depth[mask] = np.nan

# Save exactly as expected by Person B (features.py)
np.savez('bundle.npz', depth=depth, rain=rain, et=et, lat=lats, lon=lons, elev=elev, dates=dates)

print("✅ Success! Created bundle.npz in the exact format required for Plan B.")