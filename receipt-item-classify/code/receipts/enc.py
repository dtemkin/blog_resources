from abc import abstractmethod
import os
import pickle
from collections import UserDict
from receipts import ENCODERS_DIR


class Encoders(UserDict):
    
    def __init__(self, _items=None):
        super().__init__()
        if _items:
            self._items.update(**_items)
        else:
            self._items = {}
        
    def add(self, name, **kwargs):
        data=kwargs.get('data', None)
        enc=kwargs.get("encoder", 'auto')
        fit=kwargs.get("fit", True)
        
        if enc == 'auto' or enc == 'range':
            e = RangeEncoder(name=name)
        else:
            e = enc
        if fit:
            if not data:
                raise ValueError("No data found. cannot fit encoder.")
            else:
                try:
                    e.fit(data)
                except AttributeError:
                    raise AttributeError("Encoder must be a subclass of\
                    BaseEncoder or for scikit-learn.")
                except Exception as err:
                    raise Exception(err)
        
        self._items.update({name: {"enc": e, 'fitted': fit}})
        return e

    def fit(self, data, name, transform=True):
        try:
            e = self.get(name)
        except KeyError:
            raise KeyError("Encoder not found or opt did not include name")
        else:
            try:
                e.fit(data)
            except AttributeError:
                raise AttributeError("encoder must be a valid BaseEncoder\
                subclass or from scitkit learn")
            else:
                self.update({name: {'enc': e, 'fitted': True}})
        if transform:
            return e, self.apply(data=data, fitted_enc=e)
        else:
            return e, None

    def get(self, name):
        try:
            e = self._items[name]['enc']
        except KeyError:
            raise KeyError("Encoder %s not found." % name)
        else:
            return e
        
    def apply(self, data, fitted_enc=None, name=None, *args, **kwargs):
        if fitted_enc:
            enc = fitted_enc
        elif name:
            
            e = self.get(name=name)
            if e['fitted']:
                enc = e['enc']
            else:
                enc = self.fit(data=data, name=name)
        else:
            raise ValueError("Whoops failed to provide fitted encoder\
                              instance or an encoder name")
            
        return enc.transform(data)
    
    def __dict__(self):
        return self._items
                

class BaseEncoder:

    def __init__(self):
        self._map = {}
        self._inv_map = {}

    @abstractmethod
    def fit(self, data, *args, **kwargs):
        raise NotImplementedError("All methods must be defined by subclass")

    @abstractmethod
    def transform(self, data, *args, **kwargs):
        raise NotImplementedError("All methods must be defined by subclass")

    @abstractmethod
    def inverse_transform(self, enc_data, *args, **kwargs):
        raise NotImplementedError("All methods must be defined by subclass")
        
    def load(self, name):
        pth = os.path.join(ENCODERS_DIR, '{name}_encoder.pkl')
        if os.path.isfile(pth):
            stream = open(pth, mode='rb')
            obj = pickle.load(stream)
            self._map = obj['map']
            self._inv_map = obj['inv_map']
            stream.close()
            print("Loaded.")
            return True
        else:
            return False

    def dump(self, name):
        pth = os.path.join(ENCODERS_DIR, f'{name}_encoder.pkl')
        stream = open(pth, mode='wb')
        pickle.dump({'map': self._map, 'inv_map': self._inv_map}, stream)
        stream.flush()
        stream.close()
        print("Saved.")


class RangeEncoder(BaseEncoder):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def _update_encoder__(self, d):
        if len(self._map) in self._map:
            print("Update Failed, Code Already Exists")
            raise KeyError("Mapping key not found.")
        else:
            self._map.update({len(self._map): d})
            return len(self._map)

    def fit(self, data, save=True, *args, **kwargs):
        unique_vals = list(set(data))
        st = kwargs.get("start_value", 0)
        ed = kwargs.get("end_value", len(unique_vals))
        rng = range(st, ed)
        self._map = {unique_vals[k]: rng[k] for k in range(len(unique_vals))}
        self._inv_map = {rng[kx]: unique_vals[kx] for kx in 
                         range(len(unique_vals))}
        if save:
            self.dump(name=self._name)
            
    def transform(self, data, *args, **kwargs):
        error_handle = kwargs.get("errors", 'update')
        enc = []
        for d in data:
            try:
                code = self._map[d]
            except KeyError:
                if error_handle == 'update':
                    code = self._update_encoder__(d=d)
                    enc.append(code)
                elif error_handle == 'skip':
                    print("Value not found in map. Skipping...")
                    continue
                    
                elif error_handle == 'break':
                    raise KeyError("Mapping key not found.")
                else:
                    raise ValueError("Invalid error_handle. \
                    Must be 'update', 'skip', 'break'")
                
            else:
                enc.append(code)
        return enc
    
    def fit_transform(self, data):
        self.fit(data)
        return self.transform(data)

    def inverse_transform(self, data, *args, **kwargs):
        error_handle = kwargs.get("errors", 'skip')
        orig = []
        for d in data:
            try:
                x = self._inv_map[d]
            except KeyError:
                if error_handle == "skip":
                    print("Could not find the mapping key, skipping...")
                    orig.append("****ERRROR: SKIPPED****")
                    continue
                else:
                    raise KeyError("Whoops something went \
                    wrong could not find the key.")
            else:
                orig.append(x)
        return orig
