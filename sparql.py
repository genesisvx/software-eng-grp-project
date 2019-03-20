from SPARQLWrapper import SPARQLWrapper, JSON , SPARQLExceptions
import urllib , http

#local mirror agrovoc endpoint
agrovoc_endpoint = "http://localhost:8890/sparql"

def getConceptTagVirtuoso(prefLabel):
	#acid vs acids , parasite vs parasites 
	#need to use wildcard * to be able to find match
	if len(prefLabel)>=4:
		modPrefLabel = prefLabel + '*'
	else:
		modPrefLabel = prefLabel
		
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
					FILTER (STRLEN("{1}")+1 >= STRLEN(?oo))
				}}
			}}

			  {{?concept skosxl:prefLabel ?subject}}
			  UNION
			  {{?concept skosxl:altLabel ?subject}}
			}}

			GROUP BY ?concept
			LIMIT 10
		""".format(modPrefLabel , prefLabel))
	sparql.setReturnFormat(JSON)
	try:
		#print('doing tagging for {}\n'.format(prefLabel))
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
		PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
		PREFIX agro: <http://aims.fao.org/aos/agrontology#>
		select * from <http://agrovocTest.com>
		WHERE {{
			<{0}> ?p ?o
			FILTER(
				?p = skos:broader||
				?p = skos:narrower||
				?p = skos:related||
				STRSTARTS(STR(?p), "http://aims.fao.org/aos/agrontology#")
			)
		}}
		LIMIT 100
		""".format(concept1))
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	return results

def isAlphabet(word):
	try:
		return word[0].encode('ascii').isalpha()
	except Exception:
		return False

def getLabelFromConceptVirtuoso(concept):
	sparql = SPARQLWrapper('http://localhost:8890/sparql')
	sparql.setQuery("""
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

		select ?oo where {{
			{{<{0}> skos:prefLabel ?o}}
			UNION
			{{<{0}> skos:altLabel ?o}}
			BIND(str(?o) as ?oo) 
			}}
		GROUP BY ?oo
		""".format(concept))
	sparql.setReturnFormat(JSON) 
	results = sparql.query().convert()
	results = [x['oo']['value'] for x in results['results']['bindings'] if isAlphabet(x['oo']['value'])]
	return results

# def getIntersectionOfNTriplesVirtuoso(keywordArr):
# 	ntriples = []
# 	for keyword in keywordArr:
# 		res = getNTriplesFromConceptVirtuoso(keyword['baseTag'])

# 		for potentialNTriple in res['results']['bindings']:
# 			for keyword2 in keywordArr:
# 				if potentialNTriple['o']['value'].find(keyword2['baseTag']) >= 0:
# 					tempStr = keyword['baseTag'] + " {} ".format(potentialNTriple['p']['value']) + keyword2['baseTag']
# 					ntriples.append(tempStr)

# 	return ntriples
    
    
    
    
        

