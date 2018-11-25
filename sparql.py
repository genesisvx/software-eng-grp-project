from SPARQLWrapper import SPARQLWrapper, JSON
import urllib , http

agrovoc_endpoint = "http://agrovoc.uniroma2.it:3030/agrovoc/sparql"

#better formulated query?
def getConceptTag(prefLabel):
    attempts = 1;
    while attempts<5:
        try:
            print("doing tagging for {}\n".format(prefLabel))
            sparql = SPARQLWrapper(agrovoc_endpoint)
            sparql.setQuery("""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX agro: <http://aims.fao.org/aos/agrontology#>
                SELECT *
                WHERE {{
                    {{?concept skos:prefLabel ?label}}
                    UNION
                    {{?concept skos:altLabel ?label}}
                    .
                    FILTER regex(str(?label),"^{}$","i")
                }}
                GROUP BY ?concept
                """.format(prefLabel))
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            print(results)
            break
        except (urllib.error.URLError,TimeoutError):
            attempts +=1
        except http.client.RemoteDisconnected :
            attempts +=1
    return results

def getConceptTag2(prefLabel):
    attempts = 1;
    while attempts<5:
        try:
            print("doing tagging for {}\n".format(prefLabel))
            sparql = SPARQLWrapper(agrovoc_endpoint)
            sparql.setQuery("""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX agro: <http://aims.fao.org/aos/agrontology#>
                SELECT *
                WHERE {{
                    {{?concept skos:prefLabel "{0}"@en}}
                    UNION
                    {{?concept skos:prefLabel "{1}"@en}}
                    UNION
                    {{?concept skos:prefLabel "{0}"@cs}}
                    UNION
                    {{?concept skos:prefLabel "{1}"@cs}}
                    UNION
                    {{?concept skos:prefLabel "{0}"@tr}}
                    UNION
                    {{?concept skos:prefLabel "{1}"@tr}}
                    UNION
                    {{?concept skos:prefLabel "{0}"@fr}}
                    UNION
                    {{?concept skos:prefLabel "{1}"@fr}}
                    UNION
                    {{?concept skos:prefLabel "{0}"@de}}
                    UNION
                    {{?concept skos:prefLabel "{1}"@de}}
                    UNION 
                    {{?concept skos:altLabel "{0}"@en}}
                    UNION
                    {{?concept skos:altLabel "{1}"@en}}
                    UNION
                    {{?concept skos:altLabel "{0}"@cs}}
                    UNION
                    {{?concept skos:altLabel "{1}"@cs}}
                    UNION
                    {{?concept skos:altLabel "{0}"@tr}}
                    UNION
                    {{?concept skos:altLabel "{1}"@tr}}
                    UNION
                    {{?concept skos:altLabel "{0}"@fr}}
                    UNION
                    {{?concept skos:altLabel "{1}"@fr}}
                    UNION
                    {{?concept skos:altLabel "{0}"@de}}
                    UNION
                    {{?concept skos:altLabel "{1}"@de}}
                    UNION
                    {{?concept skos:prefLabel "{2}"@en}}
                    UNION
                    {{?concept skos:altLabel "{2}"@en}}  
                }}
                GROUP BY ?concept
                """.format(prefLabel , prefLabel.title() , prefLabel+'s'))
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            break
        except (urllib.error.URLError,TimeoutError):
            attempts +=1
        except http.client.RemoteDisconnected :
            attempts +=1
    return results

def getNTriplesFromConcept(concept1):
    ntriple = None;
    attempts = 1;
    while attempts<5:
        try:
            print("getting ntriples attempt {}\n".format(attempts))
            sparql = SPARQLWrapper(agrovoc_endpoint)
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
            break
        except (urllib.error.URLError , TimeoutError):
            attempts +=1
    return results

def getIntersectionOfNTriples(keywordArr):
    ntriples = []
    for keyword in keywordArr:
        res = getNTriplesFromConcept(keyword['baseTag'])

        for potentialNTriple in res['results']['bindings']:
            for keyword2 in keywordArr:
                if potentialNTriple['o']['value'].find(keyword2['baseTag']) >= 0:
                    tempStr = keyword['baseTag'] + " {} ".format(potentialNTriple['p']['value']) + keyword2['baseTag']
                    ntriples.append(tempStr)

    return ntriples
    
    
    
    
        

