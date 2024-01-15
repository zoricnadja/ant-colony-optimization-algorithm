import re
import networkx as nx
import math
import random
import time

def read_data(filename):
    data = {}
    with open(filename, "r") as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = re.split('[,():]', line)
            neighbors = line[4:]
            for i in range(len(neighbors)):
                neighbors[i] = int(neighbors[i])
            data[int(line[0])] = {"x": float(line[1]), "y": float(line[2]), "neighbors": neighbors}
            
    return data

def create_graph(data):
    G = nx.Graph()
    for node in data:
        x1 = float(data[node]['x'])
        y1 = float(data[node]['y'])
        
        if not G.has_node(node):
            G.add_node(node, id=node, x=x1, y=y1)
            
        for neighbor in data[node]['neighbors']:
            x2 = float(data[neighbor]['x'])
            y2 = float(data[neighbor]['y'])
            
            if not G.has_node(neighbor):
                G.add_node(neighbor, id = neighbor, x=x2, y=y2)
                
            G.add_edge(node, neighbor, distance=calculate_distance(x1, y1, x2, y2), pheromones=10)
    return G

def calculate_distance(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2+(y1-y2)**2)

m = 3000
iterations = 10
alpha = 1
beta = 2
gamma = 2
Q = 50
rho = 0.8 #persistence coefficient



def algorithm(id_start,id_end):
    data = read_data("data_path_nodes.txt")
    graph = create_graph(data)
    node= graph.nodes[id_start]
    node_end = graph.nodes[id_end] 
    opt_paths = [] 
    for iter in range(iterations):
        paths= []
        print(iter)

        for ant in range(m):
            previous_node_id = id_start
            stopped = 0
            repetition={}
            path = {'nodes':[],'distance':0}
            path['nodes'].append(node)
            while node != graph.nodes[id_end]:
                neighbors =  list(graph.neighbors(node['id']))
                # ceo cvor sa id x i y
                next_node_id, distance = get_next_node(node,neighbors,graph,node_end)
                if previous_node_id == next_node_id:
                    rep = 0
                    if previous_node_id in repetition:
                        if node['id'] in repetition[previous_node_id]:
                            repetition[previous_node_id][node['id']] += 1
                            rep = repetition[previous_node_id][node['id']]
                    elif node['id'] in repetition:
                        if previous_node_id in repetition[node['id']]:
                            repetition[node['id']][previous_node_id] += 1
                            rep = repetition[node['id']][previous_node_id]
                    else:
                        repetition[previous_node_id] = {}
                        repetition[previous_node_id][node['id']] = 1
                        rep = 1
                    if rep >= 2000:
                        stopped = 1
                        break                        
                previous_node_id = node['id']
                node = graph.nodes[next_node_id]
                path['nodes'].append(node)
                path['distance'] += distance
            if not stopped:
                print('pronbasao', ant)
                paths.append(path)
                node= graph.nodes[id_start]
                print('pronasao u:',i)
                break

        if paths != []:
            opt_paths.append(update_pheromones(graph,paths)[0])
        if check_for_stop(opt_paths):
            break
    if not opt_paths:
        print("Dozvoljena duzina putanje je premala, povecajte je")
    return opt_paths[len(opt_paths)-1]
     
def check_for_stop(opt_paths):
    number_of_opt_paths = len(opt_paths)
    if number_of_opt_paths >= 10:
        for i in range(1,11):
            if opt_paths[number_of_opt_paths-i] != opt_paths[number_of_opt_paths-i-1]:
                return False
        return True
    return False
     
def update_pheromones(graph,paths):
    paths = sorted(paths, key=lambda x: x['distance'])[:10]
    delta = {}
    for path in paths:
        nodes = path['nodes']
        for i in range(len(nodes)-1):
            if (nodes[i]['id'] not in delta):
                delta[nodes[i]['id']] = {}
            if (nodes[i+1]['id'] not in  delta[nodes[i]['id']]):
                delta[nodes[i]['id']][nodes[i+1]['id']] = {'pher':0, 'status':0}
            edge = graph.edges[nodes[i]['id'], nodes[i+1]['id']]
            delta[nodes[i]['id']][nodes[i+1]['id']]['pher'] += Q / edge['distance']
            
    for path in paths:
        nodes = path['nodes']
        for i in range(len(nodes)-1):
            if  delta[nodes[i]['id']][nodes[i+1]['id']]['status'] == 1:
                continue
            pheromones = graph.edges[nodes[i]['id'], nodes[i+1]['id']]['pheromones']
            pheromones = rho * pheromones + delta[nodes[i]['id']][nodes[i+1]['id']]['pher']
            delta[nodes[i]['id']][nodes[i+1]['id']]['status'] = 1

    return paths

def get_probabilities(node,neighbors,graph,node_end):
    probabilities = {}
    sum = 0
    for neighbor in neighbors:
        neighbor = graph.nodes[neighbor]
        neighbor_id = neighbor['id']
        edge = graph.edges[node['id'],neighbor_id]
        pheromones = edge['pheromones']
        distance = edge['distance']

        probabilities[neighbor_id] = get_probability_numerator(pheromones,distance,node,neighbor,node_end)
        sum += probabilities[neighbor_id]
    for neighbor_id in probabilities:
        probabilities[neighbor_id] /= sum
    return probabilities
    
def get_probability_numerator(pheromones,distance,node,neighbor,node_end):
    return (pheromones**alpha) * ((1/distance)**beta) * ((1/(1+get_teta(node['x'],node['y'],neighbor['x'],neighbor['y'],node_end)))**gamma)

def get_teta(x1,y1,x2,y2,node_end):
    if x1 == x2:
        return 0
    k1 = (y2 - y1)/(x2 - x1)
    k2 = (node_end['y'] - y1)/(node_end['x'] - x1)
    return math.atan((k1 - k2)/(1 + k1*k2))
    
def get_next_node(node,neighbors,graph,node_end):
    # 0.1 0.2 0.3
    # sum = 0.6
    
    # 0.17 0.33 0.5
    # 0 - 0.17
    # 0.18 - 0.5
    # 0.51 - 1
    # random [0,1] = 0.24
    random_number = random.random()
    probabilities = get_probabilities(node,neighbors,graph,node_end)
    probabilities = {k: v for k, v in sorted(probabilities.items(), key=lambda item: item[1])}
    for neighbor_id in probabilities:
        if probabilities[neighbor_id] >= random_number:
            break
    return neighbor_id, graph.edges[node['id'], neighbor_id]['distance']


def main():
    pocetno = time.time()
    path = algorithm(3653296222, 3653134376)
    krajnje = time.time()

    print("OPTIMALNA PUTANJA : ",len(path['nodes']))
    print('DISTANCA: ', path['distance'])
    print('VREME: ', krajnje - pocetno)

if __name__ == '__main__':
    main()