import pandas as pd
import numpy as np
import folium
from urllib.request import urlopen
import json
from shapely.geometry import Polygon, Point
import random
import itertools

# import folium.plugins
from folium.plugins import MarkerCluster


TOTAL_ACCOUNTS = 100000
TOTAL_REVENUE = 17.77
TIER_A_COUNTIES_NUM = 86


state_geo = "https://raw.githubusercontent.com/martinjc/UK-GeoJSON/master/json/administrative/gb/lad.json"
with urlopen(state_geo) as response:
    data = json.load(response)

# create df_tier dataframe
d = {
    "A": {"% Revenue": 22.1, "% of accounts": 4.2},
    "B": {"% Revenue": 26.3, "% of accounts": 10.0},
    "C": {"% Revenue": 33.7, "% of accounts": 36.2},
    "D": {"% Revenue": 15.8, "% of accounts": 44.8},
    "E": {"% Revenue": 2.1, "% of accounts": 4.8},
}

df_tier = pd.DataFrame.from_dict(d, orient="index")
df_tier["# of accounts"] = (
    (df_tier["% of accounts"] * TOTAL_ACCOUNTS) / 100
).astype(int)
df_tier["Revenue ($M)"] = round(
    (df_tier["% Revenue"] * TOTAL_REVENUE) / 100, 2
)
df_tier.to_csv("df_tier.csv")

# create df_product_tier dataframe

d = {
    "A": {
        "product_id": ["TV_1", "TV_2", "BR_1"],
        "% Accounts": [0.008, 0.024, 0.01],
        "% Revenue": np.array([0.4, 0.4, 0.2])
        * (float(df_tier.loc[df_tier.index == "A", "% Revenue"]) / 100),
    },
    "B": {
        "product_id": ["TV_3", "BR_2", "MB_1"],
        "% Accounts": [0.042, 0.02, 0.038],
        "% Revenue": np.array([0.5, 0.4, 0.1])
        * (float(df_tier.loc[df_tier.index == "B", "% Revenue"]) / 100),
    },
    "C": {
        "product_id": ["TV_4", "BR_3", "MB_2"],
        "% Accounts": [0.052, 0.108, 0.202],
        "% Revenue": np.array([0.35, 0.45, 0.2])
        * (float(df_tier.loc[df_tier.index == "C", "% Revenue"]) / 100),
    },
    "D": {
        "product_id": ["TV_5", "BR_4", "MB_3"],
        "% Accounts": [0.032, 0.086, 0.33],
        "% Revenue": np.array([0.3, 0.4, 0.3])
        * (float(df_tier.loc[df_tier.index == "D", "% Revenue"]) / 100),
    },
    "E": {
        "product_id": ["BR_5", "MB_4", "MB_5"],
        "% Accounts": [0.01, 0.025, 0.013],
        "% Revenue": np.array([0.7, 0.15, 0.15])
        * (float(df_tier.loc[df_tier.index == "E", "% Revenue"]) / 100),
    },
}

df_product_tier = pd.DataFrame.from_dict(d, orient="index")
df_product_tier = df_product_tier.explode(list(df_product_tier.columns))
df_product_tier["% Revenue"] = df_product_tier["% Revenue"].astype("float")
df_product_tier["accounts"] = (
    df_product_tier["% Accounts"] * TOTAL_ACCOUNTS
).astype(int)

df_product_tier.to_csv("df_product_tier.csv")

# create df_avg_salary dataframe
df_avg_salary = pd.read_excel(
    "regionalgrossdisposablehouseholdincomeallitlregions.xls",
    sheet_name="Table 3",
    skiprows=1,
    usecols=["ITL level", "ITL code", "Region name", "2020"],
)

df_lookup = pd.read_csv(
    "Local_Authority_District_(December_2013)_to_NUTS3_to_NUTS2_to_NUTS1_(January_2015)_Lookup_in_the_UK.csv"
).dropna()

df_avg_salary = df_avg_salary.loc[df_avg_salary["ITL level"] == "ITL3"]

# create df_comb which is a combination of lookup table to df_salary table
df_comb = df_lookup[["LAD13CD", "NUTS315NM", "NUTS215NM"]].merge(
    df_avg_salary, left_on="NUTS315NM", right_on="Region name"
)

data_lst = []
for i in range(len(data["features"])):
    data_lst.append((i, data["features"][i]["properties"]["LAD13CD"]))

df_comb = df_comb.merge(pd.DataFrame(data_lst, columns=["idx", "LAD13CD"]))

df_comb.sort_values(by="2020", ascending=False, inplace=True)
# df_comb = df_comb.reset_index(drop=True)

df_comb["% Tier A Customers"] = np.append(
    np.exp(np.linspace(0.3, 0.0, TIER_A_COUNTIES_NUM)),
    np.zeros(int(len(df_comb) - TIER_A_COUNTIES_NUM)),
)

df_comb["# Tier A Customers"] = round(
    df_comb["% Tier A Customers"]
    * df_tier.loc[df_tier.index == "A", "# of accounts"].values[0]
    / 100
).astype(int)


m = folium.Map(location=[51, 3], zoom_start=5)
mCluster = MarkerCluster(name="Tier A Customers", show=False).add_to(m)
# fg = folium.FeatureGroup(name="Tier A Customers", show=False).add_to(m)

folium.Choropleth(
    geo_data=state_geo,
    data=df_comb,
    columns=["LAD13CD", "2020"],
    key_on="feature.properties.LAD13CD",
    fill_color="RdYlBu",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Avg Salary",
    highlight=True,
).add_to(m)


def flatten_nested_lists(lst):
    while any(isinstance(i, list) for i in lst):
        lst_old = lst
        lst = lst[0]

    return list(map(tuple, lst_old))


def polygon_random_points(poly, num_points):
    min_x, min_y, max_x, max_y = poly.bounds

    points = []

    while len(points) < num_points:
        random_point = Point(
            [random.uniform(min_x, max_x), random.uniform(min_y, max_y)]
        )
        if random_point.within(poly):
            points.append(random_point)
    return points


df_slice = df_comb[["idx", "# Tier A Customers"]].loc[
    df_comb["# Tier A Customers"] != 0
]

coor = []
for i in range(len(df_slice)):
    idx = df_comb.iloc[i]["idx"]
    coor_lst = data["features"][idx]["geometry"]["coordinates"][0]
    coor.append(flatten_nested_lists(coor_lst))
    poly = Polygon(list(itertools.chain(*coor)))
    account_num = df_slice.iloc[i]["# Tier A Customers"]

    points = polygon_random_points(poly, account_num)
    for p in points:
        # print(p.x, ",", p.y)

        # folium.CircleMarker(
        #     location=[p.y, p.x],
        #     radius=1.0,
        #     color="green",
        #     fill=True,
        #     fill_color="green",
        #     fill_opacity=0.4,
        # ).add_to(m)

        # fg.add_child(
        #     folium.CircleMarker(
        #         location=[p.y, p.x],
        #         radius=1.0,
        #         color="green",
        #         fill=True,
        #         fill_color="green",
        #         fill_opacity=0.5,
        #     )
        # )
        # m.add_child(fg)

        marker = folium.CircleMarker(
            location=[p.y, p.x],
            radius=1.0,
            color="purple",
            fill=True,
            fill_color="purple",
            fill_opacity=0.4,
        )
        mCluster.add_child(marker)

folium.LayerControl().add_to(m)

# m.save("customer_tier_map.html")
