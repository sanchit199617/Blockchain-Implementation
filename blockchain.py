import hashlib
import json
import datetime
import requests
from urllib.parse import urlparse

class Blockchain:

	def __init__(self):

		# our blockchain assumes a block would consist of a single transaction
		self.latest_transaction = {}		# the most recent transaction
		self.chain = []						# main chain being a list of blocks
		self.nodes = set()					# set of nodes operating the blockchain

		# create the genesis block with random attributes
		self.forge_block(proof=1000, previous_hash='Genesis Block')

	def forge_block(self, proof, previous_hash=None):
		"""
		Creates a new block and add to our chain

		Parameters
		proof: proof given by the proof of work algorithm
		previous_hash = hash of previous block

		returns: <dict> newly created block
		"""
		block = {
		'index': len(self.chain)+1,
		'timestamp': str(datetime.datetime.now()),
		'transaction': self.latest_transaction,
		'proof': proof,
		'previous_hash': previous_hash or self.hash(self.last_block),
		}

		# clear the latest_transaction attribute
		self.latest_transaction = {}

		# add to chain
		self.chain.append(block)
		return block

	def coin_transaction(self, sender, recipient, amount):
		"""
		Create a new coin transaction and make this the latest transaction
		"""
		self.latest_transaction = {
			'sender':sender,
			'recipient': recipient,
			'amount': amount,
			}

		# return the block index that this transaction would belong to
		return self.last_block['index'] + 1

	def item_transaction(self, sender, recipient, item, cost):
		"""
		Create a new user transaction and make this the latest transaction
		"""
		self.latest_transaction = {
			'sender':sender,
			'recipient': recipient,
			'item': item,
			'cost': cost,
			}

		# return the block index that this transaction would belong to
		return self.last_block['index'] + 1

	# define a getter for the last block of our chain
	@property
	def last_block(self):
		return self.chain[-1]

	# a utility function to calculate the hash of a block
	@staticmethod	# define this to be static so that the function is bound to class and not to an object
	def hash(block):
		"""
		Create a SHA-256 hash of a block
		"""

		# encode the string before hashing as the hash function only takes a sequence of bytes as input
		block_string = json.dumps(block, sort_keys = True).encode()
		return hashlib.sha256(block_string).hexdigest()		# hexdigest is used to convert the hash to a HEX string

	def proof_of_work(self, last_block):
		"""
		Find a number p' such that hash(pp'l_h) contains predefined number of leading zeros and 1 trailing zero
		where p' is the new proof, p is the last proof, l_h is the last hash

		Parameters
		last_block: <int> Last block in Chain

		returns: Current valid proof <int>
		"""

		last_proof = last_block['proof']
		last_hash = self.hash(last_block)
		proof = 0
		while self.validate(last_proof, proof, last_hash, no_zeros=4) is False:
			proof += 1

		return proof

	@staticmethod
	def validate(last_proof, proof, last_hash, no_zeros):
		"""
		Validates the Proof of Work

		Parameters
		last_proof: <int> Previous Proof
		proof: <int> Current Proof
		last_hash: <str> The hash of the Previous Block
		no_zeros: <int> Number of leading zeros in hashed string

		returns: <bool> True if correct, False if not.
		"""

		guess = f'{last_proof}{proof}{last_hash}'.encode()
		guess_hash = hashlib.sha256(guess).hexdigest()
		return (guess_hash[:no_zeros] == '0'*no_zeros) and (guess_hash[-1] == '0')

	def register_node(self, manager_address, address):
		"""
		Sends a POST informing the manager node to add itself to the list of nodes

		Parameters
		manager_address: address of the node storing info of all other nodes
		address: Address of node. Eg. 'http://192.168.0.5:5000'
		"""
		parsed_url = urlparse(address)
		if parsed_url.path:
			# Accepts an URL without scheme like '192.168.0.5:5000'.
			response = requests.post(f'http://{manager_address}/nodes/data', json={'address':parsed_url.path})
		else:
			raise ValueError('Invalid URL')

		# update the nodes set to include addresses of other nodes
		# response from the manager contains the list of all nodes
		updated_nodes = set(response.json()['nodes'])
		self.nodes = updated_nodes
		return updated_nodes

	def valid_chain(self, chain):
		"""
		Determine if a given blockchain is valid

		Parameters:
		chain: A blockchain

		returns: True if valid, False if not
		"""

		last_block = chain[0]
		current_index = 1

		while current_index < len(chain):
			block = chain[current_index]
			# Check that the hash of the block is correct
			last_hash = self.hash(last_block)
			if block['previous_hash'] != last_hash:
				return False
			# Check that the Proof of Work is correct
			if not self.validate(last_block['proof'], block['proof'], last_hash, no_zeros=4):
				return False
			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		"""
		This is our consensus algorithm, it resolves conflicts
		by replacing our chain with the longest one in the network.

		returns: True if our chain was replaced, False if not
		"""

		neighbours = self.nodes
		new_chain = None

		# We're only looking for chains longer than ours
		max_length = len(self.chain)

		# Grab and verify the chains from all the nodes in our network
		for node in neighbours:
			response = requests.get(f'http://{node}/chain')

			if response.status_code == 200:
				length = response.json()['length']
				chain = response.json()['chain']

				# Check if the length is longer and the chain is valid
				if length > max_length and self.valid_chain(chain):
					max_length = length
					new_chain = chain

		# Replace our chain if we discovered a new, valid chain longer than ours
		if new_chain:
			self.chain = new_chain
			return True

		return False