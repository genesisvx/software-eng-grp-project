import nltk , custom_pdf2txt , sparql , pathlib , time, string

from custom_pdf2txt import convert_pdf_to_txt
from nltk import word_tokenize
from nltk.corpus import stopwords
from sparql import getConceptTag2 , getIntersectionOfNTriples

#helper function to stem out numbers
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def process_pdf2txt(path):
    newfilename = pathlib.Path(path).stem + '.txt'
    newfilename = pathlib.Path(path).parent / newfilename
    text = convert_pdf_to_txt(path , newfilename)
    
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    vocab = sorted(set(text))
    
    #remove all the number tokens
    for v in vocab:
        if v.startswith('a'):
            cutoff = vocab.index(v)
            break
    vocab = vocab[cutoff:len(vocab)-1]

    
    #remove all numbers and punctuations , and stopwords
    customStopwords = stopwords.words('english') + list(string.punctuation)
    vocab = [v for v in vocab if
                 not(is_number(v)) and v not in customStopwords]
      
    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    for v in vocab:
        # the foward slash is a syntax error in SPARQL 
        v = v.replace('\\','')
        potential_keywords.append({'word':v , 'baseTag': getConceptTag2(v)})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})

    #save the keywords / ntriples in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywords.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)    
              
    _file.close()
    
    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriples.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    _file = open(ntriplesFile , 'w+' , encoding='utf-8')
    ntriples = getIntersectionOfNTriples(tagged_keywords)
    for nt in ntriples:
        _file.write(nt + '\n')

    _file.close()

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
    vocab = sorted(set(text))
    
    #remove all the number tokens
    for v in vocab:
        if v.startswith('a'):
            cutoff = vocab.index(v)
            break
    vocab = vocab[cutoff:len(vocab)-1]
    
    #remove all numbers and punctuation and stopwords
    customStopwords = stopwords.words('english') + list(string.punctuation)
    vocab = [v for v in vocab if
                 not(is_number(v)) and v not in customStopwords]


    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    for v in vocab:
        # the foward slash is a syntax error in SPARQL 
        v = v.replace('\\','')
        potential_keywords.append({'word':v , 'baseTag': getConceptTag2(v)})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})

    #save the keywords in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywords.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)
        
    _file.close()

    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriples.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    _file = open(ntriplesFile , 'w+' , encoding='utf-8')
    ntriples = getIntersectionOfNTriples(tagged_keywords)
    for nt in ntriples:
        _file.write(nt + '\n')

    _file.close()
            

def batch_process_txt(directory):
    path = pathlib.Path(directory)

    for i in path.glob('**/*.txt'):
        process_txt(i)

def batch_process_pdf2txt(directory):
    path = pathlib.Path(directory)

    for i in path.glob('**/*.pdf'):
        try:
            print('Now processing {}\n'.format(i.stem))
            process_pdf2txt(i)
        except:
            print('Text extraction for {} is not allowed'.format(i.stem))
            pass
    
