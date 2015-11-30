from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

import re
from .forms import OpinionForm
from .format import read_dic, clean_string
from subprocess import call
from nltk.stem.snowball import PorterStemmer as Stemmer
from nltk. corpus import stopwords
from pprint import pprint as print

def index(request):
    template = loader.get_template('systran/index.html')

    if request.method == 'POST':
        form = OpinionForm(request.POST)

        if form.is_valid():
            try:
                sentence = form.cleaned_data['sentence']
                dic = read_dic('dic_98')
                s = extract_keywords(sentence)
                for word in s:
                    print(word)
                    try:
                        dic[word] += 1
                    except:
                        pass
                l = []
                with open('test', 'w') as f:
                    f.write("0")
                    i = 1
                    for key, value in dic.items():
                        if value != 0:
                            print('{} ({}) : {}'.format(key, i, value))
                            f.write(" {}:{}".format(i, value))
                        i += 1
                    f.write('\n')
                call(["./svm_classify", "test", "model", "tmp"])
                with open('tmp', 'r') as r:
                    pred = r.readline()
                template = loader.get_template('systran/results.html')
                context = RequestContext(request, {'sentence': sentence,
                    'prediction': pred, 'keywords' : s})
                return HttpResponse(template.render(context))


            except Exception as e:
                print(e)
                return HttpResponseRedirect('/systran/error')
        else:
            return HttpResponseRedirect('/systran/error')
    else:
        form = OpinionForm()
        context = RequestContext(request, {'form': form})
        return HttpResponse(template.render(context))

def extract_keywords(sentence):
    sentence = sentence.lower()
    not_stopw = ["no", "nor", "not", "over", "under", "again", "further",
                        "but", "against", "too", "very"]
    stopw = stopwords.words('english')
    for x in not_stopw:
        stopw.remove(x)
    print(stopw)
    pattern = re.compile(r'\b(' + r'|'.join(stopw) + r')\b\s*')
    sentence = sentence.replace('\n', '')
    sentence = sentence.replace("n't", " not")
    sentence = clean_string(sentence)
    sentence = pattern.sub('', sentence)
    stemmer = Stemmer()
    s = [stemmer.stem(w) for w in sentence.split()]
    b = zip(*[s[i:] for i in [0, 1]])
    b = [bigram[0] + " " + bigram[1] for bigram in b]
    return s + b


def error(request):
    template = loader.get_template('systran/error.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))
