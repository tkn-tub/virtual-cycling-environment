#!/usr/bin/env python3

import pandas as pd
import math


df = pd.read_csv("log.csv")
df['speed_mps'] = df.spokes_per_s * 0.7 * math.pi / 18
df['speed_kph'] = df.speed_mps * 3.6
ax = df.plot(
    x='time_s',
    y='speed_kph',
    kind='line',
)
fig = ax.get_figure()
fig.tight_layout()
fig.savefig('fig.pdf')

