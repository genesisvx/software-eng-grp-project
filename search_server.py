import subprocess , nltk , gensim , asyncio , time , concurrent.futures ,math
from sparql import getConceptTagVirtuoso , getNTriplesFromConceptVirtuoso , getLabelFromConceptVirtuoso
from elasticsearch import Elasticsearch , helpers
from pathlib import Path
from doc_processing import taggingHelper , ntripleHelper , getBigrams , getTrigrams
import xml.etree.ElementTree as ET

#configuration
es_process_path = 'A:\janse\Documents\elasticsearch-6.5.4\bin\elasticsearch.bat'
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
#model = gensim.models.KeyedVectors.load_word2vec_format('C:/Users/Acer/Downloads/GoogleNews-vectors-negative300.bin/GoogleNews-vectors-negative300.bin',binary=True,limit=500000)

def putIndexMapping():
    mappings = {

        "properties":{
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
    
def searchDoc(query):
    potential_concepts = []
    concepts = []
    broader = []
    broaderRaw = []
    narrower = []
    narrowerRaw = []
    tokens = nltk.word_tokenize(query)
    tokens = [t for t in tokens if t not in nltk.corpus.stopwords.words('english')]
    outputList = []
    
    bigrams = getBigrams(" ".join(tokens))
    trigrams = getTrigrams(" ".join(tokens))
    bigrams = [" ".join(b) for b in bigrams]
    trigrams = [" ".join(t) for t in trigrams]
    tokens = tokens + bigrams + trigrams 

    #synonyms set for the tokens
    synset = []
	
    #for t in tokens:
    #   try:
    #        query = model.similar_by_word(t,topn=5)
    #        for q in query:
    #            synset.append(q[0])
    #    except KeyError:
    #        pass
    
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    tempConcept = loop.run_until_complete((taggingHelper(tokens)))

    for t , concept in zip(tokens,tempConcept):
        potential_concepts.append({'word':t , 'baseTag':concept})

    #remove empty concepts
    for t in potential_concepts:
        if len(t['baseTag']['results']['bindings'])!=0:
            concepts.append({'baseTag':t['baseTag']['results']['bindings'][0]['concept']['value']})
	
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
                                {"match" : {"paragraph":{"query":broaderRaw , "boost":1.5}}},
                                {"match" : {"paragraph":{"query":narrowerRaw , "boost":1.5}}},
                                {"match" : {"title":query}},
                                {"terms" : {"concepts":narrower , "boost":2}},
                                {"terms" : {"concepts":broader , "boost":2}},
                                {"terms_set" : {"concepts":{"terms":temp_concepts , "minimum_should_match_script":{"source":"params['min_terms']" , "params":{"min_terms":math.ceil(len(temp_concepts)*0.5)}}}}}
                            ] ,
                        # "must" : {
                        #         "terms_set" : {"concepts":{"terms":temp_concepts , "minimum_should_match_script":{"source":"params['min_terms']" , "params":{"min_terms":1}}}},
                        #     },
                        
                    }
                
            },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
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
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
                    }
                    } ,
                }
            }
    else:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":query}} ,
                                {"match" : {"title":query}},
                            ] ,
                        
                    },


                },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
                    }
                    } ,
                }
            }

    data = es.search(index , doc_type , body , request_timeout = 10000)

    for d in data['aggregations']['by_title']['buckets']:
        print(d['key']) #print title of relevant docs

    for d in data['aggregations']['by_title']['buckets']:
        i = 0
        for entry in d['by_top_hits']['hits']['hits']:
            i = i + 1
            if i > 4:
                break
          #  print(entry['_score'])
           # print(entry['_source']['title'])
          #  print(entry['_source']['paragraph'])
            outputList.append(entry['_source']['title'])
            outputList.append('\n')
            outputList.append(entry['_source']['paragraph'])
            outputList.append('\n')
            outputList.append('*'*100)
            outputList.append('\n')
            outputList.append('\n')
    return outputList
			


#prototype
def searchDocPrototype():
    query = "acid content langsat"
    ntriples = []
    temp_concepts = ['http://aims.fao.org/aos/agrovoc/c_24347' , 'http://aims.fao.org/aos/agrovoc/c_92']

    if len(temp_concepts) != 0 and len(ntriples) !=0:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":query}} ,
                                {"match" : {"title":query}},
                                {"terms" : {"ntriples.raw":ntriples}},
                            ] ,
                        "must" : {
                                {"terms" : {"concepts":temp_concepts}},
                            },
                        
                    }
                
            },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
                    }
                    } ,
                }
        }
    elif len(temp_concepts) != 0 and len(ntriples) == 0:
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
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
                    }
                    } ,
                }
            }
    else:
        body = {
            "query": {
                "bool" : {
                        "should" : [
                                {"match" : {"paragraph":query}} ,
                                {"match" : {"title":query}},
                            ] ,
                        
                    },


                },
            "aggs" : {
                "by_title" : {
                    "terms" : {
                        "field" : "title.raw" ,
                        "order" : {"max_score":"desc"},
                        } ,
                    "aggs" : {
                        "by_top_hits" : {"top_hits" : {"size":15}},
                        "max_score" : {"max":{"script":{"source":"_score"}}}
                    }
                    } ,
                }
            }

    breakpoint()
    data = es.search(index , doc_type , body)

    for d in data['aggregations']['by_title']['buckets']:
        print(d['key']) #print title of relevant docs

    for d in data['aggregations']['by_title']['buckets']:
        i = 0
        for entry in d['by_top_hits']['hits']['hits']:
            i = i + 1
            if i > 4:
                break
            print(entry['_source']['title'])
            print(entry['_source']['paragraph'] + '\n')
            print('*'*100)
            


			




    





            

