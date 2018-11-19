# software-eng-grp-project
Group A's repo for COMP2019 Software Engineering Group Project 

## Dependencies
pip install pdfminer.six

pip install rdflib

pip install sparqlwrapper

## Getting keywords of an article
# If file is pdf
open command prompt
```
python
>>from doc_processing import process_pdf2txt
>>keywords = import process_pdf2txt('path/to/file.pdf' , 'newfilename.txt')
```
this function will convert filename.pdf to newfilename.txt and saves it , 
then it returns an array of keywords tagged with Agrovoc concepts.

# If file is text
```
python
>>from doc_processing import process_pdf2txt
>>keywords = import process_pdf2txt('path/to/file.txt' ,)

```
