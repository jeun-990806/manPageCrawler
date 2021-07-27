from nltk.tokenize import sent_tokenize
from nltk.tag import pos_tag
from nltk.stem import WordNetLemmatizer
import nltk
import nltk.sentiment.util


def getSentTokenizedList(text):
    return sent_tokenize(text)


def checkUnigramsIn(sent, unigrams, negation):
    return False not in nltk.nltk.sentiment.util.extract_unigram_feats(sent, unigrams, negation).values()


def searchTargetDescription(text, targets, negation):
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
        for target in targets:
            if False not in nltk.sentiment.util.extract_unigram_feats(words_adj, target, negation).values():
                result.append(sent)
                break
    return result


def searchWordWithTag(text, targets):
    result = []
    words = nltk.tokenize.word_tokenize(text)
    words = pos_tag(words)

    for word in words:
        if word[1] in targets:
            result.append(word[0])
    return result


def testCGF(text):
    grammar = nltk.CFG.fromstring("""
    S -> NP VP
    PP -> P NP
    NP -> Det N | Det N PP | 'I'
    VP -> V NP | VP PP
    Det -> 'an' | 'my'
    N -> 'elephant' | 'pajamas'
    V -> 'shot'
    P -> 'in'
    """)

    print(grammar.productions())
