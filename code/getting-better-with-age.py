try:
  import plotly.offline as offline
except ImportError:
  raise ImportError("You need to install the plotly package using 'pip install plotly'")
else:
  import plotly.graph_objs as graph
offline.init_notebook_mode()



def AgeDifference(Age1, Age2, Max_Age=100):
    
    if Age1 < Age2:
        young = Age1
        old = Age2
        diff = old - young
        diffdesc = "older than you"
    elif Age1 > Age2:
        young = Age2
        old = Age1
        diff = young - old
        diffdesc = "younger than you"

    elif Age1 == Age2:
        young=Age1
        old=Age2
        diff = 0
        diffdesc = "the same age as you"
    rng = range(young, Max_Age)
    diffs = dict([(str(Year), (Year + abs(diff))/Year) for Year in rng])
    
    for i in range(Age1, len(diffs.keys()), 5):
        
        print("When You Are %s Your Partner will be %s which is %s times %s" % (i, i+diff, round(diffs[str(i)], 2), diffdesc))

    offline.plot({"data":[{"x": [k for k in diffs.keys()], 
                           "y":[v for v in diffs.values()]}], 
                  "layout":graph.Layout(xaxis=dict(title='Your Age'), 
                                        yaxis=dict(title='Age Multiple'), 
                                        title="Age Ratio")})
