from collections import Counter


def merge_predicted(rule_pred, other_pred):
    p = other_pred.copy()
    p.extend(rule_pred)
    
    ordered = sorted(p, key=lambda x1: x1[0])
    return [o[1] for o in ordered]


class RuleModel:

    def __init__(self, target_cls, *args, **kwargs):
        self._X, self._y = [], []
        self._predicted = []
        self._target_cls = target_cls
        self._rules = {}
        self._fpr_threshold = kwargs.get('fpr_threshold', [.0, .10])
        self._max_n, self._min_n = kwargs.get("max_n", 50), kwargs.get("min_n", 5)
        self._max_chnk = kwargs.get("max_chunk_sz", 30)
        self._min_chnk = kwargs.get("min_chunk_sz", 0)

    @property
    def get_fpr_threshold(self):
        return self._fpr_threshold

    @property
    def rules(self):
        return self._rules
    
    @property
    def target_class(self):
        return self._target_cls

    @property
    def X(self):
        return self._X
    
    @property
    def y(self):
        return self._y

    @property
    def predicted(self):
        return self._predicted
    
    def false_pos_rate(self, fp, tn, digits=None):
        fpr=float(fp/(fp+tn))
        if type(digits) is int:
            fpr = round(fpr, digits)
        return fpr

    def _make_chunks__(self, string, size, incl_space):
        if not incl_space:
            strx = string.replace(" ", "")
        return [strx[i:i+size] for i in range(0, len(string), size)]
          

    def _make_counter__(self, arr, substring_size, freq):
        cnts = Counter()
        for strx in arr:
            chunks = self._make_chunks__(string=strx, size=substring_size, 
                                         incl_space=False)
            cnts.update(chunks)
        
        return sorted([(k, cnts[k]) for k in cnts if len(k) == substring_size], 
                      key=lambda x: x[1], reverse=(True if freq=='most' else False))
    
    def _check_rules__(self, x, rs):
        val = False
        for rule in rs:
            if rule in x.replace(" ", ""):
                val = True
            elif x.isdigit():
                val = True
        return val
    
    def _update_rules__(self, existing, new, exclude, n):
        existing = [e for e in existing if e not in exclude]
        existing.extend(new)
        return list(existing)[:n]
    
    def _approx_equal__(self, x1, x2, max_diff=.05):
        return (abs(x1-x2)/x1 > max_diff)
    
    def _verify_class__(self, found):
        return (found == self.target_class)
    
    def _filter_data__(self, X, y):
        return [X[_idx] for _idx in range(len(X)) 
                if y[_idx] == self.target_class]
    
    def _get_conditional_lists__(self, X, y, rules):
        
        _fn_tups, _fp_tups, _tn_tups, _tp_tups = [], [], [], []
        _neg_classes = []
        for _idx in range(len(X)):
            if self._check_rules__(X[_idx], rules):
                if self._verify_class__(y[_idx]):
                    _tp_tups.insert(len(_tp_tups), (_idx, X[_idx]))
                else:
                    _fp_tups.insert(len(_fp_tups), (_idx, X[_idx]))
                    
            else:
                if self._verify_class__(y[_idx]):
                    _tn_tups.insert(len(_tn_tups), (_idx, X[_idx]))
                else:
                    _fn_tups.insert(len(_fn_tups), (_idx, X[_idx]))
                    
                _neg_classes.insert(len(_neg_classes), (_idx, y[_idx]))
                
        return _fn_tups, _fp_tups, _tn_tups, _tp_tups, _neg_classes
    
    
    def _check_threshold__(self, val):
        try:
            t = self.get_fpr_threshold
        except Exception as err:
            raise KeyError("Invalid threshold name", err)
        else:
            if val < t[0]:
                return False, 'min'
            elif val > t[1]:
                return False, 'max'
            else:
                return True, ''

    def fit(self, X, y, **kwargs):
        filtered_x = kwargs.get("filtered_data", self._filter_data__(X, y))
        chnk_size = kwargs.get("chnk_size", self._min_chnk)
        n = kwargs.get("n", self._min_n)
        pn = kwargs.get("pass_num", 0)
        print(f"Pass number {pn}")
        cnts = self._make_counter__(filtered_x, chnk_size, freq=kwargs.get("freq_type", 'most'))
        rules = self._update_rules__(existing=kwargs.get('rules', []), 
                                     new=[c[0] for c in cnts], n=n,
                                     exclude=kwargs.get("exclude", []))
        print(f"Created Rules: {rules}")
        fneg, fpos, tneg, tpos, neg_cls = self._get_conditional_lists__(X, y, rules)

        fneg_sz, fpos_sz, tneg_sz, tpos_sz = (len(i) for i in 
                                              [fneg, fpos, tneg, tpos])
        fneg_str, fpos_str, tneg_str, tpos_str = ([t[1] for t in xi] 
                                                  for xi in 
                                                  [fneg, fpos, tneg, tpos])
        tot_filt = len(filtered_x)
        
        curr_fpr = self.false_pos_rate(fp=fpos_sz, tn=tneg_sz)
        prev_fpr = kwargs.get("prev_fpr", curr_fpr)
        similarfpr = self._approx_equal__(prev_fpr, curr_fpr)
        if similarfpr:
            chgmag = {"chnk": 1}
        else:
            chgmag = {"chnk": 1}

        thfpr, fmsg = self._check_threshold__(curr_fpr)
        if thfpr:
            self._X = X
            self._y = y
            self._rules = rules
        else:
            
            model_params = {"X": X, 'y': y, "n": n, 'chnk_size': chnk_size, 
                            'filtered_data': filtered_x, 'rules': rules,
                            "prev_fpr": curr_fpr}
            if fmsg == 'max':
                # increase substring size
                # decrease N
                if model_params['chnk_size'] >= self._max_chnk:
                    print("Hit limit no further optimization is possible")
                    self._X = X
                    self._y = y
                    self._rules = rules
                else:
                    chnk_size += chgmag['chnk']
                    model_params.update({"chnk_size": chnk_size,
                                         "pass_num": pn+1,
                                         'exclude': set([r for r in rules if 
                                                         any([_ for _ in fpos_str if r in _])])})
                    self.fit(**model_params)

            else:
                if model_params['chnk_size'] >= self._min_chnk:
                    
                    #n_diff = n + chgmag['n']
                    #new_n = (n_diff if n_diff <= self._max_n else n)

                    chnk_size -= chgmag['chnk']

                    model_params.update({"chnk_size": chnk_size, 
                                         "pass_num": pn+1})

                    self.fit(**model_params)
                else:
                    print("Hit limit no further optimization is possible")
                    self._X = X
                    self._y = y
                    self._rules = rules

    def predict(self, X, **kwargs):
        for tx in range(len(X)):
            if self._check_rules__(X[tx], self.rules):
                self._predicted.append((tx, self.target_class))
            else:
                self._predicted.append((tx, None))

        # print(f"{len(self._predicted)} not an item cases identified by rule model")
