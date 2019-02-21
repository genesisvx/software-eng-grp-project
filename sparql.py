from SPARQLWrapper import SPARQLWrapper, JSON , SPARQLExceptions
import urllib , http

#local mirror agrovoc endpoint
agrovoc_endpoint = "http://localhost:8890/sparql"

def getConceptTagVirtuoso(prefLabel):
	sparql = SPARQLWrapper(agrovoc_endpoint)
	sparql.setQuery("""
			PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
			select ?concept from <http://agrovocTest.com> 
			WHERE{{
			{{
				select ?oo (SAMPLE(?s) as ?subject) from <http://agrovocTest.com> 
				WHERE {{
					?s skosxl:literalForm ?o.
					?o bif:contains "'{0}'"
					BIND(str(?o) as ?oo)
					FILTER (?oo = "{0}")
				}}
			}}

			  {{?concept skosxl:prefLabel ?subject}}
			  UNION
			  {{?concept skosxl:altLabel ?subject}}
			}}

			GROUP BY ?concept
			LIMIT 10
		""".format(prefLabel))
	sparql.setReturnFormat(JSON)
	try:
		results = sparql.query().convert()
	except (urllib.error.HTTPError , SPARQLExceptions.EndPointInternalError):
		#some pdfs have weird characters that will cause errors for Virtuoso server , so for those cases return an empty results
		results = {'head': {'link': [], 'vars': ['concept']}, 'results': {'distinct': False, 'ordered': True, 'bindings': []}}
	except (urllib.error.HTTPError , SPARQLExceptions.QueryBadFormed):
		#strings with inappropriate characters
		results = {'head': {'link': [], 'vars': ['concept']}, 'results': {'distinct': False, 'ordered': True, 'bindings': []}}

	return results

def getNTriplesFromConceptVirtuoso(concept1):
	ntriple = None;   
	sparql = SPARQLWrapper('http://localhost:8890/sparql')
	sparql.setQuery("""
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
		PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
		PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
		PREFIX agro: <http://aims.fao.org/aos/agrontology#>
		SELECT *
		WHERE {{
			  <{}> ?p ?o
		}}
		""".format(concept1))
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	return results

def getIntersectionOfNTriplesVirtuoso(keywordArr):
	ntriples = []
	for keyword in keywordArr:
		res = getNTriplesFromConceptVirtuoso(keyword['baseTag'])

		for potentialNTriple in res['results']['bindings']:
			for keyword2 in keywordArr:
				if potentialNTriple['o']['value'].find(keyword2['baseTag']) >= 0:
					tempStr = keyword['baseTag'] + " {} ".format(potentialNTriple['p']['value']) + keyword2['baseTag']
					ntriples.append(tempStr)

	return ntriples
    
    
    
    
        

