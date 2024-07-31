import networkx as nx
import json
G = nx.DiGraph()
contact_id = '28050'
contacts_list = [
    '28050',
    '28131',
    '28130',
    '28129',
    '28128',
    '28127',
    '28126',
    '28112',
    'c',
    '28092',
    '28090',
    '28089',
    '28088',
    '28087',
    '28086',
    '28085',
    '28084',
    '28083',
    '28082',
    '28081',
    '28080',
    '28079',
    '28078',
    '28077',
    '10307'
]

contact_connections = [(contacts_list[0], connection) for connection in contacts_list[1:]]

# print("No. of 1st degree connections ", len(contacts_list[1:]))

print(contact_connections)

G.add_nodes_from(contacts_list)
G.add_edges_from(contact_connections)

# print([p for p in nx.all_shortest_paths(G, source='28050', target='3052')])
print(" ----- SAVING PATHS LIST ----- \n")

all_shortest_paths = dict(nx.all_pairs_shortest_path(G))

# all_shortest_paths_json_simple = json.dumps((all_shortest_paths)))
all_shortest_paths_json_pretty = json.dumps((all_shortest_paths["28050"]), sort_keys=True, indent=4)

f = open("/home/ec2-user/aw/altworkz/static/json/graphs/28050.json", "w")
#f.write(all_shortest_paths)
print(all_shortest_paths_json_pretty)
f.write(all_shortest_paths_json_pretty)
f.close()



all_shortest_paths = json.dumps((all_shortest_paths), sort_keys=True, indent=4)
print(all_shortest_paths)
#print(len(all_shortest_paths))
# print(json.dumps()


