import subprocess , nltk , gensim , asyncio , time , concurrent.futures ,math , time ,re , string
from sparql import getConceptTagVirtuoso , getNTriplesFromConceptVirtuoso , getLabelFromConceptVirtuoso
from elasticsearch import Elasticsearch , helpers
from pathlib import Path
from doc_processing import taggingHelper , ntripleHelper , getBigrams , getTrigrams
import xml.etree.ElementTree as ET
import numpy as np

#configuration
es_process_path = 'D:/elasticsearch-6.5.0/bin/elasticsearch.bat'
index = 'agrovoctest'
doc_type = '_doc'
port = 9200
host = 'localhost'
#start process
#p = subprocess.Popen(es_process_path)
#conncet to node
es = Elasticsearch([{'host':host , 'port':port}])

#use 500k , reduce 5/6th of memory requirements and it seems sufficient for use 
#https://stackoverflow.com/questions/50478046/memory-error-when-using-gensim-for-loading-word2vec
model = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/Acer/Downloads/GoogleNews-vectors-negative300.bin/GoogleNews-vectors-negative300.bin',binary=True,limit=500000)

def putIndexMapping():
    mappings = {

        "properties":{
            'link': {"type":"keyword"},
            'title' : {"type":"text",
                       "fields" : {
                            "raw" : {"type":"keyword"}
                           },
                       },
            'paragraph_num': {"type":"integer"},
            'paragraph' : {"type":"text"},
            'concepts': {"type":"keyword"},
        }
    }
    
    es.indices.put_mapping(index=index , doc_type=doc_type , body=mappings)

def resetIndex():
    if es.indices.exists(index):
        es.indices.delete(index)

    settings = {
        "settings":{
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }
    }
    es.indices.create(index , body = settings)
    putIndexMapping()


def indexHelper(f):
    if f.stem.find('_keywords')>0:
        return
      
    #if f.stem.find('_keywords'):
        #return
    concepts = []
    ntriples = []
    xmlFile = Path(str(f).replace('.txt','.cermxml'))
    title = f.stem
    #if xml file is less that 10kb , eg 10000 bytes , theres a problem and we go back naive way of finding paragraphs
    if xmlFile.is_file() and xmlFile.stat().st_size > 10000:
        tree = ET.parse(xmlFile)
        para = []
        for elem in tree.iter():
            if elem.tag == 'p':
                para.append(elem.text)
                #para.append(" ".join(elem.text).split())
    else:
        #something wrong with pdf to txt conversion
        if f.stat().st_size<10000:
            return
        content = open(f , 'r' , encoding = 'utf8' , errors='ignore').read()
        #removing escape characters
        para = content.split('\n\n')
        for p in para:
            p = " ".join(p.split())
    
    keywords_path = f.stem + '_keywordsVirtuoso.txt'
    keywords_path = f.parent / keywords_path
    
    if keywords_path.is_file():
        tempFile = open(keywords_path , 'r' , encoding='utf8',errors ='ignore')
        for line in tempFile:
            tempArr= line.strip().split()
            concepts.append(tempArr[1])
        tempFile.close()

    body = []
    for i ,p in enumerate(para):
        action = {
                "_index":index ,
                "_type":doc_type ,
                "link":str(f.resolve()).replace('.txt','.pdf'),
                "title" : title ,
                "paragraph_num" : para.index(p) ,
                "paragraph" : p ,
                "concepts" : concepts ,
        }
    
        body.append(action)

        #batch the bulk operation to prevent MemoryError
        if(i>0 and i%1000==0):
            helpers.bulk(es , body , request_timeout = 100)
            body = []

    #insert remainder of paragraphs
    helpers.bulk(es , body , request_timeout = 100)

def batchIndexDocuments(path):
    settings = {
        "index":{
            "refresh_interval" : "60m"
        }
    }
    es.indices.put_settings(settings)

    start = time.time()
    path = Path(path)
    files = []

    for i in path.glob('**/*.txt'):
        keywords_path = i.stem + '_keywordsVirtuoso.txt'
        keywords_path = i.parent / keywords_path

        if keywords_path.is_file or (i.stem.find('_keywords') == -1 and i.stem.find('_ntriples') == -1):
            files.append(i)

    total_count = len(list(files))
    current_count = 0 

    files = []
    for i in path.glob('**/*.txt'):
        keywords_path = i.stem + '_keywordsVirtuoso.txt'
        keywords_path = i.parent / keywords_path

        if keywords_path.is_file or (i.stem.find('_keywords') == -1 and i.stem.find('_ntriples') == -1):
            files.append(i)

    with concurrent.futures.ProcessPoolExecutor(max_workers = 4) as executor:
        futures = dict()
        for i in files:
            future =  executor.submit(indexHelper,i)
            futures[future] = i
        
        for index , future in enumerate(concurrent.futures.as_completed(futures)):
            print("current document being index {}/{}".format(index+1,total_count))
            try:
                future.result()
            except Exception:
                if future.exception() is not None:
                    print(future.exception()) 
                    print('indexing failed for {}\n'.format(futures[future]))

    end = time.time()
    print('finished indexing after {}'.format(end-start))

    settings = {
        "index":{
            "refresh_interval" : "1s"
        }
    }
    es.indices.put_settings(settings)

def avg_vector(paragraph, model=model, num_features=300, index2word_set=model):
    #function to average all words vectors in a given paragraph
    #remove punctuation
    regex = re.compile('[' + re.escape(string.punctuation) + '\\r\\t\\n]')
    paragraph = regex.sub(" ", str(paragraph))

    words = paragraph.split()

    featureVec = np.zeros((num_features,), dtype="float32")
    nwords = 0

    for word in words:
        if word in index2word_set:
            nwords = nwords+1
            featureVec = np.add(featureVec, model[word])

    if nwords>0:
        featureVec = np.divide(featureVec, nwords)
    return featureVec

def cosine_similarity(vec1,vec2):
    dot = np.dot(vec1,vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    cos = dot / ( norm1 * norm2 )
    if math.isnan(float(cos)):
        cos = 1
    return cos 
    
def searchDoc(query):   	
    potential_concepts = []
    concepts = []
    conceptRaw = []
    broader = []
    broaderRaw = []
    narrower = []
    narrowerRaw = []
    tokens = nltk.word_tokenize(query)
    tokens = [t for t in tokens if t not in nltk.corpus.stopwords.words('english')]
    outputList = []
    start = time.time()
    bigrams = getBigrams(" ".join(tokens))
    trigrams = getTrigrams(" ".join(tokens))
    bigrams = [" ".join(b) for b in bigrams]
    trigrams = [" ".join(t) for t in trigrams]
    tokens = tokens + bigrams + trigrams 
    
    asyncio.set_event_loop(asyncio.new_event_loop())      
    loop = asyncio.get_event_loop()
    tempConcept = loop.run_until_complete((taggingHelper(tokens)))

    for t , concept in zip(tokens,tempConcept):
        potential_concepts.append({'word':t , 'baseTag':concept})

    #remove empty concepts
    for t in potential_concepts:
        if len(t['baseTag']['results']['bindings'])!=0:
            concepts.append({'baseTag':t['baseTag']['results']['bindings'][0]['concept']['value']})

    for c in concepts:
    	conceptRaw += getLabelFromConceptVirtuoso(c['baseTag'])
    conceptRaw = " ".join(conceptRaw)

    #get ntriples
    tempNtriples = loop.run_until_complete(ntripleHelper(concepts))

    for i , nt in enumerate(tempNtriples) :
        if (len(nt['results']['bindings'])!=0):
            for nt in nt['results']['bindings']:
                if nt['p']['value'].find('#narrower')>0:
                    narrower.append(nt['o']['value'])
                elif nt['p']['value'].find('#broader')>0:
                    broader.append(nt['o']['value'])

    for b in broader:
        broaderRaw += getLabelFromConceptVirtuoso(b)
    broaderRaw = " ".join(broaderRaw)    

    for n in narrower:
        narrowerRaw += getLabelFromConceptVirtuoso(n)
    narrowerRaw = " ".join(narrowerRaw)    


    #remove stopwords from tokens and combine them into query again
    #to facilitate in full text search
    tokens = [t for t in tokens if t not in nltk.corpus.stopwords.words('english')]
    query = " ".join(tokens)

    temp_concepts = []
    for c in concepts:
        temp_concepts.append(c['baseTag'])

    if len(temp_concepts) != 0 and len(tempNtriples) > 0:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":query}} ,
                                {"match" : {"paragraph":conceptRaw}},
                                {"match" : {"paragraph":{"query":broaderRaw , "boost":0.5}}},
                                {"match" : {"paragraph":{"query":narrowerRaw , "boost":0.5}}},
                                {"match" : {"title":query}},
                                {"terms" : {"concepts":narrower , "boost":0.5}},
                                {"terms" : {"concepts":broader , "boost":0.5}},
                                {"terms_set" : {"concepts":{"terms":temp_concepts , "minimum_should_match_script":{"source":"params['min_terms']" , "params":{"min_terms":math.ceil(len(temp_concepts)*0.5)}}}}}
                            ] ,
                        # "must" : {
                        #         "terms_set" : {"concepts":{"terms":temp_concepts , "minimum_should_match_script":{"source":"params['min_terms']" , "params":{"min_terms":1}}}},
                        #     },
                        
                    }
                
            },
            "highlight" : {
                "fields":{
                    "paragraph":{},
                },
                "number_of_fragments":0,

            },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"highlight":{"fields":{"paragraph":{}} , "number_of_fragments":0} , "size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}},
                    }
                    } ,
                }
        }
    elif len(temp_concepts) != 0 and len(tempNtriples) == 0:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":query}} ,
                                {"match" : {"title":query}},
                            ] ,
                        "must" : {
                                "terms" : {"concepts":temp_concepts},
                            },
                        
                    }
                },
            "highlight" : {
                "fields":{
                    "paragraph":{},
                },
                "number_of_fragments":0,

            },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"highlight":{"fields":{"paragraph":{}} , "number_of_fragments":0} , "size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}},
                    }
                    } ,
                }
            }
    else:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":{"query":query , "fuzziness":2} }} ,
                                {"match" : {"title":query}},
                            ] ,
                        
                    },


                },
            "highlight" : {
                "fields":{
                    "paragraph":{},
                },
                "number_of_fragments":0,

            },                
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"highlight":{"fields":{"paragraph":{}} , "number_of_fragments":0} , "size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}},
                    }
                    } ,
                }
            }

    data = es.search(index , doc_type , body , request_timeout = 10000)
    

    for d in data['aggregations']['by_title']['buckets']:
        print(d['key']) #print title of relevant docs
    end = time.time()
    print(end-start)
    for d in data['aggregations']['by_title']['buckets']:
        i = 0
        for entry in d['by_top_hits']['hits']['hits']:
            i = i + 1
            if i > 4:
                break
          #  print(entry['_score'])
        # print(entry['_source']['title']+'\n')
        # print(entry['_source']['paragraph']+'\n')
        # print(entry['highlight']['paragraph'][0]+'\n')
            try: 
                outputList.append({'score': entry['_score'],'link':entry['_source']['link'] , 'title':entry['_source']['title'] , 'paragraph':entry['highlight']['paragraph'][0]})
            except KeyError:
                outputList.append({'score': entry['_score'],'link':entry['_source']['link'] , 'title':entry['_source']['title'] , 'paragraph':entry['_source']['paragraph']})

    qVector = avg_vector(query)

    for output in outputList:
        paraVector = avg_vector(output['paragraph'])
        cosim = cosine_similarity(qVector,paraVector)
        output['score'] = output['score'] * cosim

    outputList.sort(key=lambda x:x['score'] , reverse=True)
    print(outputList)
    loop.close() # close event loop
    return outputList




			




    





            

