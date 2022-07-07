import pandas as pd

def _dimension2parts(m):
    '''Split l, w, h into separate components'''
    if m.find("x") > -1:
        l, w, h = m.split("x")
    elif m.find("*") > -1:
        l, w, h = m.split("*")
    else:
        l, w, h = None, None, None
    return float(l), float(w), float(h)

def _depthpct(l, w, h):
    """Calculate depth percentage"""
    # There are several instances where Depth in the dataset is N/A but the dimension is provided.
    
    if l == -1:
        depth_pct = None
    else:
        depth_pct = h/((l+w)/2)
    return depth_pct

def _tablesize(l, w, h, tab_pct):
    '''Calculate Table Width.'''
    # Calculate the width of the table when the table percent and dimensions are not NA.
    if l == -1 or tab_pct == -1:
        tabsize = None
    else:
        tabsize = tab_pct*w
    return tabsize
        
def split_measurements(df) -> pd.DataFrame:
    """Separate Meaurements Column into component parts and perform added table and depth calculations"""
    l_mm, w_mm, h_mm = [], [], []
    table_width = []
    table_pct = []
    depth_pct = []
    
    for idx in df.index:
        meas = df.loc[idx]['Measurements']
        tab_pct = df.loc[idx]['Table']
        # Dims
        l, w, h = _dimension2parts(meas)
        
        # Depth Percent
        d_pct = _depthpct(l, w, h)
        
        # Table Calculations
        tab_size = _tablesize(l, w, h, tab_pct/100.)
        table_pct.append((tab_pct/100. if not pd.isna(tab_pct) 
                          else None))
        table_width.append((tab_size if not pd.isna(tab_size) 
                            else None))
        
        
        l_mm.append(l)
        w_mm.append(w)
        h_mm.append(h)
        depth_pct.append(d_pct)
    
    # Add new fields to dataframe.
    df.insert(1, 'l_mm', l_mm)
    df.insert(2, 'w_mm', w_mm)
    df.insert(3, 'h_mm', h_mm)
    df.insert(4, 'depth_pct', depth_pct)
    df.insert(5, 'table_width', table_width)
    df.insert(6, 'table_pct', table_pct)
    depth_diffs = depth_pct - (df['Depth']/100.)
    # print(max(depth_diffs), min(depth_diffs), np.mean(depth_diffs), depth_diffs)
    df.drop(["Depth", "Measurements", "Table"], axis=1, inplace=True)
    
    return df


def make_dummies(df, cols): 
    """Create Dummy Variables for categorical columns"""
    cat_df = pd.get_dummies(df[list(cols)], dummy_na=True)
    df.drop(cols, axis=1, inplace=True)
    # Due to numeric value of Vendor column, dummy variables needed to be created explicitly.
    df.insert(len(df.columns), 'Vendor_1', [(1 if v==1 else 0) 
                                            for v in df['Vendor']])
    df.insert(len(df.columns), 'Vendor_2', [(1 if v==2 else 0) 
                                            for v in df['Vendor']])
    df.insert(len(df.columns), 'Vendor_3', [(1 if v==3 else 0) 
                                            for v in df['Vendor']])
    df.insert(len(df.columns), 'Vendor_4', [(1 if v==4 else 0) 
                                            for v in df['Vendor']])
    # Remove the original Vendor Column
    df.drop("Vendor", axis=1, inplace=True)
    df = df.join(cat_df)

    return df

def transcode_vars(df, cols):
    
    '''Convert variables to numeric representations.'''

    for col in cols:
        vals = []
        if col == 'Clarity':
            map_ = {"FL": 6, "IF": 5, "VVS1": 4.5, "VVS2": 4, "VS1": 3.5, 
                    "VS2": 3, "SI1": 2.5, "SI2": 2, "I1": 1.5, "I2": 1, "I3": .5, pd.NA: 0, " ": 0}
        else:
            map_={"Excellent": 5, "Very Good": 4,
                  "Good": 3, "Fair": 2, "Poor": 1, 
                  pd.NA: 0, " ": 0}
        for d in df[col]:
            if d in map_:
                vals.append(map_[d])
            else:
                vals.append(0)
        
        df.drop(col, axis=1, inplace=True)
        df.insert(len(df.columns), col, vals)
        
    return df


def transform_df(df):
    """Common transformation function combining previous steps with some added cleaning"""
    # df.drop("Known_Conflict_Diamond", axis=1, inplace=True) 
    # Drop column due to number of N/As in testing set.
    
    # Replace index with id
    df.index=df['id']
    df.drop('id', axis=1, inplace=True)
    
    # Correct misspellings and variations in spelling.
    df['Shape'] = [(i.lower().strip() if i != "Marquis" 
                    else "marquise") for i in df['Shape']]
    df['Color'] = [i.strip() if len(i.strip()) == 1 else i[0].strip() 
                   for i in df['Color']]
    df['Clarity'] = [(pd.NA if c == "None" or c is None else 
                      c.replace("Very good", "Very Good")) for c in
                     df['Clarity']]  
    df['Polish'] = [(pd.NA if p == " " else 
                     p.replace("Very good", "Very Good")) 
                    for p in df['Polish']]
    df['Cut'] = [(pd.NA if cx == " " else 
                  cx.replace("Very good", "Very Good")) 
                 for cx in df['Cut']]
    df['Symmetry'] = [s.replace('Execllent', 'Excellent').
                      replace("Very good", "Very Good") 
                      for s in df['Symmetry']]
    
    df = split_measurements(df)
    
    # Remove items that do not fit or are not represented in both the training and testing sets.
    df.drop(df.loc[df['Symmetry']=='Faint'].index, 
            axis=0, inplace=True)
    df.drop(df.loc[df['Cut']=='Ideal'].index, 
            axis=0, inplace=True)
    df.drop(df.loc[df['Clarity'].isin(['FL', 'I3'])].index, 
            axis=0, inplace=True)
    df.drop(df.loc[df['Color'].isin(['U', 'W', 'T'])].index, 
            axis=0, inplace=True)
    
    df.insert(len(df.columns), 'Profit', df['Retail']-df['Price'])
    
    
    return df


