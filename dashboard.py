import json
import pandas as pd
import logging
import geopandas as gpd
import python_calamine
from typing import IO, Iterator

from rich.logging import RichHandler

from bokeh.plotting import figure, output_file, show, curdoc
from bokeh.models import ColumnDataSource, Legend, GeoJSONDataSource, LinearColorMapper, ColorBar, Range1d
from bokeh.models import NumeralTickFormatter, HoverTool, LabelSet, Panel, Tabs, Slider, CustomJS, TapTool, CDSView
from bokeh.models.widgets import TableColumn, DataTable, NumberFormatter, Dropdown, Select, RadioButtonGroup, TableColumn
from bokeh.palettes import Category20c
from bokeh.io import curdoc, output_notebook, show, output_file
from bokeh.layouts import row, column, gridplot
from bokeh.palettes import Viridis6 as palette
from bokeh.transform import cumsum

FORMAT='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configuration for logging
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

# Assign logger
log = logging.getLogger('rich')

# File output settings
FileOut = logging.FileHandler('app.log')

log.addHandler(FileOut)

year_slider = Slider(title="Select Year", value=2010, start=2010, end=2012)

count_sel = Select(
    title="Select Continent", 
    value="USA", 
    options=[
    'United Kingdom', 'France', 'Australia', 'Netherlands', 'Germany',
    'Norway', 'EIRE', 'Switzerland', 'Spain', 'Poland', 'Portugal',
    'Italy', 'Belgium', 'Lithuania', 'Japan', 'Iceland',
    'Channel Islands', 'Denmark', 'Cyprus', 'Sweden', 'Austria',
    'Israel', 'Finland', 'Bahrain', 'Greece', 'Hong Kong', 'Singapore',
    'Lebanon', 'United Arab Emirates', 'Saudi Arabia',
    'Czech Republic', 'Canada', 'Unspecified', 'Brazil', 'USA',
    'European Community', 'Malta', 'RSA'
    ])

def iter_ec(file: IO[bytes]) -> Iterator[dict[str, object]]:
    workbook = python_calamine.CalamineWorkbook.from_filelike(file)
    rows = iter(workbook.get_sheet_by_index(0).to_python())
    headers = list(map(str, next(rows)))
    for row in rows:
        yield dict(zip(headers, row))

def load_data(file_path):
    with open(file_path, 'rb') as f:
        rows = iter_ec(f)
        row = list(rows)
    df = pd.DataFrame(row)
    return df

def create_data(attr, old, new):
    """
    Create and modify data for the bokeh map
    """
    # Mask data to the required year value
    chosen_year = year_slider.value
    df1 = geo_df[geo_df['year']==str(chosen_year)].copy()

    # Read data to json
    df_json = json.loads(df1[['country', 'country_code', 'geometry', 'technology', 'unit', 'year', 'percentage']].to_json())

    map_data = json.dumps(df_json)

    # Assign Source
    map_source.geojson = map_data

    log.info("Year changed to @chosen_year")

def ARPU(attr, old, new):
    """
    Calculate Average Revenue per User
    """

    # Calculate average revenue per user
    chosen_country = count_sel.value
    df1 = geo_df[geo_df['country']==str(chosen_country)].copy()
    
    # Assign source
    map_source.geojson = map_data

def build_map(src):
    """
    Build map data
    """

    
    return map_all

def main():
    """
    Main function to load data and process the map data
    """
    log.info('Session started')  # Log that the session has starte
    try:
        # Load data
        df1 = load_data(r'data/customer.xlsx')

        # Preprocessing country names for merge
        rename_country = {
        'EIRE': 'Ireland',
        'USA': 'United States of America',
        'RSA': 'South Africa',
        'Czech Republic': 'Czechia'
        }

        isles = [
        'Bahrain', 
        'Singapore', 
        'Hong Kong', 
        'Malta', 
        'Channel Islands', 
        'European Community',
        'Unspecified'
        ]

        df1['Country'] = df1['Country'].apply(lambda x: rename_country.get(x, x))

        isles_df = df1.query('Country.isin(@isles)')

        df1 = df1.query('~Country.isin(@isles)').copy()

        df1['Revenue'] = df1['UnitPrice']*df1['Quantity']

        df1['year'] = df1['InvoiceDate'].dt.year

        df = df1.groupby(['Country', 'year'])[['Quantity', 'Revenue']].sum().reset_index()

        df.columns = ['country', 'year', 'Quantity', 'Revenue']

        # Load Map data
        borders = 'mapping/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'
        gdf = gpd.read_file(borders)[['ADMIN', 'ADM0_A3', 'geometry']]

        # Rename columns
        gdf.columns = ['country', 'country_code', 'geometry']

        # Merge data with co-ordinates
        global geo_df
        geo_df = gdf.merge(df, left_on='country', right_on='country', how='right')

        # Read data to json
        df_json = json.loads(geo_df.query('year==2010')[
             ['country', 'country_code', 'geometry', 'year', 'Quantity', 'Revenue']
             ].to_json())

        # Convert to string like object
        map_data = json.dumps(df_json)

        # Assign Source
        global map_source
        map_source = GeoJSONDataSource(geojson = map_data)

        year_slider.on_change('value', create_data)

        count_sel.on_change('value', ARPU)

        # Update chart
        # Map Geometry
        color_mapper = LinearColorMapper(palette=palette[::-2], low=0, high=100)

        color_bar = ColorBar(color_mapper = color_mapper, location = (0,0))

        # Map
        TOOLS = "pan,wheel_zoom,reset,hover,save"

        map_all = figure(plot_width=725, plot_height=500,
                        title="Retail shopping from different countries",
                        tools=TOOLS, x_axis_location=None, y_axis_location=None,
                        tooltips = [
                            ("Country", "@country"),
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

        log.info("Map created")

        curdoc().add_root(column(row(year_slider, count_sel), map_all))
        curdoc().title = 'Revenue generated worldwide from online retail shopping'

    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    main()