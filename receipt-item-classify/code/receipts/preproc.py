from receipts import DATA_DIR
from receipts.enc import Encoders
from mypyutils import itertoolsx as it

from sklearn.model_selection import train_test_split
import os
from collections import Counter
from random import seed, choices
from statistics import mean
import csv
from nltk.metrics.distance import edit_distance
from scipy.spatial.distance import hamming
import pprint
import numpy as np


class Data:

    def __init__(self, f):
        self._f = f
        self.data = []
        self.X = []
        self.y = []
        self.train_x, self.train_y = [], []
        self.test_x, self.test_y = [], []
        self.encoders = Encoders()
        
    def head(self, n):
        return self.data[:n]

    def tail(self, n):
        return self.data[len(self.data)-n:]

    def load(self):
        data_path = os.path.join(DATA_DIR, self._f)

        readr = csv.DictReader(open(data_path, mode='r'), 
                               fieldnames=['id', 'product_text', 'retailer',
                                           'category'])
        next(readr)
        for row in readr:
            self.data.append({k: row[k].lower().strip() for k in row})

    def set_xy(self, xvars=("product_text")):
        for d in self.data:
            self.y.append(d['category'])
            xrow = []
            for x in xvars:
                if x == 'product_text':
                    v = self._clean_product_text(d[x])
                elif x == 'id':
                    v = int(d[x])
                else:
                    v = d[x]
                xrow.append(v)
            self.X.append(xrow)
            
    def _clean_product_text(self, x):
        retailer_strings = ['kkroger', 'kkroer', 'kkr0er', 'kr0ger',
                            'kkroge', 'kroger', 'kkrog', 'koger', 
                            'kkroe', 'kroer','roger', 'oger', 'kkro', 
                            'kroe', 'koer', 'krgr', "krog", 'kro', 
                            'kkr ', 'kgr', 'kr0', 'kr ',
                            'ppublix', 'publix',  "ppublx", 'publx', 'publ', 
                            'ppub', 'pubx', 'pblx', 'pbl', 
                            'pub', 'plx', 'pbx', 'safeway',
                            'safewy', 'safwy', 'sfwy', 'sfy',
                            'sfw', 'swy']
        for rx in retailer_strings:
            if x.find(rx) > -1:
                return self._clean_product_text(x.replace(rx, "").strip())
            else:
                pass
        return x

    
    @staticmethod
    def generate_pad(x, n, char_wts, random=None):
        seed(random)
        pad = []
        if char_wts:
            chars = []
            lengths = []
            for xi in x:
                chars.extend(list(xi[1]))
                lengths.append(len(xi[1]))
            char_freqs = {elem: chars.count(elem)/float(len(chars)) 
                          for elem in set(chars)}
            mean_size = mean(lengths)
            for i in range(n):
                new_chars = choices(list(set(chars)), 
                                    weights=char_freqs, k=mean_size)
                new_string = "".join(new_chars)
                pad.append(new_string)
                
        else:
            pad.extend(choices([i[0] for i in x], k=n))
        return pad

    def pad_classes(self, min_size, cls_counts=None, use_char_wts=False):
        if not cls_counts:
            cls_counts = Counter(self.y)

        small_classes = {k: cls_counts[k] for k in cls_counts 
                         if cls_counts[k] < min_size}
        for clx in small_classes:
            try:
                ff = np.array([idx for idx in range(len(self.y)) 
                               if self.y[idx] == clx])
                xvals = np.array(self.X)[ff]
            except IndexError:
                raise IndexError("Whoops something went wrong")
            else:
                n_cls = min_size - small_classes[clx]
                pad = Data.generate_pad(x=xvals, n=n_cls, char_wts=use_char_wts)
                self.X.extend([p for p in pad])
                self.y.extend([clx for _ in pad])
    
    def split_data(self, train_sz, test_sz=None, rand_state=None):
        # output format - train_x, test_x, train_y, test_y
        self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.X, self.y, train_size=train_sz)
        stmt = "{setx} are not equal x: {x_set} != y: {y_set}"
        assert (len(self.train_x)==len(self.train_y)), stmt.format(setx='train', x_set=len(self.train_x), y_set=len(self.train_y))
        assert (len(self.test_x)==len(self.test_y)), stmt.format(setx='train', x_set=len(self.train_x), y_set=len(self.train_y))
        print("all sets are equal")
    
class Utils:
    pp = pprint.PrettyPrinter(indent=2)

    
    @classmethod
    def _create_counter(cls, data, name, top_n=None):
        cnt = Counter(data)
        cnt_lst = [(k, cnt[k]) for k in cnt]

        freqs = it.relative_freq(data, float_prec=10, as_=list)
        cnt = sorted(cnt_lst, key=lambda x: x[1], reverse=True)

        if top_n is not None and top_n < len(freqs):
            freqs = freqs[:top_n]
            cnt = cnt[:top_n]
            data = [d for d in data if d in freqs]


        return {'counts': dict(cnt), 'frequencies': dict(freqs), 
                'data': data, 'name': name}

    @classmethod
    def counters(cls, data, top_n):
        pt_part, pt_split, pt_chars = [], [], []
        rets, cats = [], []
        names_idx = ['Product Text (Parts)', 'Product Text (Split)', 
                     'Product Text (Chars)', "Retailers", 'Categories']
        for d in data:
            pt_part.append(it.partition_string(d['product_text']
                                               .replace(" ", ""), 5))

            pt_split.append(d['product_text'].split(" "))
            pt_chars.append(list(d['product_text']))
            rets.append(d['retailer'])
            cats.append(d['category'])
        ptcnt_part = cls._create_counter(it.flatten_nested_list(pt_part), 
                                         name='Product Text (Parts)',
                                         top_n=top_n)
        ptcnt_split = cls._create_counter(it.flatten_nested_list(pt_split),
                                          name='Product Text (Split)',
                                          top_n=top_n)
        ptcnt_chars = cls._create_counter(it.flatten_nested_list(pt_chars),
                                          name='Product Text (Chars)',
                                          top_n=top_n)
        retcnt = cls._create_counter(rets, name="Retailers", top_n=top_n)
        catcnt = cls._create_counter(cats, name='Categories', top_n=top_n) 

        return {"name_idx": names_idx, 
                "counters": [ptcnt_part, ptcnt_split, 
                             ptcnt_chars, retcnt, catcnt]}

    @classmethod
    def string_distances(cls, strings):
        pcts = []
        for string1 in strings:
            pcts_1 = []
            for string2 in strings:
                dist = edit_distance(string1, string2)
                lrgr = max(len(string1), len(string2))
                pct = (lrgr - dist) / lrgr
                pcts_1.append(round(pct, 3))
            pcts.append(pcts_1)
        cls.pp.pprint(pcts)

    @classmethod
    def encoded_distances(cls, arrs):
        pcts = []
        for arr1 in arrs:
            pcts_1 = []
            for arr2 in arrs:
                dist = hamming(arr1, arr2)
                pcts_1.append(round(dist, 3))
            pcts.append(pcts_1)
        cls.pp.pprint(pcts)

    @staticmethod
    def generate_sample(data, size, outfile=None, save=True):
        outfile = (outfile if outfile is not None else f"sample-{size}.csv")
        outpath = os.path.join(DATA_DIR, outfile)
        sample = data[:size]
        if save:
            with open(outpath, mode='w') as f:
                writr = csv.DictWriter(f, fieldnames=['id', 'product_text', 'retailer', 'category'])
                writr.writeheader()
                writr.writerows(sample)
                f.flush()
                f.close()
        return sample