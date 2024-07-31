import networkx as nx
import os
import json

from .elasticsearch import ElasticSearch

def get_contact_connections (context, user_id, contact_id):

    print("################################ EXPERIMENTAL GRAPH ################################\n")

    if os.path.exists('/home/ec2-user/aw/altworkz/static/json/graphs/connections-graph.xml'):
    
        g = nx.DiGraph(nx.read_graphml("/home/ec2-user/aw/altworkz/static/json/graphs/connections-graph.xml"))
        second_degree_contact_list = set()
        
        for result_contact in context['results']:
        
            print("Getting Result Contact ")
            print(result_contact['contact_id'])
            
            try:

                for shortest_path in nx.all_shortest_paths(g, str(contact_id), str(result_contact['contact_id'])):

                    print("Shortest Path ")
                    print(shortest_path)     


                    for node in shortest_path[1:]:
                                                               
                        print("node ", node)

                        second_degree_contact_list.add(node)
                        
                        if node not in context['second_degree_connection_details']:
                        
                            context['second_degree_connection_details'][node] = {} 

                              
            except:
            
                print("Exception")

            cil = ElasticSearch(user_id)
            cil = cil.get_contacts_by_id(list(second_degree_contact_list))
            print(cil)
            cil = cil['hits']['hits']  
            context['sec_degree_connection_details'] = {contact_detail['_source']['contact_id']: contact_detail['_source'] for contact_detail in cil}

            print('cil ', cil)
    
            print(json.dumps(context['sec_degree_connection_details'], sort_keys=False, indent=4)) 


                
    print("################################ EXPERIMENTAL GRAPH ################################\n")
                
    
    return
             
    connection_graph = json.loads(open("/home/ec2-user/aw/altworkz/static/json/graphs/connections-graph.xml", "r").read())
    context['connection_graph'] = connection_graph 
    context['second_degree_connection_details'] = {} 
    second_degree_contact_list = set()
        
        
    for dest_node, cg in connection_graph.items():

        second_degree_contact_list.add(dest_node)    

        print("cg", cg)

        for path in cg[1:]:

            for node in path:

                second_degree_contact_list.add(node)
                
                if node not in context['second_degree_connection_details']:
                
                    context['second_degree_connection_details'][node] = {} 

    cil = ElasticSearch(request.user.id)
    cil = cil.get_contacts_by_id(list(second_degree_contact_list))
    # print(cil)
    cil = cil['hits']['hits']    
