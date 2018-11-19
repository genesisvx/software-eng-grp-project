# software-eng-grp-project
Group A's repo for COMP2019 Software Engineering Group Project 

## Dependencies
pip install pdfminer.six

pip install rdflib

pip install sparqlwrapper

## Converting PDF to .txt files
open command prompt
```
python
>>import custom_pdf2txt
>>convert = custom_pdf2txt.convert_pdf_to_txt
>>convert('Test1.pdf','Test1.txt')

```
if Test1.txt doesn't exist , then it will be created automatically , so there is no need for it to be created beforehand.
