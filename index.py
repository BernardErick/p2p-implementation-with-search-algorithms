import json
import random
import networkx as nx
import matplotlib.pyplot as plt
import os
import imageio

def create_gif_from_pngs(directory="."):
    # Obtém a lista de arquivos PNG na raiz do projeto com o prefixo "graph"
    file_list = [f for f in os.listdir(directory) if f.endswith(".png") and f.startswith("graph")]
    file_list.sort()  # Ordena a lista para garantir a ordem correta

    # Caminho para o arquivo de saída GIF
    output_gif_path = os.path.join(directory, "resume.gif")

    # Lista para armazenar os frames do GIF
    images = []

    # Lê cada arquivo PNG e adiciona ao GIF
    for file_name in file_list:
        print("adicionando ao gif")
        file_path = os.path.join(directory, file_name)
        images.append(imageio.imread(file_path))

    # Salva o GIF com um intervalo de 1 segundo entre os frames
    imageio.mimsave(output_gif_path, images, duration=500, loop=0)

class P2PNetwork:
    def _init_(self, num_nodes, min_neighbors, max_neighbors):
        self.num_nodes = num_nodes
        self.min_neighbors = min_neighbors
        self.max_neighbors = max_neighbors
        self.graph = nx.Graph()

    def print_graph(self):
        print("Graph:")
        for node_id in self.graph.nodes:
            resources = ', '.join(self.graph.nodes[node_id]['resources'])
            print(f"Node {node_id}: Resources [{resources}]")

        print("\nEdges:")
        for edge in self.graph.edges:
            print(f"{edge[0]} -- {edge[1]}")

        print("\n")

    def print_graph_with_interface(self):
        seed = 42
        pos = nx.spring_layout(self.graph, seed=seed)  # Layout para a visualização do grafo
        node_labels = {node: f"{node}\n{', '.join(self.graph.nodes[node]['resources'])}" for node in self.graph.nodes}

        nx.draw(self.graph, pos, with_labels=True, labels=node_labels, font_weight='bold', node_color='skyblue')
        plt.savefig("graph.png")
        
    def print_graph_with_interface_advanced(self, visited_nodes=None, current_node=None):
        plt.figure()
        seed = 42
        pos = nx.spring_layout(self.graph, seed=seed)  # Layout para a visualização do grafo
        node_labels = {node: f"{node}\n{', '.join(self.graph.nodes[node]['resources'])}" for node in self.graph.nodes}
        
        node_colors = ['green' if node == current_node else 'red' if node in visited_nodes else 'skyblue' for node in self.graph.nodes]

        nx.draw(self.graph, pos, with_labels=True, labels=node_labels, font_weight='bold', node_color=node_colors)
        value = len(visited_nodes)
        
        plt.savefig("graph" + str(value) + ".png")

    def validate_network(self):
        # Verificação 1: A rede não pode estar particionada
        if not nx.is_connected(self.graph):
            raise ValueError("A rede está particionada.")

        # Verificação 2: Número mínimo e máximo de vizinhos
        for node_id in self.graph.nodes:
            neighbors_count = len(list(self.graph.neighbors(node_id)))
            if neighbors_count < self.min_neighbors or neighbors_count > self.max_neighbors:
                raise ValueError(f"O nó {node_id} não tem o número correto de vizinhos.")

        # Verificação 3: Nós sem recursos
        for node_id in self.graph.nodes:
            if not self.graph.nodes[node_id]['resources']:
                raise ValueError(f"O nó {node_id} não tem recursos.")

        # Verificação 4: Arestas de um nó para ele mesmo
        for edge in self.graph.edges:
            if edge[0] == edge[1]:
                raise ValueError("Existem arestas de um nó para ele mesmo.")

    def search_resources(self, node_id, resource_id, ttl, algo):
        if algo == 'flooding':
            messages, involved_nodes, history = self.flooding_search(node_id, resource_id, ttl)
        elif algo == 'informed_flooding':
            messages, involved_nodes, history = self.informed_flooding_search(node_id, resource_id, ttl)
        elif algo == 'random_walk':
            messages, involved_nodes, history = self.random_walk_search(node_id, resource_id, ttl)
        elif algo == 'informed_random_walk':
            messages, involved_nodes, history = self.informed_random_walk_search(node_id, resource_id, ttl)
        else:
            raise ValueError("Algoritmo de busca inválido.")

        print(f"Número total de mensagens: {messages}")
        print(f"Número total de nós envolvidos: {involved_nodes}")
        print("\nHistórico:")
        for step in history:
            print(step)

    #Busca por Inundação
    def flooding_search(self, node_id, resource_id, ttl):
        visited = set()
        queue = [(node_id, ttl)]
        messages = 0
        involved_nodes = set()
        history = []

        while queue:
            current_node, current_ttl = queue.pop(0)
            
            involved_nodes.add(current_node)

            history.append(f"{current_node} verificou nele mesmo ({current_node}) sobre o recurso {resource_id}")

            if current_node not in visited:
                visited.add(current_node)
                self.print_graph_with_interface_advanced(visited, current_node)
                if resource_id in self.graph.nodes[current_node]['resources']:
                    history.append(f"Encontrado em {current_node}!")
                    return messages, len(involved_nodes), history
                else:
                    history.append(f"Não encontrado!")

                if current_ttl > 0:
                    neighbors = list(self.graph.neighbors(current_node))
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            print("Comunicação de vizinhos do ",current_node, " -> ", neighbor)
                            #TODO não incluir vizinhos já visitados
                            queue.append((neighbor, current_ttl - 1))
                            messages += 1
                            history.append(f"{current_node} perguntou para {neighbor} sobre o recurso {resource_id}")
        
        return messages, len(involved_nodes), history

    def informed_flooding_search(self, node_id, resource_id, ttl):
        # Implementar busca informada por inundação
        print("informed_flooding_search")
        return "Nada","ainda"
        pass

    def random_walk_search(self, node_id, resource_id, ttl):
        # Implementar busca por passeio aleatório
        print("random_walk_search")
        return "Nada","ainda"
        pass

    def informed_random_walk_search(self, node_id, resource_id, ttl):
        # Implementar busca informada por passeio aleatório
        print("informed_random_walk_search")
        return "Nada","ainda"
        pass


def parse_config(config_data):
    config = json.loads(config_data)

    num_nodes = config["num_nodes"]
    min_neighbors = config["min_neighbors"]
    max_neighbors = config["max_neighbors"]

    network = P2PNetwork(num_nodes, min_neighbors, max_neighbors)

    for node_resources in config["resources"]:
        node_id, resources = node_resources.split(":")
        resources = [r.strip() for r in resources.split(",")]
        network.graph.add_node(node_id, resources=resources)

    for edge in config["edges"]:
        node1, node2 = edge.split(",")
        network.graph.add_edge(node1.strip(), node2.strip())

    return network


if __name__ == "__main__":
    config_data = '''
    {
        "num_nodes": 10,
        "min_neighbors": 1,
        "max_neighbors": 4,
        "resources" :[
            "n1: r1",
            "n2: r3, r4",
            "n3: r5, r6",
            "n4: r7, r8",
            "n5: r9, r10",
            "n6: r11, r12",
            "n7: r13, r14",
            "n8: r15, r16",
            "n9: r17, r18",
            "n10: r21, r20"
        ],
        "edges" :[
            "n1, n2",
            "n2, n3",
            "n3, n4",
            "n4, n5",
            "n5, n6",
            "n3, n7",
            "n3, n8",
            "n4, n9",
            "n4, n10"
        ]
    }
    '''
    network = parse_config(config_data)

    try:
        network.validate_network()
    except ValueError as e:
        print(f"Erro na validação da rede: {e}")
        exit(1)

    network.print_graph()
    network.print_graph_with_interface()

    # Exemplo de uso da busca por inundação
    node_id = 'n1'
    resource_id = 'r11'
    ttl = 4
    algo = 'flooding'

    messages, involved_nodes, history = network.flooding_search(node_id, resource_id, ttl)
    
    print(f"\nResultado da busca por inundação:")
    print(f"Número total de mensagens: {messages}")
    print(f"Número total de nós envolvidos: {involved_nodes}")
    print("\nHistórico:")

    for step in history:
        print(step)

    create_gif_from_pngs()
