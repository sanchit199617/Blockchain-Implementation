from flask import Flask, jsonify, request
from uuid import uuid4
from argparse import ArgumentParser
from blockchain import Blockchain

# make a 'server node' so that we could interact with the blockchain
# instantiate the Node
node = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()

# declare the address of this node
node_address = ''

# give the address of manager node
manager_address = ''

# define functions and corresponding urls that trigger it
@node.route('/mine', methods=['GET'])
def mine():

	# to mine, this node has to run proof of work first
	last_block = blockchain.last_block
	proof = blockchain.proof_of_work(last_block)

	# This node is rewarded with 1 coin
	# sender "0" signifies that this node has mined a coin
	blockchain.coin_transaction(
		sender="0",
		recipient=node_identifier,
		amount = 1,
	)

	# forge the new block
	previous_hash = blockchain.hash(last_block)
	block = blockchain.forge_block(proof, previous_hash)

	response = {
		'message': "New Block Forged",
		'block index': block['index'],
		'transaction': block['transaction'],
		'proof': block['proof'],
		'previous_hash': block['previous_hash'],
	}
	return jsonify(response), 200


@node.route('/transaction/new', methods=['POST'])
def new_transaction():
	values = request.get_json()

	# Check that the required fields are in the POST'ed data
	required = ['sender', 'recipient', 'item', 'cost']
	if not all(k in values for k in required):
		return 'Missing values', 400

	# Create a new transaction
	index = blockchain.item_transaction(values['sender'], values['recipient'], values['item'], values['cost'])

	# show proof of work and then forge a block
	last_block = blockchain.last_block
	proof = blockchain.proof_of_work(last_block)

	previous_hash = blockchain.hash(last_block)
	block = blockchain.forge_block(proof, previous_hash)

	response = {
		'message': f'Transaction added to Block {index}',
		'transaction': block['transaction'],
	}
	return jsonify(response), 201

# get the chain
@node.route('/chain', methods=['GET'])
def get_chain():
	response = {
		'chain': blockchain.chain,
		'length': len(blockchain.chain),
	}
	return jsonify(response), 200

# register a new node with the blockchain with the help of manager node
@node.route('/node/register', methods=['GET'])
def register_node():

	# register the node with the manager
	nodes = blockchain.register_node(manager_address, node_address)

	response = {
		'message': 'New node has been added',
		'total_nodes': list(nodes),
	}
	return jsonify(response), 200

# resolve this nodes chain
@node.route('/node/resolve', methods=['GET'])
def consensus():

	replaced = blockchain.resolve_conflicts()

	if replaced:
		response = {
			'message': 'Our chain was replaced',
			'new_chain': blockchain.chain
		}
	else:
		response = {
			'message': 'Our chain is authoritative',
			'chain': blockchain.chain
		}

	return jsonify(response), 200

# this url recieves a POST from manager that informs it about the other nodes present in the network
@node.route('/nodes/data', methods=['POST'])
def get_nodes():
	blockchain.nodes = set(request.get_json()['nodes'])
	response = {'message': 'Set of nodes updated succesfully'}
	return jsonify(response), 201

def main():
	parser = ArgumentParser()
	parser.add_argument('-p', '--port', default=5001, type=int, help='the port to listen on')
	parser.add_argument('-ha', '--host', default='127.0.0.1', help='the host address')
	args = parser.parse_args()

	global node_address, manager_address
	node_address = args.host + ':' +  str(args.port)
	manager_address = '127.0.0.1:5000'

	node.run(host=args.host, port=args.port)

if __name__ == '__main__':
	main()