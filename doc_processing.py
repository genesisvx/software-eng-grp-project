import nltk , custom_pdf2txt , sparql , pathlib , time, string , asyncio, concurrent.futures

from custom_pdf2txt import convert_pdf_to_txt
from nltk import word_tokenize
from nltk.corpus import stopwords
from sparql import getConceptTagVirtuoso , getNTriplesFromConceptVirtuoso , getIntersectionOfNTriplesVirtuoso

#helper function to stem out numbers
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

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

def ntripleIntersectionHelper(arr):
    ntriples = []
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(ntripleHelper(arr))

    for index , r in enumerate(res):
        potentialNTriples = r['results']['bindings']
        for keyword2 in arr:
            for potentialNTriple in potentialNTriples:
                if potentialNTriple['o']['value'].find(keyword2['baseTag']) >= 0:
                    tempStr = arr[index]['baseTag'] + " {} ".format(potentialNTriple['p']['value']) + keyword2['baseTag']
                    ntriples.append(tempStr)

    return ntriples

def process_pdf2txt(path):
    path = pathlib.Path(path)
    print('Now processing {}\n'.format(path.stem))
    newfilename = path.stem + '.txt'
    newfilename = path.parent / newfilename
    text = convert_pdf_to_txt(path , newfilename)
    
    cutoff_index=text.find('References')
    if(cutoff_index):
        text = text[0:cutoff_index]

    tokens = word_tokenize(text)
    text = nltk.Text(tokens)
    vocab = sorted(set(text))
    
    #remove all the number tokens
    cutoff = 0 
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

    #save the keywords in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywordsVirtuoso.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)
        
    _file.close()

    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriplesVirtuoso.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    _file = open(ntriplesFile , 'w+' , encoding='utf-8')
    ntriples = ntripleIntersectionHelper(tagged_keywords)
    for nt in ntriples:
        _file.write(nt + '\n')

    _file.close()

#returns tagged keywords that have correspond entry in AGROVOC
def process_txt(path):
    
    path = pathlib.Path(path)

    if path.stem.find('_keywords') != -1 or path.stem.find('_ntriples') != -1:
        return

    print('Now processing {}\n'.format(path.stem)) 
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

    #save the keywords in a file for easier pre-processing
    keywordsFile = pathlib.Path(path).stem + '_keywordsVirtuoso.txt'
    keywordsFilePath = pathlib.Path(path).parent / keywordsFile

    _file = open(keywordsFilePath , 'w+' , encoding='utf-8')
    for keyword in tagged_keywords:
        entry = "{} {}\n".format(keyword['word'],keyword['baseTag'])
        _file.write(entry)
        
    _file.close()

    #save the ntriples in a file for easier pre-processing
    ntriplesFile = pathlib.Path(path).stem + '_ntriplesVirtuoso.txt'
    ntriplesFile = pathlib.Path(path).parent / ntriplesFile

    _file = open(ntriplesFile , 'w+' , encoding='utf-8')
    ntriples = ntripleIntersectionHelper(tagged_keywords)
    for nt in ntriples:
        _file.write(nt + '\n')

    _file.close()
            

def batch_process_txt(directory):
    path = pathlib.Path(directory)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        files = path.glob('**/*.txt')
        executor.map(process_txt,files)


def batch_process_pdf2txt(directory):
    path = pathlib.Path(directory)
    files = path.glob('**/*.pdf')

    executor = concurrent.futures.ProcessPoolExecutor()
    futures = dict()

    for i in files:
        future = executor.submit(process_pdf2txt,i)
        futures[future] = i 

    for future in concurrent.futures.as_completed(futures):
        i = futures[future]
        try:
            print(future.results)
        except:
            print('Text extraction not allowed for {}\n'.format(i.stem))
            #print('Text extraction for {} is not allowed'.format(i.stem))
            

    
