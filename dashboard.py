import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource, Legend, GeoJSONDataSource, LinearColorMapper, ColorBar, Range1d
from bokeh.models import NumeralTickFormatter, HoverTool, LabelSet, Panel, Tabs, Slider, CustomJS, TapTool, CDSView
from bokeh.models.widgets import TableColumn, DataTable, NumberFormatter, Dropdown, Select, RadioButtonGroup, TableColumn
from bokeh.palettes import Category20c
from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Viridis6 as palette
from bokeh.transform import cumsum

def create_data(attr, old, new):
    """Create and modify data for the bokeh map"""

    # Mask data to the required year value
    chosen_year = year_slider.value
    df1 = geo_df1[geo_df1['year']==str(chosen_year)].copy()
    df2 = gen_df1.query('country.isin(@continents)')[gen_df1['year']==str(chosen_year)].copy()

    # Read data to json
    df_json = json.loads(df1[['country', 'country_code', 'geometry', 'technology', 'unit', 'year', 'percentage']].to_json())

    map_data = json.dumps(df_json)

    # Assign Source
    map_source.geojson = map_data
    bar_sc.data = df2

def ARPU(src):
    "Calculate Average Revenue per User"

    # Calculate average revenue per user
    chosen_country = country_slider.value
    df1 = geo_df1[geo_df1['country']==str(chosen_country)].copy()
    
    # Assign source
    map_source.geojson = map_data

def build_map(src):
    """Build map data"""

    # Data source
    map_source = src

    # Map Geometry
    color_mapper = LinearColorMapper(palette=colorcet.bgy, low=0, high=100)

    color_bar = ColorBar(color_mapper = color_mapper, location = (0,0))

    # Map
    TOOLS = "pan,wheel_zoom,reset,hover,save"

    map_all = figure(plot_width=725, plot_height=500,
                    title="Retail shopping from different countries",
                    tools=TOOLS, x_axis_location=None, y_axis_location=None,
                    tooltips = [
                        ("Country", "@Country"),
                        ("Revenue", "@Revenue")
                    ]
                )

    map_all.grid.grid_line_color = None
    map_all.hover.point_policy = "follow_mouse"

    # Create patches (of map)
    map_all.patches(
        "xs", "ys", source=map_source,
        fill_color={
            "field": 'Revenue',
            "transform": color_mapper
        },
        fill_alpha=0.7, line_color="black", line_width=0.5
    )

    map_all.add_layout(color_bar, 'below')

    return map_all

df = pd.read_csv(r'data/customer.xlsx')

# Map data
borders = 'mapping/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
gdf = gpd.read_file(borders)[['ADMIN', 'ADM0_A3', 'geometry']]

# Merge data with co-ordinates
geo_df = gdf.merge(df, left_on='country', right_on='Country', how='left')

# Read data to json
df_json = json.loads(geo_df1.query('year=="2010"')[
    ['country', 'country_code', 'geometry', 'technology', 'unit', 'year', 'percentage']
    ].to_json())

# Convert to string like object
map_data = json.dumps(df_json)

# Update chart
map_all = build_map(map_source)

cont_bar = bar_cont(bar_sc)

count_line = chart_time(time_sc)

ren_line = chart_energy(ren_sc)

curdoc().add_root(column(year_slider, map_all))
curdoc().title = 'Revenue generated worldwide from online retail shopping'

rc.log("Map created", style='yellow')
