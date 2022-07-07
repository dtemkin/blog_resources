from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error
import numpy as np
import pandas as pd


def setX(df):
    x_cols = list(df.columns)
    x_cols.remove('Retail')
    x_cols.remove("Price")
    x_cols.remove("LogPrice")
    x_cols.remove("LogRetail")
    return df[x_cols]


def data_prep(df, y_col):
    X = setX(df)
    return train_test_split(X, df[y_col], train_size=.90, random_state=1111)

def fit_model(train_x, train_y, test_x, test_y, predict_type):
    # Instantiate Random Forest Model
    rforest_reg = RandomForestRegressor(n_estimators=1000, max_depth=10, random_state=123) #r2 = .83
    # Instantiate Gradient Boosting Model
    gboost_reg = GradientBoostingRegressor(n_estimators=1000, learning_rate=.1, subsample=.85, max_depth=10, max_features='log2', random_state=123) # r2 = .87
    # Instantiate Voting Meta Regressor
    mod = VotingRegressor(estimators=[('rf', rforest_reg), ("gb", gboost_reg)]) # r2 = .73

    
    # Fit model
    mod.fit(train_x, train_y)
    # Get Predictions
    y_pred = mod.predict(test_x)
    
    # For some reason, y_pred is not recognized as a vaild numpy array
    y_pred_arr = np.asarray(y_pred)
    y_actual = test_y.to_numpy()
    
    # Calculate Model Efficacy
    r_sq = r2_score(y_actual, y_pred_arr)
    corr = np.sqrt(r_sq)
    mae = mean_absolute_error(y_actual, y_pred)
    mape = mean_absolute_percentage_error(y_actual, y_pred)
    print(f"\n\n{predict_type} Model\n==========================\n")
    print(f"R-Squared: {r_sq}\nCorrelation: {corr}\nMAE: {mae}\nMAPE: {mape}")
    
    # Build dataframe with id's and predictions.
    predicted_df = pd.DataFrame({"id": test_x.index, predict_type: y_pred})
    return predicted_df, mod


def bid_math(df, price_limit, price_add):

    sorted_df = df.sort_values(by='predicted_retail', ascending=False)
    sorted_df['predicted_price'] += price_add
    
    if price_limit:
        sorted_df = sorted_df[sorted_df['predicted_price']<24000]
    
    tot = 0
    bids = []

    for ix in sorted_df.index:
        if tot+sorted_df['predicted_price'].loc[ix] < 5000000:
            bids.append(ix)
            tot+= sorted_df['predicted_price'].loc[ix]

        else:
            break


    trunc_df = sorted_df.loc[bids]
    profit = 0
    over_bids = [0]
    under_bids = [0]

    for t in trunc_df.index:
        prc_diff = trunc_df['predicted_price'].loc[t] - trunc_df['actual_price'].loc[t]
        prft = trunc_df['actual_retail'].loc[t] - trunc_df['predicted_price'].loc[t]
        if prc_diff > 0:
            profit += prft
            over_bids.append(prc_diff)
        elif prc_diff < 0:
            under_bids.append(prc_diff)
        else:
            profit += prft

    print(f"Num Bids: {len(trunc_df.index)} | Total Profit: {profit} \n#################\n\
    Over-Bids:\n\tCount: {len(over_bids)}\n\tTotal: {sum(over_bids)}\
    \n\tMax: {max(over_bids)}\n\tMin: {min(over_bids)}\n\tAvg: {np.mean(over_bids)}\
    \n#################\n\
    Under-Bids:\n\tCount: {len(under_bids)}\n\tTotal: {sum(under_bids)}\
    \n\tMax: {max(under_bids)}\n\tMin: {min(under_bids)}\n\tAvg: {np.mean(under_bids)}")

