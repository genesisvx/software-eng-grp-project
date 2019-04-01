import nltk , custom_pdf2txt , sparql , pathlib , time, string , asyncio, concurrent.futures ,re  , time , subprocess
import multiprocessing as mp

from custom_pdf2txt import convert_pdf_to_txt
from nltk import word_tokenize 
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.collocations import BigramCollocationFinder , TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures , TrigramAssocMeasures
from sparql import getConceptTagVirtuoso , getNTriplesFromConceptVirtuoso 

#helper function to stem out numbers
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

'''
async functions for parallel processing of network request to AGROVOC endpoint
'''
async def taggingHelper(arr):
    for a in arr:
        a = a.replace('\\','')

    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(
            None,
            getConceptTagVirtuoso,
            word
            )
        for word in arr
    ]
    responses =  await asyncio.gather(*futures)
    return responses

async def ntripleHelper(arr):
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(
            None,
            getNTriplesFromConceptVirtuoso,
            word['baseTag']
            )
        for word in arr
    ]
    responses = await asyncio.gather(*futures)
    return responses

'''
preprocessing of pdfs or txt files with AGROVOC and other onthologies.
'''


def removeNonAscii(s):
    return "".join(i for i in s if ord(i)<128)

def cleanSentence(sentence):
    s = sentence 

    s = removeNonAscii(s)

    #removes multiple whitespace and other escape characters
    s = " ".join(s.split())

    #deal with word that is broken up by hypens e.g some- thing -> something
    s = re.sub(r'- ' , '' , s)

    #remove punctuation
    regex = re.compile('[' + re.escape(string.punctuation) + '\\r\\t\\n]')
    s = regex.sub(" ", str(s))

    return s

def getBigrams(text , score_fn = BigramAssocMeasures.chi_sq , n=200):
    bigrams = []

    tokens = [t for t in word_tokenize(text) if len(t)>1]

    bigram_finder = BigramCollocationFinder.from_words(tokens)
    potential_bigrams = bigram_finder.nbest(score_fn,n)

    for bigram in potential_bigrams:
        if filterBigram(bigram):
            bigrams.append(bigram)

    potential_bigrams = bigram_finder.nbest(BigramAssocMeasures.raw_freq,n)

    for bigram in potential_bigrams:
        if filterBigram(bigram):
            bigrams.append(bigram)

    return bigrams

def getTrigrams(text , score_fn = TrigramAssocMeasures.chi_sq , n=200):
    trigrams = []

    tokens = [t for t in word_tokenize(text) if len(t)>1]

    trigram_finder = TrigramCollocationFinder.from_words(tokens)
    potential_trigrams = trigram_finder.nbest(score_fn,n)

    for trigram in potential_trigrams:
        if filterTrigram(trigram):
            trigrams.append(trigram)

    potential_trigrams = trigram_finder.nbest(TrigramAssocMeasures.raw_freq,n)

    for trigram in potential_trigrams:
        if filterTrigram(trigram):
            trigrams.append(trigram)

    return trigrams

def filterBigram(potential_bigram):
    acceptable_types = ('JJ', 'JJR', 'JJS', 'NN', 'NNS', 'NNP', 'NNPS')
    second_type = ('NN', 'NNS', 'NNP', 'NNPS')
    tags = nltk.pos_tag(potential_bigram)
    if tags[0][1] in acceptable_types and tags[1][1] in second_type:
        return True
    else:
        return False

def filterTrigram(potential_trigram):
    first_type = ('JJ', 'JJR', 'JJS', 'NN', 'NNS', 'NNP', 'NNPS')
    third_type = ('JJ', 'JJR', 'JJS', 'NN', 'NNS', 'NNP', 'NNPS')
    tags = nltk.pos_tag(potential_trigram)
    if tags[0][1] in first_type and tags[2][1] in third_type:
        return True
    else:
        return False

def jarWrapper(path):
        subprocess.call(['java' , '-cp' , './cermine-impl-1.14-SNAPSHOT-jar-with-dependencies.jar', 'pl.edu.icm.cermine.ContentExtractor' , '-outputs' , 'jats' , '-path' , str(path) ])

def process_pdf2txt(path):
    path = pathlib.Path(path)

    #save the keywords in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywordsVirtuoso.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriplesVirtuoso.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    #do not process the metadata txt files
    if path.stem.find('_keywords') != -1 or path.stem.find('_ntriples') != -1:
        return

    #already preprocesed
    if keywordsFilePath.is_file() or ntriplesFile.is_file():
        return

    newfilename = path.stem + '.txt'
    newfilename = path.parent / newfilename

    text = ''

    #this part of the code is to deal with edge cases where some pdfs have super weird layouts
    #decided to do this as i tested the pdf in question , and even after 6 hours it was still processing it
    queue = mp.Queue()
    proc= mp.Process(target = convert_pdf_to_txt , args = (path , newfilename ,queue))
    proc.start()
    try:
        text = queue.get(timeout = 10)
    except Exception:
        print("Took too long to convert pdf to txt...")
    
    proc.join(1)
    if proc.is_alive():
        print("Skipping this pdf...")
        proc.terminate()
        return

    #wasn't able to convert from pdf to txt
    if text == '':
        return

    #use CERMINE to get xml representation that will help identify paragraphs during indexing
    jarWrapper(path)

    #maybe this can be deleted?
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    sentences = sent_tokenize(text)
    sentences = [cleanSentence(sentence) for sentence in sentences]

    text = ''

    for s in sentences:
        text = text + s

    bigrams = []
    trigrams = []

    #returns as tuples . but to query agrovoc it needs to be string
    bigrams = getBigrams(text)
    trigrams = getTrigrams(text)

    bigrams = [" ".join(b) for b in bigrams]
    trigrams = [" ".join(t) for t in trigrams]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    vocab = sorted(set(text))
    
    #remove all the number tokens
    cutoff = 0
    for v in vocab:
        if v.startswith('a'):
            cutoff = vocab.index(v)
            break
    vocab = vocab[cutoff:len(vocab)]
    
    #remove all numbers and punctuation and stopwords
    customStopwords = stopwords.words('english') + list(string.punctuation)
    vocab = [v for v in vocab if
                 not(is_number(v)) and v not in customStopwords]

    vocab = vocab + bigrams + trigrams

    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    loop = asyncio.get_event_loop()
    print('Tagging with AGROVOC...')
    tempConcept = loop.run_until_complete(taggingHelper(vocab))

    for v in vocab:
        # the foward slash is a syntax error in SPARQL 
        v = v.replace('\\','')

    for v , concept in zip(vocab,tempConcept):
        potential_keywords.append({'word':v , 'baseTag':concept})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)
        
    _file.close()
    print('Finished tagging with AGROVOC...')

    # _file = open(ntriplesFile , 'w+' , encoding='utf-8')
    # print('Finding triples with AGROVOC...')
    # ntriples = loop.run_until_complete(ntripleHelper(tagged_keywords))
    # for index , nt in enumerate(ntriples) :
    #     if (len(nt['results']['bindings'])!=0):
    #         for nt in nt['results']['bindings']:
    #             ntString = tagged_keywords[index]['baseTag'] + " " + nt['p']['value'] + " " + nt['o']['value']
    #             _file.write(ntString + '\n')

    # _file.close()
    # print('Finished finding triples with AGROVOC...')
    
def process_txt(path):
    
    path = pathlib.Path(path)

    #save the keywords in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywordsVirtuoso.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriplesVirtuoso.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    #do not process the metadata txt files
    if path.stem.find('_keywords') != -1 or path.stem.find('_ntriples') != -1:
        return 100

    #already preprocessed
    if keywordsFilePath.is_file() or ntriplesFile.is_file():
        return 100

    file = open(path,'r',encoding="utf-8")
    text = file.read()

    #maybe this can be deleted?
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    sentences = sent_tokenize(text)
    sentences = [cleanSentence(sentence) for sentence in sentences]

    text = ''

    for s in sentences:
        text = text + s

    bigrams = []
    trigrams = []

    #returns as tuples . but to query agrovoc it needs to be string
    bigrams = getBigrams(text)
    trigrams = getTrigrams(text)

    bigrams = [" ".join(b) for b in bigrams]
    trigrams = [" ".join(t) for t in trigrams]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    vocab = sorted(set(text))
    
    #remove all the number tokens
    cutoff = 0
    for v in vocab:
        if v.startswith('a'):
            cutoff = vocab.index(v)
            break
    vocab = vocab[cutoff:len(vocab)]
    
    #remove all numbers and punctuation and stopwords
    customStopwords = stopwords.words('english') + list(string.punctuation)
    vocab = [v for v in vocab if
                 not(is_number(v)) and v not in customStopwords]

    vocab = vocab + bigrams + trigrams

    #may return empty after query AGROVOC , thus is potential keywords
    potential_keywords = []
    loop = asyncio.get_event_loop()
    tempConcept = loop.run_until_complete(taggingHelper(vocab))

    for v in vocab:
        # the foward slash is a syntax error in SPARQL 
        v = v.replace('\\','')

    for v , concept in zip(vocab,tempConcept):
        potential_keywords.append({'word':v , 'baseTag':concept})

    #cleaning up the query results by removing empty responses
    #format of query output refer to GitHub
    tagged_keywords = []
    for k in potential_keywords:
        if len(k['baseTag']['results']['bindings'])!=0:
            tagged_keywords.append({'word':k['word'] , 'baseTag':k['baseTag']['results']['bindings'][0]['concept']['value']})

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)
        
    _file.close()

            
def batch_process_txt(directory):
    path = pathlib.Path(directory)
    #files = [x for x in path.glob('**/*.txt') if not (x.name.find('_keywords')>=0 or x.name.find('_ntriples')>=0)]
    files = path.glob('**/*.txt')

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_txt,files)


def batch_process_pdf2txt(directory):
    start = time.time()
    path = pathlib.Path(directory)
    files = path.glob('**/*.pdf')

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = dict()
        count = 0

        for i in files:
            count += 1
            future = executor.submit(process_pdf2txt,i)
            futures[future] = i 

        for index , future in enumerate(concurrent.futures.as_completed(futures)):
            print("current pdf being processed:{}/{}\n".format(index+1,count))
            i = futures[future]
            
            try:
                future.result()
            except concurrent.futures.TimeoutError:
                print('{} took too long ..\n'.format(i.stem))
            except Exception:
                if future.exception() is not None:
                    print('Text extraction not allowed for {}\n'.format(i.stem))
                    #print('Text extraction for {} is not allowed'.format(i.stem))
    
    end = time.time()
    print('all done {}',format(end-start)) 


