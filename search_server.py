from elasticsearch import Elasticsearch
import subprocess
from pathlib import Path

#configuration
es_process_path = 'C:/Users/Acer/Desktop/Nottingham/Year 2/Group Project/NLP/elasticsearch-6.5.0/bin/elasticsearch.bat'
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
            'title' : {"type":"text"},
            'content' : {"type":"text"},
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



def documentIndex(path):
    path = Path(path)
    files = []

    for i in path.glob('**/*.txt'):
        if i.stem.find('_keywords') == -1 and i.stem.find('_ntriples') == -1:
            files.append(i)

    breakpoint()
    
    #preparing index body
    for f in files:
        concepts = []
        ntriples = []
	
        title = f.stem
        content = open(f , 'r' , encoding = 'utf-8').read()
        #removing escape characters
        content = " ".join(content.split())
        
        keywords_path = f.stem + '_keywords.txt'
        keywords_path = f.parent / keywords_path
        
        if keywords_path.is_file():
            tempFile = open(keywords_path , 'r')
            for line in tempFile:
                tempArr= line.strip().split()
                concepts.append(tempArr[1])
            tempFile.close()

        ntriples_path = f.stem + '_ntriples.txt'
        ntriples_path = f.parent / ntriples_path

        if ntriples_path.is_file():
            tempFile = open(ntriples_path , 'r')
            for line in tempFile:
        	    ntriples.append(line.strip())
            tempFile.close()

        body = {
		"title" : title ,
		"content" : content ,
		"ntriples" : ntriples ,
		"concepts" : concepts ,
        }

        es.index(index,doc_type,body)
	

			




    





            

