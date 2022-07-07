from utils import abs2rel, sort_bins
from string import ascii_uppercase
import seaborn as sns
from matplotlib import pyplot as plt
from tabulate import tabulate
import pandas as pd
import numpy as np

valid_colors = list(ascii_uppercase)[3:]

    # Start with all 0's so each characteristic has the same items across vendors.

def build_table(df):
    df.insert(len(df.columns), 'Profit', 
              df['Retail']-df['Price'])
    vendor_cnts = df['Vendor'].value_counts()
    # Pivot Table For Vendors x (Avg. Price, Avg. Retail, Avg. Profit)
    tab = pd.pivot_table(df, values=['Price', 'Retail', "Profit"], 
                         index=['Vendor'], aggfunc={"Price": np.mean,
                                                    "Retail": np.mean,
                                                    "Profit": np.mean})

    # ASCII Table
    tabarr = tab.to_numpy()
    tt = []
    for t in range(len(tabarr)):
        # Add Vendor ID, and Items Sold by Vendor
        arr = list(tabarr[t])
        arr.insert(0, t+1)
        arr.insert(len(arr), vendor_cnts[t+1])
        tt.append(arr)
    return tabulate(tt, headers=["Vendor", 'Price', 'Retail', 
                                 "Profit", "Count"])


def vendor_diamond_bins(data):
    # copy base dictionaries
    clarity = {k: 0 for k in
                list(data['Clarity'].unique())}
    color = {k: 0 for k in
                  list(data['Color'].unique()) 
                  if k in valid_colors}
    regions = {k: 0 for k in
                   list(data['Regions'].unique())}
    shape = {k: 0 for k in
                  list(data['Shape'].unique())}
    polish = {k: 0 for k in
                   list(data['Polish'].unique())}
    symmetry = {k: 0 for k in
                     list(data['Symmetry'].unique())}

    
    # Calculate vendor specific distribution for each characteristic
    clarity_cnts = dict(data['Clarity'].value_counts())
    color_cnts = {c: v for c, v in data['Color'].value_counts().items() 
                  if c in valid_colors}
    regions_cnts = dict(data['Regions'].value_counts())
    shape_cnts = dict(data['Shape'].value_counts())
    polish_cnts = dict(data['Polish'].value_counts())
    symmetry_cnts = dict(data['Symmetry'].value_counts())
    
    # Create bins for Profit and Carats
    profit_bins = pd.cut(data['Profit'], bins=8) 
    profit_bins_cnt = profit_bins.value_counts()
    profit_bins_dict = {k: profit_bins_cnt[k] for k in
                        sort_bins(profit_bins)}
    carat_bins = pd.cut(data['Carats'], bins=10)
    carat_bins_cnt = carat_bins.value_counts()
    carat_bins_dict = {k: carat_bins_cnt[k] for k in 
                       sort_bins(carat_bins)}
    
    # Update vendor dicts
    clarity.update(clarity_cnts)
    color.update(color_cnts)
    regions.update(regions_cnts)
    shape.update(shape_cnts)
    polish.update(polish_cnts)
    symmetry.update(symmetry_cnts)
    
    
    return {"clarity": {"keys": list(clarity.keys()), 
                        'pcts': abs2rel(clarity)},
            "color": {"keys": list(color.keys()), 
                      "pcts": abs2rel(color)},
            "regions": {"keys": list(regions.keys()), 
                        "pcts": abs2rel(regions)},
            "shape": {"keys": list(shape.keys()), 
                      'pcts': abs2rel(shape)},
            "polish": {"keys": list(polish.keys()), 
                       'pcts': abs2rel(polish)},
            "profit": {"keys": list(profit_bins_dict.keys()), 
                       'pcts': abs2rel(profit_bins_dict)},
            "symmetry": {"keys": list(symmetry.keys()), 
                         'pcts': abs2rel(symmetry)},
            "carat": {"keys": list(carat_bins_dict.keys()), 
                      'pcts': abs2rel(carat_bins_dict)}}

def vendor_charbars(df, ttl, vendors=[1, 2, 3, 4], chars=8, max_profit=0):
    fig1, axes1 = plt.subplots(len(vendors), chars, figsize=(35,15))
    fig1.suptitle(ttl, 
                  size=24)

    # For each vendor --
    for vend in vendors:

        # Get the data that pertains to that vendor and results in a profit.
        vdata = df[(df['Vendor']==vend) & (df['Profit'] > max_profit)]

        dcts = vendor_diamond_bins(vdata)

        # Build bar charts for each of the charateristics
        sns.barplot(x=dcts['carat']['keys'], y=dcts['carat']['pcts'],
                    ax=axes1[vend-1, 0], color="Purple")
        sns.barplot(x=dcts['clarity']['keys'], 
                    y=dcts['clarity']['pcts'], 
                    ax=axes1[vend-1, 1], color='LightBlue')
        sns.barplot(x=dcts['color']['keys'], 
                    y=dcts['color']['pcts'], ax=axes1[vend-1, 2], 
                    color='LightGreen')
        sns.barplot(x=dcts['regions']['keys'], 
                    y=dcts['regions']['pcts'], 
                    ax=axes1[vend-1, 3], color='Gray')
        sns.barplot(x=dcts['shape']['keys'], 
                    y=dcts['shape']['pcts'], 
                    ax=axes1[vend-1, 4], color='DarkRed')
        sns.barplot(x=dcts['polish']['keys'], 
                    y=dcts['polish']['pcts'], 
                    ax=axes1[vend-1, 5], color='Orange')
        sns.barplot(x=dcts['symmetry']['keys'], 
                    y=dcts['symmetry']['pcts'], 
                    ax=axes1[vend-1, 6], color="DarkGreen")
        sns.barplot(x=dcts['profit']['keys'], 
                    y=dcts['profit']['pcts'], 
                    ax=axes1[vend-1, 7], color="DarkBlue")

        # Tweak the axis angle for some characteristics
        axes1[vend-1, 0].set_xticks(axes1[vend-1, 0].get_xticks(),
                                    axes1[vend-1, 0].get_xticklabels(),
                                    rotation=20, ha='right')    
        axes1[vend-1, 3].set_xticks(axes1[vend-1, 3].get_xticks(), 
                                    axes1[vend-1, 3].get_xticklabels(),
                                    rotation=20, ha='right')
        axes1[vend-1, 4].set_xticks(axes1[vend-1, 4].get_xticks(), 
                                    axes1[vend-1, 4].get_xticklabels(),
                                    rotation=20, ha='right')
        axes1[vend-1, 6].set_xticks(axes1[vend-1, 6].get_xticks(), 
                                    axes1[vend-1, 6].get_xticklabels(),
                                    rotation=20, ha='right')
        axes1[vend-1, 7].set_xticks(axes1[vend-1, 7].get_xticks(), 
                                    axes1[vend-1, 7].get_xticklabels(),
                                    rotation=20, ha='right')
    plt.subplots_adjust(top = 0.90, bottom=0.01, 
                        hspace=.65, wspace=0.33)
    # Label x axes
    plt.setp(axes1[-1, 0], xlabel="Carat")
    plt.setp(axes1[-1, 1], xlabel="Clarity")
    plt.setp(axes1[-1, 2], xlabel="Color")
    plt.setp(axes1[-1, 3], xlabel="Regions")
    plt.setp(axes1[-1, 4], xlabel="Shape")
    plt.setp(axes1[-1, 5], xlabel="Polish")
    plt.setp(axes1[-1, 6], xlabel="Symmetry")
    plt.setp(axes1[-1, 7], xlabel="Profit")
    # Label y axes
    for i in range(len(vendors)):
        
        plt.setp(axes1[i, 0], ylabel=f"Vendor {vendors[i]}")

    plt.savefig(ttl+".png")
    return plt


def retail_carat_scat(df):
    fig3, ax3 = plt.subplots()
    fig3.suptitle("Retail x Carats", size=24)
    sns.scatterplot(x=df['Carats'],
                    y=df['Retail'])

    fig3.savefig("Retail x Carats.png")
    


def retail_cost_kde(df):
    profit_rat = df["Retail"]/df["Price"]
    fig4, ax4 = plt.subplots()
    ax4.set_xlabel("Retail/Price Ratio")
    sns.histplot(profit_rat, ax=ax4)
    ax4x = ax4.twinx()
    sns.kdeplot(profit_rat, ax=ax4x)
    fig4.suptitle("Retail/Price Ratio", size=18)
    fig4.savefig("Retail_Price_Ratio.png")
    return fig4

###########################################################
def vendor1_charbars(df):
    fig2, axes2 = plt.subplots(1, 6, figsize=(30,10))
    fig2.suptitle("Diamond Characteristics for\
    (Vendor 1 & Profit > 3600)", size=24)

    # Repeat process only with Vendor 1 and Diamonds that resulted in a $3600 Profit (Greater than average) 
    vend1_data = df[(df['Vendor']==1) & 
                    (df['Profit'] > 3600)]

    dcts = vendor_diamond_bins(vend1_data)


    sns.barplot(x=dcts['clarity']['keys'], y=dcts['clarity']['pcts'], ax=axes2[0], color='LightBlue')
    sns.barplot(x=dcts['color']['keys'], y=dcts['color']['pcts'], ax=axes2[1], color='LightGreen')
    sns.barplot(x=dcts['regions']['keys'], y=dcts['regions']['pcts'], ax=axes2[2], color='Gray')
    sns.barplot(x=dcts['shape']['keys'], y=dcts['shape']['pcts'], ax=axes2[3], color='DarkRed')
    sns.barplot(x=dcts['polish']['keys'], y=dcts['polish']['pcts'], ax=axes2[4], color='Orange')
    sns.barplot(x=dcts['symmetry']['keys'], y=dcts['symmetry']['pcts'], ax=axes2[5], color="DarkGreen")
    #sns.barplot(x=list(profit_bins.keys()), y=[v/sum(profit_bins.values()) for v in profit_bins.values()], ax=axes2[5])


    axes2[2].set_xticks(axes2[2].get_xticks(), axes2[2].get_xticklabels(), rotation=20, ha='right')
    axes2[3].set_xticks(axes2[3].get_xticks(), axes2[3].get_xticklabels(), rotation=20, ha='right')


    plt.setp(axes2[0], xlabel="Clarity")
    plt.setp(axes2[1], xlabel="Color")
    plt.setp(axes2[2], xlabel="Regions")
    plt.setp(axes2[3], xlabel="Shape")
    plt.setp(axes2[4], xlabel="Polish")
    plt.setp(axes2[5], xlabel="Symmetry")
    plt.savefig("Diamond Characteristics (Vendor 1 & Profit over 3600).png")

