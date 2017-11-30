import os
import random
import numpy as np
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import spacy
from spacy.tokenizer import Tokenizer
from spacy.attrs import POS, ORTH, LEMMA
from string import punctuation, digits, ascii_lowercase
from collections import Counter, OrderedDict

from wordcloud import WordCloud
from PIL import Image
import matplotlib.pyplot as plt

nlp = spacy.load("en")


def get_abspath(filename):
    return os.path.abspath(os.path.join(os.path.curdir, filename))


def pdf2text(fname, pages=None, save=True):
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

def load_letters():
    if os.path.isfile(get_abspath("amzn-shareholder-letters-1997-2016.txt")):
        f = open(file=get_abspath("amzn-shareholder-letters-1997-2016.txt"), mode="r")
        text = " ".join([i.strip() for i in f.readlines() if i != "\n"])
    else:
        text = pdf2text(fname="amzn-shareholder-letters-1997-2016.pdf")
    return text


def stop_words():
    file = open(get_abspath("bezos-stopwords.ls"), mode="r")
    lines = [l.rstrip().lower() for l in file.readlines() if l != "\n"]
    lines.extend(list(punctuation))
    lines.extend(['"', "'", "--", "-", "/", ",", ".", "...", "amazon.com",
                  "www.amazon.com", "http://www.amazon.com", "aws", "prime",
                  "kindle", "\t", "shareholders", "amazon", "jeffrey", "executive",
                  "inc.","inc", "amazonians","bezos", "jeff", "founder", "chief",
                  "officer", "day","sincerely", "\uf8e7\uf8e7", "u.s.", "u.k.", "''",])
    lines.extend(list(digits))
    lines.extend(list(ascii_lowercase))
    return lines

def update_tokenizer(tokenizer):
    conj = [{"i'm": [{ORTH: "i"}, {ORTH: "n't", LEMMA: "not"}],
             "you'll": [{ORTH: "you"}, {ORTH: "'ll", LEMMA: "will"}],
             "we'll": [{ORTH: "we"}, {ORTH: "'ll", LEMMA: "will"}],
             "i'll": [{ORTH: "i"}, {ORTH: "'ll", LEMMA: "not"}],
             "isn't": [{ORTH: "is"}, {ORTH: "n't", LEMMA: "not"}],
             "shouldn't": [{ORTH: "should"}, {ORTH: "n't", LEMMA: "not"}],
             "wouldn't": [{ORTH: "would"}, {ORTH: "n't", LEMMA: "not"}],
             "couldn't": [{ORTH: "should"}, {ORTH: "n't", LEMMA: "not"}],
             "don't": [{ORTH: "do"}, {ORTH: "n't", LEMMA: "not"}],
             "can't": [{ORTH: "ca", LEMMA: "can"}, {ORTH: "n't", LEMMA: "not"}],
             "won't": [{ORTH: "wo", LEMMA: "will"}, {ORTH: "n't", LEMMA: "not"}]}]

    tokenizer.add_special_case(conj)
    return tokenizer

def simple_tokenizer(remove_stops=True, min_word_length=3):
    txt = load_letters()
    doc = nlp(txt)
    words = []
    for w in doc:
        if w.text.lower().strip() in stop_words() and remove_stops is True:
            pass
        elif len(w.text) <= min_word_length:
            pass
        elif w.text == "1997":
            pass
        elif w.text.lower().strip() == "customers":
            words.append("customer")
        else:
            words.append(w.text.lower().strip())
            
    return [w for w in words]



def grey_scale_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(0, 30)


def generate_frequency_table(n=10):
    
    word_counts = Counter(simple_tokenizer()).most_common(n)
    table=['<html><body><table border="1"><tr><th id="title" colspan="2"><b>Top %s Words</b></th></tr><tr><th headers="title"><em>Word</em></th><th headers="title"><em>Frequency</em></th></tr>' % n]

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
      
def generate_wordcloud():

    imgmask = np.array(Image.open(get_abspath("amazon-logo.jpg")))
    words = simple_tokenizer()
    text = " ".join(words)
    wc = WordCloud(background_color="white", max_font_size=35, max_words=500, mask=imgmask, margin=2, random_state=1).generate(text=text)

    plt.title("Jeff Bezos - Amazon Shareholders Letters (1997-2016)")
    plt.imshow(wc.recolor(color_func=grey_scale_func, random_state=3), interpolation="bilinear")
    wc.to_file("wordcloud.png")
    plt.axis("off")
generate_frequency_table()
generate_wordcloud()
