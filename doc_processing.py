import nltk , custom_pdf2txt , sparql

from custom_pdf2txt import convert_pdf_to_txt
from nltk import word_tokenize
from sparql import getConceptTag

def process_pdf2txt(path , newfilename):
    text = convert_pdf_to_txt(path ,newfilename)
    
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    words = [w.lower() for w in text]
    vocab = sorted(set(words))
    
    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    for v in vocab:
        potential_keywords.append({'word':v , 'baseTag': getConceptTag(v)})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})
              
    return tagged_keywords

#returns tagged keywords that have correspond entry in AGROVOC
def process_txt(path):
    file = open(path,'r',encoding="utf-8")
    text = file.read()

    #maybe this can be deleted?
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    words = [w.lower() for w in text]
    vocab = sorted(set(words))

    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    for v in vocab:
        potential_keywords.append({'word':v , 'baseTag': getConceptTag(v)})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})
              
    return tagged_keywords
    
