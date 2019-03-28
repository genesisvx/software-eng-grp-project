# software-eng-grp-project
Group A's repo for COMP2019 Software Engineering Group Project 

## Dependencies
install elastic search @ https://www.elastic.co/downloads/elasticsearch

install virtuoso open source version @ https://sourceforge.net/projects/virtuoso/files/

AGROVOC Core NT dump file @ http://aims.fao.org/agrovoc/releases

pip install elasticsearch

pip install pdfminer.six

pip install rdflib

pip install sparqlwrapper

pip install asyncio

pip install flask

## Very first run
- install all dependencies
- change the es_process_path variable in search_server.py
```
#configuration
es_process_path = 'your/path/to/elasticsearch-6.5.0/bin/elasticsearch.bat'
```
- preprocess the pdf files
```
>>import doc_processing
>>doc_processing.batch_process_pdf2txt('/test texts 2/')
```

- create index and index all test documents in test texts
```
>>import search_server
>>search_server.resetIndex()
>>search_server.batchIndexDocuments('/test texts 2/')
```
- create a new folder at virtuoso directory , eg D:\Virtuoso OpenSource 7.2\ontology and put AGROVOC file inside

- then edit this line in virtuoso.ini file in the database folder
```
DirsAllowed			= ., ../vad, ../ontology
```
- then start virtuoso , open cmd prompt with admin privileges
```
>cd D:\Virtuoso OpenSource 7.2\bin
>virtuoso +service list
vos         stopped
>virtuoso +service start +instance vos
```
- then execute isql.exe in bin folder , type in this line to load the AGROVOC file stored in the ontology folder
```
 DB.DBA.TTLP_MT (file_to_string_output('../ontology/agrovoc_2018-11-06_core.nt'),'','http://agrovocTest.com');
```
- then you can start searching
```
>>search_server.searchDoc('search for stuff')
```
- if you want to process more documents and then index them , use batch_process_txt / batch_process_pdf2txt 
- then use batchIndexDocument to index the processed documents

## Flask
- to start flask, open Powershell in the project location and run the following commands
```
$env:FLASK_APP = "flaskr"
$env:FLASK_ENV="development"
flask run --host=0.0.0.0
```

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



