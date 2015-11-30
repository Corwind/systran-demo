#!/usr/bin/python3

"""
format.py

Usage:
    format.py -d <dic> -i <input> -o <output> (-f|--fun) <fun> [--use-idf]
    [--get-idf <idf-file> | --write-idf <idf-file>] [--format <format>]

Options:
    -h --help       Print this message
    -v --version    Print the version
    -d              The file to print the dictionary
    -i              The input file
    -o              The output file
    -f --fun        Specify the formatting function to use. You can use the
                    following : format_{analyse,analyse_test,train,test}
    --use-idf       Whether or not to compute tf-idf
    --get-idf       Get idf values computed from learning set from a file
    --write-idf     Write idf values computed from learning set to a file
    --format        Specify the format if needed, the grammar is the following:
                    [target] [separator] [feature][feature_separator][value]
                    [target] has to be a numerical value
                    [feature] has to be a string of alpha-numerical values
                    [value] has to be a numerical value
                    [separator] and [feature_separator] have to be a single non
                    alpha-numerical character.
                    Accepted strings are (for exemple):
                        - "[target] | [feature]:[value]",
                        - "1 /:\ data:42"


"""


from math import log10
from collections import OrderedDict
from string import punctuation
from string import digits

IDF = True
GET_IDF = False
WRITE_IDF = False
IDF_FILE = None
SEP = " "
FEAT_SEP = ":"

def clean_string(s):
    for c in punctuation:
        s = s.replace(c, " ")
    for c in digits:
        s = s.replace(c, "")
    return s


def read_file(f_in):
    lines = []
    with open(f_in, "r") as f:
        lines = f.readlines()
    return lines


def build_dic(lines):
    dic = OrderedDict()
    final_lines = []
    print("Building dictionnary...")
    for line in lines:
        l = line.split("\t")
        if len(l) == 1:
            lines.remove(line)
            continue
        l = l[1]
        l = clean_string(l)
        words = bigrams(l) + l.split()
        final_lines.append(words)
        for w in words:
            dic[w] = 0
            dic.move_to_end(w)
    done()
    return (dic, final_lines)

def get_grades(lines):
    grades = []
    for l in lines:
        l = l.split("\t")
        if len(l) == 1:
            continue
        grade = l[0]
        grades.append("+1" if grade[0] == "+" else "-1")
    return grades

def get_cleanlines_grades(lines):
    final_lines = []
    grades = []
    for l in lines:
        l = l.split("\t")
        if len(l) == 1:
            continue
        grade = l[0]
        grades.append("+1" if grade[0] == "+" else "-1")
        l = l[1:][0]
        l = clean_string(l)
        final_lines.append(l.split())
    return grades, final_lines


def format_data(f_out, data, f_dic, dic, w = False):
    grades, lines = data
    if w:
        for line in lines:
            for word in line:
                dic[word] += 1
        for key, value in dic.items():
            if value < 3:
                del dic[key]
        write_dic(f_dic, dic)
        dic = clean_all_dic(dic)
    idf = None
    if IDF:
        idf = compute_idf(lines, dic)
    write_file(f_out, (grades, lines), dic, idf)

def format_analyse_test(f_in, f_out, f_dic):
    dic = read_dic(f_dic)
    grades = []
    lines = []
    l = []
    newline = True
    with open(f_in, 'r') as fin:
        for line in fin:
            if line.startswith("------------------------"):
                continue
            if line.startswith("++++++++++++++++++++++++"):
                lines.append(l)
                newline = True
                continue
            word = line.split("\t")[2]
            if newline:
                l = []
                grades.append(word)
                newline = False
                continue
            l.append(word)
    for i in range(len(grades)):
        grades[i] = ("+1" if grades[i][0] == '+' else "-1")
    format_data(f_out, (grades, lines), f_dic, dic)

def format_analyse(f_in, f_out, f_dic):
    dic = OrderedDict()
    grades = []
    lines = []
    l = []
    newline = True
    with open(f_in, 'r') as fin:
        for line in fin:
            if line.startswith("------------------------"):
                continue
            if line.startswith("++++++++++++++++++++++++"):
                lines.append(l)
                newline = True
                continue
            word = line.split("\t")[2]
            if newline:
                l = []
                grades.append(word)
                newline = False
                continue
            l.append(word)
            dic[word] = 0
            dic.move_to_end(word)
    for i in range(len(grades)):
        grades[i] = ("+1" if grades[i][0] == '+' else "-1")
    format_data(f_out, (grades, lines), f_dic, dic, True)

def format_train(f_in, f_out, f_dic):
    lines = read_file(f_in)
    dic, clean_lines = build_dic(lines)
    grades = get_grades(lines)
    format_data(f_out, (grades, clean_lines), f_dic, dic, True)

def format_test(f_in, f_out, f_dict):
    dic = read_dic(f_dict)
    lines = read_file(f_in)
    grades, clean_lines = get_cleanlines_grades(lines)
    format_data(f_out, (grades, clean_lines), f_dic, dic)

def dict_idf(dic, idf, line):
    for word in line:
        tf = compute_tf(word, line)
        try:
            dic[word] = tf * idf[word]
        except:
            pass
    return dic

def dict_occur(dic, line):
    for word in line:
        try:
            dic[word] += 1
        except:
            pass
    return dic

def write_file(f, data, dic, idf = None):
    if WRITE_IDF:
        write_idf(idf, IDF_FILE)
    print("Writing formatted data to {}...".format(f))
    grades, lines = data
    with open(f, "w") as fout:
        n = len(lines)
        for j in range(n):
            if (j % 100) == 0:
                print("{0} / {1}".format(str(j), n))
            if idf:
                dic = dict_idf(dic, idf, lines[j])
            else:
                dic = dict_occur(dic, lines[j])
            fout.write(grades[j] + SEP)
            i = 1
            for key, value in dic.items():
                if(value != 0):
                    fout.write(str(i) + FEAT_SEP + str(value) +
                               (" " if i != len(dic) else "\n"))
                else:
                    if i == len(dic):
                        fout.write("\n")
                i += 1
            dic = clean_all_dic(dic)
            i = 1
    done()


def clean_all_dic(dic):
    for key in dic.keys():
        dic[key] = 0
    return dic

def clean_dic(dic, line):
    for word in line.split():
        try:
            dic[word] = 0
        except:
            pass
    return dic


def write_dic(f_dict, dic):
    print("Writing dictionnary to {}...".format(f_dic))
    with open(f_dict, "w+") as fdict:
        for key in dic.keys():
            fdict.write(key)
            fdict.write("\n")
    done()


def read_dic(f_dict):
    dic = OrderedDict()
    with open(f_dict, 'r') as f:
        for line in f.readlines():
            w = line.replace("\n", "")
            if map(str.isalpha, w.split()):
                dic[w] = 0
                dic.move_to_end(w)
    return dic


def compute_tf(word, line):
    i = 0
    for w in line:
        if w == word:
            i += 1
    tf = i / len(line)
    return tf


def compute_idf(lines, dic):
    print("Computing idf...")
    idf = OrderedDict()
    if GET_IDF:
        with open(IDF_FILE, 'r') as f:
            for line in f.readlines():
                l = line.split('\t')
                idf[l[0]] = float(l[1])
        return idf
    for key in dic.keys():
        i = 0
        for j in range(len(lines)):
            if key in lines[j]:
                i += 1
        if i == 0:
            continue
        idf[key] = log10(float(len(lines)) / float(i))
    done()
    return idf

def write_idf(idf, f_idf):
    print("Writing idf to {}...".format(f_idf))
    with open(f_idf, 'w') as f:
        for key, value in idf.items():
            f.write(key + "\t" + str(value) + "\n")
    done()

def bigrams(line, debug=None):
    if debug:
        print(str(debug))
    ls = line.split()
    z = zip(*[ls[i:] for i in [0, 1]])
    z = [bigram[0] + " " + bigram[1] for bigram in z]
    return z

def corpus_bigrams(corpus):
    print("Computing bigrams from corpus...")
    b = []
    for line in corpus:
        b.append(bigrams(line, corpus_bigrams))
    done()
    return b

def check_func(fun):
    return fun in globals().keys()

def parse_grammar(g):
    g = g.split()
    if len(g) == 3:
        SEP = " " + g[1] + " "
    else:
        SEP = " "
    for c in g[len(g) - 1]:
        if (not (c.isalnum() or c == '[' or c == ']')):
            FEAT_SEP = c
            break
    return SEP, FEAT_SEP

def parse_format(f):
    if "[" in f:
        return parse_grammar(f)
    s_f = f.split()
    if (len(s_f) == 3):
        SEP = " " + s_f[1] + " "
    else:
        SEP = " "
    for c in s_f[len(s_f) - 1]:
        if not(c.isalnum()):
            FEAT_SEP = c
            break
    return SEP, FEAT_SEP

def done():
    print("Done.")

if __name__ == "__main__":
    from docopt import docopt
    arguments = docopt(__doc__, version='1.0')
    f_dic = arguments["<dic>"]
    f_in = arguments["<input>"]
    f_out = arguments["<output>"]
    func = arguments["<fun>"]
    IDF = arguments["--use-idf"]
    GET_IDF = arguments["--get-idf"]
    WRITE_IDF = arguments["--write-idf"]
    if GET_IDF or WRITE_IDF:
        if not IDF:
            exit("Invalid arguments combination: --get-idf or --write-idf must\
                 be used with --use-idf")
        IDF_FILE = arguments["<idf-file>"]
    print(arguments)
    if (arguments["--format"]):
        SEP, FEAT_SEP = parse_format(arguments["<format>"])
    print(SEP)
    print(FEAT_SEP)
    if (not check_func(func)):
        exit("{} does not exist.".format(func))
    globals()[func](f_in, f_out, f_dic)
