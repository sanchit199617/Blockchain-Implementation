import requests
from flask import Flask, jsonify, request
from argparse import ArgumentParser
import random

# to broadcast the address of all nodes to all other nodes we maintain a global set of notes maintained by a 'manager' node

nodes = set()		# set of all nodes in the blockchain

# Instantiate a new node that would store data of all other nodes in the blockchain
# this node does not perform mining or any other blockchain specific task
# each node would register themselves with this node
manager = Flask(__name__)

# a request to below url would return the set of all nodes present in the blockchain
@manager.route('/nodes/data', methods=['POST'])
def get_nodes():
	# add the requesting node to the list of nodes
	requesting_address = request.get_json()['address']
	nodes.add(requesting_address)

	# send a post to all other nodes informing about the updated set of nodes
	for node in nodes:
		if node!=requesting_address:
			r = requests.post(f'http://{node}/nodes/data', json={'nodes':list(nodes)})
	
	response = {'nodes': list(nodes)}
	return jsonify(response), 201

@manager.route('/home', methods=['POST'])
def home():
	values = request.get_json()

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'item', 'cost']
	if not all(k in values for k in required):
		return 'Missing values', 400

	# transaction = {
	# 'sender': 'sanchit',
	# 'recipient': 'kshitij',
	# 'item': 'food',
	# 'cost': 10,
	# }

	transaction = values

	verifying_node = random.choice(list(nodes))
	transaction_response = requests.post(f'http://{verifying_node}/transaction/new', json=transaction)
	print(verifying_node)
	# print(verifying_node)
	# # call consensus on other nodes to make sure the same chain is stored everywhere
	# for node in nodes:
	# 	if node!=verifying_node:
	# 		print(node)
	# 		r = requests.get(f'http://{node}/node/resolve')
	
	return jsonify(transaction_response.json()), 200

def main():
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5000, type=int, help='the port to listen on')
	args = parser.parse_args()

	# by default the manager node would run on http://127.0.0.1:5000
	manager.run(host='127.0.0.1', port=args.port)

if __name__ == '__main__':
	main()