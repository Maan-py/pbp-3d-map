import numpy as np
from scipy.interpolate import griddata

def calculate_grid(df, points=100):
    """
    Menghitung grid interpolasi dari data poin.
    
    Args:
        df: DataFrame dengan kolom X, Y, Z
        points: Jumlah titik grid per dimensi
        
    Returns:
        tuple: (grid_x, grid_y, grid_z)
    """
    df_unique = df.groupby(['X', 'Y'], as_index=False)['Z'].mean()
    grid_x = np.linspace(df['X'].min(), df['X'].max(), points)
    grid_y = np.linspace(df['Y'].min(), df['Y'].max(), points)
    grid_x, grid_y = np.meshgrid(grid_x, grid_y)

    try:
        grid_z = griddata(
            (df_unique['X'], df_unique['Y']),
            df_unique['Z'],
            (grid_x, grid_y),
            method='cubic'
        )
    except Exception:
        grid_z = griddata(
            (df_unique['X'], df_unique['Y']),
            df_unique['Z'],
            (grid_x, grid_y),
            method='linear'
        )
        
    return grid_x, grid_y, grid_z

def calculate_volumes(grid_z, x_range, y_range, goc, woc, nx=100, ny=100):
    """
    Menghitung volume reservoir.
    
    Args:
        grid_z: Grid kedalaman
        x_range: Tuple (min, max) untuk X
        y_range: Tuple (min, max) untuk Y
        goc: Gas-Oil Contact
        woc: Water-Oil Contact
        nx: Jumlah grid points X
        ny: Jumlah grid points Y
        
    Returns:
        tuple: (vol_total_res, vol_gas_cap, vol_oil_zone)
    """
    dx = (x_range[1] - x_range[0]) / (nx - 1)
    dy = (y_range[1] - y_range[0]) / (ny - 1)
    cell_area = dx * dy
    
    # Volume di atas WOC (Total Reservoir)
    thick_above_woc = woc - grid_z
    thick_above_woc[thick_above_woc < 0] = 0
    vol_total_res = np.nansum(thick_above_woc) * cell_area
    
    # Volume di atas GOC (Gas Cap)
    thick_above_goc = goc - grid_z
    thick_above_goc[thick_above_goc < 0] = 0
    vol_gas_cap = np.nansum(thick_above_goc) * cell_area
    
    # Volume Oil = selisih
    vol_oil_zone = max(0, vol_total_res - vol_gas_cap)
    
    return vol_total_res, vol_gas_cap, vol_oil_zone

def calculate_reserves(vol_oil_zone, vol_gas_cap, ntg, porosity, sw, bo, bg):
    """
    Menghitung STOIIP dan GIIP.
    
    Returns:
        tuple: (stoiip, giip)
    """
    stoiip = (vol_oil_zone * ntg * porosity * (1 - sw)) / bo
    giip = (vol_gas_cap * ntg * porosity * (1 - sw)) / bg
    return stoiip, giip
