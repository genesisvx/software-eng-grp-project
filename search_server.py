import subprocess , nltk
from sparql import getConceptTag2 , getIntersectionOfNTriples
from elasticsearch import Elasticsearch , helpers
from pathlib import Path

#configuration
es_process_path = 'D:/elasticsearch-6.5.0/bin/elasticsearch.bat'
index = 'agrovoc'
doc_type = '_doc'
port = 9200
host = 'localhost'
#start process
p = subprocess.Popen(es_process_path)
#conncet to node
es = Elasticsearch([{'host':host , 'port':port}])

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
            'ntriples': {
                "type" : "text" ,
                "fields" : {
                    "raw": { "type" : "keyword" }
                    },
                },
            'concepts': {"type":"keyword"},
        }
    }
    
    es.indices.put_mapping(index=index , doc_type=doc_type , body=mappings)

def resetIndex():
    if es.indices.exists(index):
        es.indices.delete(index)

    es.indices.create(index)
    putIndexMapping()



def batchIndexDocuments(path):
    path = Path(path)
    files = []

    for i in path.glob('**/*.txt'):
        if i.stem.find('_keywords') == -1 and i.stem.find('_ntriples') == -1:
            files.append(i)

    #preparing index body
    for f in files:
        print("now indexing {}\n".format(f.stem))
        concepts = []
        ntriples = []

        title = f.stem
        content = open(f , 'r' , encoding = 'utf8' , errors='ignore').read()
        #removing escape characters
        para = content.split('\n\n')
        for p in para:
            p = " ".join(p.split())
        
        keywords_path = f.stem + '_keywords.txt'
        keywords_path = f.parent / keywords_path
        
        if keywords_path.is_file():
            tempFile = open(keywords_path , 'r' , encoding='utf8',errors ='ignore')
            for line in tempFile:
                tempArr= line.strip().split()
                concepts.append(tempArr[1])
            tempFile.close()

        ntriples_path = f.stem + '_ntriples.txt'
        ntriples_path = f.parent / ntriples_path

        if ntriples_path.is_file():
            tempFile = open(ntriples_path , 'r' , encoding ='utf8' ,errors='ignore')
            for line in tempFile:
        	    ntriples.append(line.strip())
            tempFile.close()

        body = []
        for i ,p in enumerate(para):
            action = {
                    "_index":index ,
                    "_type":doc_type ,
                    "title" : title ,
                    "paragraph_num" : para.index(p) ,
                    "paragraph" : p ,
                    "ntriples" : ntriples ,
                    "concepts" : concepts ,
            }
        
            body.append(action)

            #batch the bulk operation to prevent MemoryError
            if(i>0 and i%100==0):
                helpers.bulk(es , body)
                body = []
 
        #insert remainder of paragraphs
        helpers.bulk(es , body)

def searchDoc(query):
    potential_concepts = []
    concepts = []
    ntriples = []
    tokens = nltk.word_tokenize(query)
    tokens = [t for t in tokens if t not in nltk.corpus.stopwords.words('english')]
    
    #try to find concepts from tokens
    for t in tokens:
        potential_concepts.append({'baseTag':getConceptTag2(t)})

    #remove empty concepts
    for t in potential_concepts:
        if len(t['baseTag']['results']['bindings'])!=0:
            concepts.append({'baseTag':t['baseTag']['results']['bindings'][0]['concept']['value']})
	
    #get ntriples
    ntriples = getIntersectionOfNTriples(concepts)

    #remove stopwords from tokens and combine them into query again
    #to facilitate in full text search
    tokens = [t for t in tokens if t not in nltk.corpus.stopwords.words('english')]
    query = " ".join(tokens)


    temp_concepts = []
    for c in concepts:
        temp_concepts.append(c['baseTag'])
    breakpoint()

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
            
    

			




    





            

