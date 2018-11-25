# software-eng-grp-project
Group A's repo for COMP2019 Software Engineering Group Project 

## Dependencies
install elastic search @ https://www.elastic.co/downloads/elasticsearch

pip install elasticsearch

pip install pdfminer.six

pip install rdflib

pip install sparqlwrapper

## Very first run
- install all dependencies
- change the es_process_path variable in search_server.py
```
#configuration
es_process_path = 'your/path/to/elasticsearch-6.5.0/bin/elasticsearch.bat'
```
- create index and index all test documents in test texts
```
>>import search_server
>>search_server.resetIndex()
>>search_server.batchIndexDocuments('/test texts/')
```
- then you can start searching
```
>>search_server.searchDoc('search for stuff')
```
- if you want to process more documents and then index them , use batch_process_txt / batch_process_pdf2txt 
- then use batchIndexDocument to index the processed documents

## Getting keywords , ntriples articles
### Individual pdf file
the processed document will then have two new files , docname_keywords.txt & docname_ntriples.txt
open command prompt
```
python
>>from doc_processing import process_pdf2txt
>>process_pdf2txt('path/to/file.pdf')
```
### Individual txt file
```
python
>>from doc_processing import process_pdf2txt
>>process_txt('path/to/file.txt')

```

### Batch processing files in a directoy
```
python
>>from doc_processing import batch_process_txt , batch_process_pdf2txt
>> #just provide them with the directory of the parent folder , then it will find all .txt / .prd files even if they are inside nested folders 
>> path = r'C:\Users\Acer\Desktop\Nottingham\Year 2\Group Project\NLP\software-eng-grp-project'
>> batch_process_pdf2txt(path)
```

## search_server.py
handles connection to the index server @ localhost:9200 and allows us to start searching

### how to search
relevant document  titles are returned in the first part.
in the second part , a few paragraphs from each document that are relevant are also returned.
```
import search_server
>>search_server.searchDoc("what is acid content of langsat")
```

search_server.py includes some helper functions :

### resetIndex()
deletes the index and uses putIndexMapping() to create a new index. Any changes to how we index the documents are done in putIndexMapping() , then we will call resetIndex() to apply the changes.

### batchIndexDocuments(path)
give the path to the parent directory , then it will index all the doc.txt , doc_keywords.txt & doc_ntriples.txt 



