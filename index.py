import json
import random
import networkx as nx
import matplotlib.pyplot as plt
import os
import imageio
import re
import time

def create_gif_from_pngs(directory="."):
    # Obtém a lista de arquivos PNG na raiz do projeto com o prefixo "graph"
    file_list = [f for f in os.listdir(directory) if f.endswith(".png") and f.startswith("graph")]
    file_list.sort(key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else float('inf'))

    # Caminho para o arquivo de saída GIF
    output_gif_path = os.path.join(directory, "resume.gif")

    # Lista para armazenar os frames do GIF
    images = []

    # Lê cada arquivo PNG e adiciona ao GIF
    for file_name in file_list:
        print("Adicionando ao gif:", file_name)
        file_path = os.path.join(directory, file_name)
        images.append(imageio.imread(file_path))

    # Salva o GIF com um intervalo de pelo menos 1 segundo entre os frames
    imageio.mimsave(output_gif_path, images, duration=2000, loop=0)

    png_files = [f for f in os.listdir(directory) if f.endswith(".png") and f.startswith("graph")]
    # Exclui cada arquivo PNG
    for png_file in png_files:
        file_path = os.path.join(directory, png_file)
        os.remove(file_path)
    

class P2PNetwork:
    def __init__(self, num_nodes, min_neighbors, max_neighbors, cache_path):
        self.num_nodes = num_nodes
        self.min_neighbors = min_neighbors
        self.max_neighbors = max_neighbors
        self.graph = nx.Graph()
        self.cache_path = cache_path

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
        pos = nx.spring_layout(self.graph, seed=seed, k=1.5)  # Layout para a visualização do grafo
        node_labels = {node: f"{node}\n{', '.join(self.graph.nodes[node]['resources'])}" for node in self.graph.nodes}

        plt.figure(figsize=(13, 10))
        nx.draw(self.graph, pos, with_labels=True, labels=node_labels, font_weight='bold', node_color='skyblue')
        plt.savefig("graph.png")
        
    def print_graph_with_interface_advanced(self, visited_nodes=None, current_node=None):
        plt.figure()
        seed = 42
        pos = nx.spring_layout(self.graph, seed=seed, k=1.5)  # Layout para a visualização do grafo
        node_labels = {node: f"{node}\n{', '.join(self.graph.nodes[node]['resources'])}" for node in self.graph.nodes}
        
        node_colors = ['green' if node == current_node else 'red' if node in visited_nodes else 'skyblue' for node in self.graph.nodes]
        plt.figure(figsize=(13, 10))
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

    #Busca por Inundação
    def flooding_search(self, node_id, resource_id, ttl):
        visited = set()
        queue = [(node_id, ttl)]
        messages = 0
        involved_nodes = set()
        history = []

        start_time = time.time()
        while queue:
            current_node, current_ttl = queue.pop(0)
            
            involved_nodes.add(current_node)

            history.append(f"{current_node} verificou nele mesmo ({current_node}) sobre o recurso {resource_id}")

            if current_node not in visited:
                visited.add(current_node)
                self.print_graph_with_interface_advanced(visited, current_node)
                if resource_id in self.graph.nodes[current_node]['resources']:
                    history.append(f"Encontrado em {current_node}!")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f"Tempo decorrido do algitmo de busca por inundação SEM CACHE: {elapsed_time} segundos")
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
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Tempo decorrido do algitmo de busca por inundação SEM CACHE: {elapsed_time} segundos")
        return messages, len(involved_nodes), history

    def informed_flooding_search(self, node_id, resource_id, ttl):
        start_time = time.time()

        visited = set()
        queue = [(node_id, ttl)]
        messages = 0
        involved_nodes = set()
        history = []

        cached_result = self.get_cache_value(resource_id)
        if cached_result is not None:
            print(f"Recurso encontrado no cache! Valor: {cached_result}")

            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Tempo decorrido do algitmo de busca por inundação COM CACHE: {elapsed_time} segundos")
            return messages, len(involved_nodes), history

        while queue:
            current_node, current_ttl = queue.pop(0)
            
            involved_nodes.add(current_node)

            history.append(f"{current_node} verificou nele mesmo ({current_node}) sobre o recurso {resource_id}")

            if current_node not in visited:
                visited.add(current_node)
                self.print_graph_with_interface_advanced(visited, current_node)
                if resource_id in self.graph.nodes[current_node]['resources']:
                    
                    # Use o caminho absoluto para o arquivo de cache
                    self.save_cache(str(resource_id), str(current_node))
                    
                    history.append(f"Encontrado em {current_node}!")
                    end_time = time.time()
                    elapsed_time = end_time - start_time
                    print(f"Tempo decorrido do algitmo de busca por inundação COM CACHE: {elapsed_time} segundos")
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
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Tempo decorrido do algitmo de busca por inundação COM CACHE: {elapsed_time} segundos")
        return messages, len(involved_nodes), history

    def save_cache(self, key, value):
        print("Chave:",key)
        print("Chave:",value)
        cache_file = self.cache_path

        # Adicione mensagens de debug
        print(f"Debug: Caminho absoluto para o arquivo de cache: {cache_file}")
        # Verifica se o arquivo de cache já existe
        if os.path.exists(cache_file):
            # Carrega o conteúdo atual do arquivo JSON
            with open(cache_file, 'r') as file:
                cache_data = json.load(file)
        else:
            # Se o arquivo não existir, cria um dicionário vazio
            cache_data = {}

        # Adiciona a chave e valor ao dicionário
        cache_data[key] = value

        # Salva o dicionário atualizado de volta no arquivo JSON
        with open(cache_file, 'w') as file:
            json.dump(cache_data, file, indent=2)
    def get_cache_value(self,key):
        cache_file = "cache.json"

        # Verifica se o arquivo de cache existe
        if os.path.exists(cache_file):
            # Carrega o conteúdo atual do arquivo JSON
            with open(cache_file, 'r') as file:
                cache_data = json.load(file)

            # Verifica se a chave existe no dicionário
            if key in cache_data:
                # Retorna o valor correspondente à chave
                return cache_data[key]

    # Retorna None se a chave não existir ou o arquivo não existir
    
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


def parse_config_from_file(file_path):
    with open(file_path, 'r') as file:
        config_data = file.read()
    return parse_config(config_data)
    
def parse_config(config_data):
    config = json.loads(config_data)

    num_nodes = config["num_nodes"]
    min_neighbors = config["min_neighbors"]
    max_neighbors = config["max_neighbors"]

    print(num_nodes)
    print(min_neighbors)
    print(max_neighbors)

    network = P2PNetwork(num_nodes, min_neighbors, max_neighbors, '.')
    
    for node_resources in config["resources"]:
        node_id, resources = node_resources.split(":")
        resources = [r.strip() for r in resources.split(",")]
        network.graph.add_node(node_id, resources=resources)

    for edge in config["edges"]:
        node1, node2 = edge.split(",")
        network.graph.add_edge(node1.strip(), node2.strip())

    return network


if __name__ == "__main__":
 # Caminho para o arquivo bootstrap.json na raiz do projeto
    bootstrap_file_path = os.path.join(os.getcwd(), "bootstrap.json")

    # Caminho absoluto para o arquivo de cache
    cache_file_path = os.path.join(os.getcwd(), "cache.json")

    # Verifica se o arquivo bootstrap.json existe
    if not os.path.exists(bootstrap_file_path):
        print("Arquivo bootstrap.json não encontrado na raiz do projeto.")
        exit(1)

    # Lê o conteúdo do arquivo bootstrap.json e instância a classe P2PNetwork com o caminho absoluto para o arquivo de cache
    network = parse_config_from_file(bootstrap_file_path)
    network.cache_path = cache_file_path
    
    try:
        network.validate_network()
    except ValueError as e:
        print(f"Erro na validação da rede: {e}")
        exit(1)

    network.print_graph()
    network.print_graph_with_interface()

    # Definindo qual o tipo de teste eu vou querer
    node_id = 'n1'
    resource_id = 'r11'
    ttl = 30
    algo = 'informed_flooding'

    messages, involved_nodes, history = network.informed_flooding_search(node_id, resource_id, ttl)
    
    print(f"\nResultado da busca por inundação:")
    print(f"Número total de mensagens: {messages}")
    print(f"Número total de nós envolvidos: {involved_nodes}")
    print("\nHistórico:")

    for step in history:
        print(step)

    create_gif_from_pngs()