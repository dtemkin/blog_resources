

import os
import random
import numpy as np
from statistics import median
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFPage

import spacy as spacy

from spacy.attrs import ORTH, LEMMA
from spacy.lang.en import English
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import sent_tokenize

from string import punctuation, digits, ascii_lowercase
from collections import Counter, OrderedDict

from wordcloud import WordCloud
from PIL import Image
import matplotlib.pyplot as plt
import re


import plotly.graph_objs as go
from plotly.offline import plot

from gensim.corpora import Dictionary
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
import pyLDAvis.gensim
from gensim.models.phrases import Phrases, Phraser


def set_stopwords():
    file = open(get_abspath("bezos-stopwords.ls"), mode="r")
    stopwords = [l.rstrip().lower() for l in file.readlines() if l != "\n"]
    stopwords.extend(list(punctuation))
    stopwords.extend(['"', "'", "--", "-", "/", ",", ".", "...", "'s", "amazon.com",
                      "www.amazon.com", "http://www.amazon.com", "aws", "prime",
                      "kindle", "\t", "thousand", "million", "billion", "shareholders",
                      "amazon", "jeffrey", "executive", "share", "shareholder",
                      "inc.", "inc", "amazonians", "bezos", "jeff", "founder", "chief",
                      "officer", "day", "90th", "sincerely", "\uf8e7\uf8e7", "u.s.", "u.k.", "''"])
    stopwords.extend(list(digits))
    stopwords.extend(list(ascii_lowercase))
    return stopwords


def get_abspath(filename):
    return os.path.abspath(os.path.join(os.path.curdir, filename))


stops = set_stopwords()
nlp = spacy.load("en")


class Documents(object):
    data = []

    def __init__(self, data=list()):
        self.data.extend(data)
        self.agg_tokens = []
        self._doctokens = []
        self._sents = []

        self.nlp = spacy.load("en")

    def pdf2text(self, fname, pages=None, save=True):
        if not pages:
            pagenums = set()
        else:
            pagenums = set(pages)

        output = StringIO()
        manager = PDFResourceManager()
        converter = TextConverter(manager, output, laparams=LAParams())
        interpreter = PDFPageInterpreter(manager, converter)

        infile = open(get_abspath(fname), 'rb')
        for page in PDFPage.get_pages(infile, pagenums):
            interpreter.process_page(page)
        infile.close()
        converter.close()
        text = output.getvalue()
        if save is True:
            file, ext = os.path.splitext(fname)
            outfile = file + ".txt"
            with open(outfile, mode="w") as f:
                f.write(text)
            f.close()
            output.close()
        else:
            output.close()
        return text

    def load_letters(self):
        if os.path.isfile(get_abspath("amzn-shareholder-letters-1997-2016.txt")):
            f = open(file=get_abspath("amzn-shareholder-letters-1997-2016.txt"), mode="r")
            text = " ".join([i.strip() for i in f.readlines() if i != "\n"])
        else:
            text = self.pdf2text(fname="amzn-shareholder-letters-1997-2016.pdf")
        doc_strings = [d.replace("holders: ", "").replace("owners: ", "").replace("holders, customers, and employees: ", "").strip() for d in text.split("To our share")][1:]

        for d in doc_strings:
            doc = Document(d)
            self._sents.extend(doc.sents)
            self.data.append(doc)

        phrase_model = Phrases(self._sents, min_count=1, threshold=1)
        for doc in self.data:
            tknize = doc.set_tokenizer(nlp=self.nlp)
            tokens = doc.process(phrase_model=phrase_model, tokenizer=tknize)
            # stemmed = doc.apply_stemmer(tokens)
            doc.tokens = tokens
            self._doctokens.append(doc.tokens)
            self.agg_tokens.extend(doc.tokens)


    @property
    def tokens(self):
        return self.agg_tokens

    @property
    def doctokens(self):
        return self._doctokens


class Document(object):

    stemmer = SnowballStemmer("english")

    def __init__(self, text):
        self._text = text
        self._tokens = None

    def set_tokenizer(self, nlp):
        tokenizer = English().Defaults.create_tokenizer(nlp)
        conj = {"i'm": [{ORTH: "i"}, {ORTH: "n't", LEMMA: "not"}],
                "it's": [{ORTH: "it"}, {ORTH: "'s", LEMMA: "is"}],
                "you'll": [{ORTH: "you"}, {ORTH: "'ll", LEMMA: "will"}],
                "we'll": [{ORTH: "we"}, {ORTH: "'ll", LEMMA: "will"}],
                "we're": [{ORTH: "we"}, {ORTH: "'re", LEMMA: "are"}],
                "i'll": [{ORTH: "i"}, {ORTH: "'ll", LEMMA: "not"}],
                "isn't": [{ORTH: "is"}, {ORTH: "n't", LEMMA: "not"}],
                "shouldn't": [{ORTH: "should"}, {ORTH: "n't", LEMMA: "not"}],
                "wouldn't": [{ORTH: "would"}, {ORTH: "n't", LEMMA: "not"}],
                "couldn't": [{ORTH: "should"}, {ORTH: "n't", LEMMA: "not"}],
                "don't": [{ORTH: "do"}, {ORTH: "n't", LEMMA: "not"}],
                "we've": [{ORTH: "we"}, {ORTH: "'ve", LEMMA: "have"}],
                "can't": [{ORTH: "ca", LEMMA: "can"}, {ORTH: "n't", LEMMA: "not"}],
                "won't": [{ORTH: "wo", LEMMA: "will"}, {ORTH: "n't", LEMMA: "not"}]}
        for c in conj.items():
            tokenizer.add_special_case(c[0], c[1])
        return tokenizer

    def isDigitMod(self, x):
        try:
            int(x)
        except ValueError:
            try:
                float(x)
            except ValueError:
                return False
            else:
                return True
        else:
            return True

    def _clean_text(self, tokens, min_word_length=3):
        for w in tokens:
            try:
                lc = w.lower()
            except TypeError:
                yield None
            else:

                if (
                        lc.strip() not in stops and
                        self.isDigitMod(w.strip()) is False and
                        len(lc.strip()) > min_word_length and
                        lc.find(",") == -1 and lc.find("@") == -1 and
                        lc.find("-") == -1
                ):
                    yield lc.strip()

    def context_pairs(self, tkns):
        pairs = [("cash", "flow"), ("balance", "sheet"), ("financial", "statement"),
                 ("income", "statement"), ("long", "term"), ("short", "term"),
                 ("long", "run"), ("short", "run")]
        tx = []
        for t in range(len(tkns)):
            for p in pairs:
                if tkns[t] == p[0] and tkns[t+1] == p[1]:
                    tx.append("_".join([tkns[t], tkns[t+1]]))
                else:
                    tx.append(tkns[t])
        return tx

    def process(self, phrase_model, tokenizer):
        bigrams = Phraser(phrase_model)
        tokes = []
        for sent in self.sents:
            tkns = [t.lemma_ for t in tokenizer(sent)]
            tkns = self.context_pairs(tkns)
            tkns = [c for c in self._clean_text(tkns) if c is not None]
            tkns = bigrams[tkns]
            tokes.extend(tkns)
        return tokes

    def apply_lemmatizer(self, tokens):
        return [l.lemma_ for l in tokens if l.lemma_ != '-pron-']

    def apply_stemmer(self, tokens):
        return [self.stemmer.stem(t) for t in tokens]

    @property
    def sents(self):
        return sent_tokenize(self._text.lower())

    @property
    def tokens(self):
        return self._tokens

    @tokens.setter
    def tokens(self, x):
        self._tokens = x


class Analyze(object):

    def __init__(self, docs):
        self.docs = docs

    def generate_frequency_table(self, n=10):

        word_counts = Counter(self.docs.tokens).most_common(n)

        table = [
            '<html><body><table border="1"><tr><th id="title" colspan="2"><b>Top %s Words</b></th></tr><tr><th headers="title"><em>Word</em></th><th headers="title"><em>Frequency</em></th></tr>' % n]

        for i in word_counts:
            table.append(r'<tr><td>{}</td><td>{}</td></tr>'.format(i[0], i[1]))
        table.append('</table></body></html>')

        html = "".join(table)
        htmlfile = get_abspath("bezos-table.html")
        if os.path.isfile(htmlfile):
            os.remove(htmlfile)
        with open(htmlfile, mode="w") as f:
            f.write(html)
            f.flush()
        f.close()
        return word_counts[0]

    def grey_scale_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        return "hsl(0, 0%%, %d%%)" % random.randint(0, 30)

    def generate_wordcloud(self):

        imgmask = np.array(Image.open(get_abspath("amazon-logo.jpg")))
        text = " ".join(self.docs.tokens)
        wc = WordCloud(background_color="white", max_font_size=35, max_words=500, mask=imgmask, margin=2,
                       random_state=1).generate(text=text)

        plt.title("Jeff Bezos - Amazon Shareholders Letters (1997-2016)")
        plt.imshow(wc.recolor(color_func=self.grey_scale_func, random_state=3), interpolation="bilinear")
        wc.to_file("wordcloud.png")
        plt.axis("off")


docs = Documents()
docs.load_letters()
analyze = Analyze(docs)
max_freq = analyze.generate_frequency_table(n=10)

num_topics = 3
chunksize = 100
passes = 10
iterations = 100
eval_every = 1
dictionary = Dictionary(docs.doctokens)
corpus = [dictionary.doc2bow(d) for d in docs.doctokens]
temp = dictionary[0]
id2word = dictionary.id2token


def lda_model(corpus, id2word, num_topics=8, chunksize=50,
              passes=10, iterations=100, eval_every=1):

    mod = LdaModel(corpus=corpus, id2word=id2word, chunksize=chunksize,
                   alpha='auto', eta='auto', iterations=iterations,
                   num_topics=num_topics, passes=passes, eval_every=eval_every)
    return mod


def compute_coherence_values(corpus, dictionary, id2word, texts, limit, start=3, step=1):
    model_coherence = []

    for num_topics in range(start, limit, step):
        model = lda_model(corpus=corpus, id2word=id2word, num_topics=num_topics)

        comodel = CoherenceModel(model=model, texts=texts, dictionary=dictionary, coherence='c_v')

        model_coherence.append((num_topics, model, comodel.get_coherence()))
    return model_coherence


model_coherences = compute_coherence_values(corpus=corpus, dictionary=dictionary,
                                            id2word=id2word, texts=docs.doctokens,
                                            limit=12)

max_coherence = max([mx[2] for mx in model_coherences])

trace = go.Scatter(
    x=[c[0] for c in model_coherences],
    y=[c[2] for c in model_coherences]
)

data = [trace]
layout = go.Layout(title="LDA Model Coherence Values by Number of Topics",
                   xaxis=dict(title="Number of Topics"),
                   yaxis=dict(title="Coherence Value"))

fig = go.Figure(data=data, layout=layout)
plot(fig, filename='coherences.html', auto_open=False)

for m in model_coherences:
    if m[2] == max_coherence:
        best_model = m[1]
        prepped = pyLDAvis.gensim.prepare(best_model, corpus, dictionary)
        pyLDAvis.save_html(prepped, "ldaviz.html")

