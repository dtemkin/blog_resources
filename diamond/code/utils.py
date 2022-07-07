
def abs2rel(dct):
    return [v/sum(dct.values()) for v in dct.values()]

def sort_bins(bin_col):
    """
    Sorts bins after using pd.cut. Increasing order. Puts "NaN" bin at the beginning. 

    """
    vals = {}
    for i, item in enumerate(bin_col.unique()):
        if str(item) == "nan":
            vals[i] = -99999
        else:
            vals[i] = float(str(item).split(",")[0][1:])
    ixs = list({k: v for k, v in \
                    sorted(vals.items(), 
                           key=lambda item: item[1])}.keys())
    sorted_bins = bin_col.unique()[list(ixs)]
    return sorted_bins