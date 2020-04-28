from receipts import PLOTS_DIR
from receipts.preproc import Utils, Counter

import os
from plotly import io
import chart_studio.plotly as ply
from plotly import graph_objs as go
from plotly.subplots import make_subplots


class DataExploration(object):
    
    @classmethod
    def data(cls, x, grp, top_n=None):
        cx = Utils.counters(x, top_n=top_n)
        
        valid = ['Product Text (Parts)', 'Product Text (Split)', 
                 'Product Text (Chars)', "Retailers", 'Categories']
        
        try:
            data_idx = cx['name_idx'].index(grp)
        except KeyError:
            raise KeyError(f"Invalid group name {grp}. Not found in {valid}")
        else:
            counter = cx['counters'][data_idx]
            data_lst = counter['data']
            data_cnts = counter['counts']
            data_freqs = counter['frequencies']
        
        return data_lst, data_cnts, data_freqs
        
        
    
    @classmethod
    def plot2html(cls, fig, filename, **html_kwargs):
        incl_plotly = html_kwargs.pop("include_plotlyjs", False)
        full_html = html_kwargs.pop('full_html', False)
        ht = html_kwargs.pop('height', '750px')
        wd = html_kwargs.pop('width', '80%')

        _file = os.path.join(PLOTS_DIR, '%s.html' % filename)
        io.write_html(fig, file=_file,
                      full_html=full_html, include_plotlyjs=incl_plotly,
                      default_height=ht, default_width=wd, **html_kwargs)

    @classmethod
    def show_plot(cls, fig, filename):
        return ply.iplot(fig, filename=filename)
        
        
    @classmethod
    def bar(cls, data, grp, build_counters=True, show=True, 
            to_html=True, plt_type='freq',
            layout_opts='default', n=None,  **html_kwargs):
        typ = ('Frequency' if plt_type.lower()[0] == 'f' else 
               'Count' if plt_type.lower()[0] == 'c' else None)
        
        lay = go.Layout({"width": 750, "height": 500})
        if layout_opts == 'default':
            lay.update({"title_text": f'{grp} {typ}',
                        "xaxis": {"title": f'{grp}', "tickangle":45}})
            if typ is not None:
                lay.update({"yaxis_title_text": typ})
            else:
                raise ValueError("Invalid plot type must be 'freq' or 'count'")
        else:
            lay.update(**layout_opts)
        if build_counters:
            l, c, f = cls.data(data, grp, top_n=n)
        else:
            if typ == 'Frequency':
                f = data
            else:
                c = data
                
        hist_name = f'{grp} Bar Chart'
        if typ == 'Frequency':
            fig = go.Figure(data=[go.Bar(x=list(f.keys()), y=list(f.values()),
                                         name=hist_name, hoverinfo='x+y')],
                            layout=lay)
        else:
            fig = go.Figure(data=[go.Bar(x=list(c.keys()), y=list(c.values()),
                                         name=hist_name, hoverinfo='x+y')],
                            layout=lay)
        
        fname = f'{grp}_bar_{typ}'

        return fig, fname
    
    @classmethod
    def conditional_histogram(cls, data, grpX="Product Text (Split)", 
                              grpY="Categories", n=None):
        fname = f"{grpX}_by_{grpY}_condhist"
        # xx = ('product_text' if grpX.find("Product")>-1 else "retailer")
        # yy = "category"
        data_ = {}
        for dx in data: 
            if dx['category'] in data_:
                data_[dx['category']].extend(dx['product_text'].split(" "))
            else:
                
                data_.update({dx['category']: dx['product_text'].split(" ")})
        
        # fig = make_subplots(rows=2, cols=2, shared_yaxes='all', shared_xaxes='all', 
        #                    specs=[[{"rowspan": 2, "type": "histogram"}, 
        #                           {'rowspan': 2, 'type': 'table'}], 
        #                           [None, None]], horizontal_spacing=.1)
        fig = go.Figure()
        btns = []
        data_items = list(data_.items())
        for clx, dat in data_items:
            cnti = Counter(dat)
            cnttot = sum(cnti.values())
            cntfreqs = {c: cnti[c]/cnttot for c in cnti}
            tracex = go.Histogram(x=dat, name=clx + " keywords",
                                  visible=(True if clx == data_items[0][0]
                                           else False),
                                  hovertext=['%s: %s %%' %
                                             (x, str(round(cntfreqs[x]*100, 4)))
                                             for x in cntfreqs],
                                  hoverinfo='text')
            # if n is None:
            #    cnt_ord = sorted([(k, cnti[k]) for k in cnti], key=lambda x: x[1], reverse=True)
            #    cnttot2 = cnttot
            # else:
            #    cnt_ord = sorted([(k, cnti[k]) for k in cnti.most_common(n)], key=lambda x: x[1], reverse=True)
            #    cnttot2 = sum(cnt.most_common(n).values())
                
            # ks, vs, fs = [], [], []
            # for cx in cnt_ord:
            #     ks.append(cx[0])
            #     vs.append(cx[1])
            #     fs.append(round(cx[1]/cnttot2, 4))
            
            # trace_tab = go.Table(header={'values': ["Item", 'Count', 'Frequency']},
            #                     cells={"values": [ks, vs, fs],
            #                            "align": "left"}, 
            #                     visible=(True if clx == data_items[0][0]
            #                              else False))
            
            btnx = {"label": clx, 'method': 'update',
                    "args":[{'visible': [True if clx == tt[0] else False
                                         for tt in data_items]                
                            }]
                   }
            
            # fig.add_trace(tracex, row=1, col=1)
            # fig.add_trace(trace_tab, row=1, col=2)
            fig.add_trace(tracex)
            
            
            btns.append(btnx)

        fig.update_layout(
            {"updatemenus":[
                go.layout.Updatemenu(
                    buttons=btns,
                    direction="down",
                    pad={"r": 5, "t": 5},
                    showactive=True,
                    xanchor="right",
                    x=1.5,
                    yanchor="top",
                    y=1.10
                )],
                'title_text': 'Keyword Frequency by Class',
                'xaxis': dict(title='Keyword', tickangle=45),
                'yaxis_title_text': 'Count',
                "width": 900, "height": 700,
                "autosize": True
        })
        return fig, fname
        
    @classmethod
    def table(cls, data, grp, show=True, to_html=True, order_by='freq',
              layout_opts='default', n=None, **html_kwargs):
        order = ('Frequency' if order_by.lower()[0] == 'f' else 
                 'Count' if order_by.lower()[0] == 'c' else None)

        lay = go.Layout({"width": 750, "height": 500})
        if layout_opts == 'default':
            lay.update({"title_text": f"{grp} by {order}"})
        else:
            lay.update(**layout_opts)

        l, counts, freqs = cls.data(data, grp, top_n=n)

        _names = list(dict(counts).keys())
        _freqs = list(dict(freqs).values())
        _cnts = list(dict(counts).values())
        
        fig = go.Figure(
            data=[go.Table(header={'values': [f'{grp}', 'Count',
                                              'Frequency']},
                           cells={"values": [_names, _cnts, _freqs],
                                  "align": "left"})],
            layout=lay)
        
        fname = f'{grp}_table_by_{order}'
        
        return fig, fname
    
    @classmethod
    def subplots(cls, shape=(1, 2), *figs, **opts):
        f = make_subplots(rows=shape[0], cols=shape[1],
                          shared_yaxis=opts.pop("shared_yaxis", True),
                          horizontal_spacing=opts.pop("horizontal_spacing", .3),
                          specs=opts.pop('specs', [{"type": "histogram"}, 
                                                   {'type': "table"}]))
        
        f.add_trace(figs[0], row=1, col=1)
        f.add_trace(figs[1], row=1, col=2)
        return f
    
    @classmethod
    def plot(cls, *figs, **kwargs):
        show_ = kwargs.get('show', True)
        tohtml_ = kwargs.get("to_html", True)
        fnames = kwargs.get("fnames", ())
        for f in range(len(figs)):
            if tohtml_:
                try:
                    fname = fnames[f]
                except IndexError as err1:
                    raise IndexError("Insufficient filenames specified", err1)
                except TypeError as err2:
                    raise TypeError("'fnames' must be iterable", err2)
                else:
                    cls.plots2html(fig=figs[f], fname=fname,
                                   html_kwargs=kwargs.get("html_kwargs", {}))

            if show_:
                f.show()

                
