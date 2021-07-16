from nltk.tokenize import sent_tokenize
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
import nltk


def searchTargetDescription(text, target):
    result = []
    n = WordNetLemmatizer()

    for sent in sent_tokenize(text):
        words = nltk.tokenize.word_tokenize(sent)
        words = pos_tag(words)
        words_adj = []
        for w in words:
            if 'V' in w[1]:
                words_adj.append(n.lemmatize(w[0], 'v'))
            else:
                words_adj.append(n.lemmatize(w[0]))
        if len(set(target) - set(words_adj)) == 0 or 'All' in words_adj:
            result.append(sent)

    return result
