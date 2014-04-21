import logging
import os.path
from twosync.utils import get_hash, get_str_hash, log_and_raise
from collections import namedtuple

_filter = namedtuple('_filter', 'full, preglob, postglob, values')

class config(object):
	"""
	The config object open a config file an prepare it for usage
	
	After parsing a config file. The Data can be used for the program.
	The format ist spezialised for this program. It has the following keys:
		root: Is a path for the folders who sould synchronised (has to set 2 times: "source" and "target")
		ignore file: which files has to be ignored for synchronisation
		ignore path: which directories has to be ignored for synchronisation
		ignore not file: files who sould synchronised, but match ignore file
		ignore not path: directory who sould synchronised, but match ignore path
	root has to be a absolutley path to a directory
	All ignore-keys can use * at the value as placeholder for everything
	"""

	def __init__(self, configname):
		logging.info("Create config object")
		
		self._keys 			= ['root']
		self._parse_keys 	= ['ignore not file', 'ignore file', 'ignore not path', 'ignore path']
		self._config 		= dict()
		self._configname 	= configname
		self._path_config 	= os.path.expanduser("~/.twosync/" + self._configname)
		self._path_hash 	= os.path.expanduser("~/.twosync/.hash_" + self._configname)
		self._path_data 	= os.path.expanduser("~/.twosync/.data_" + self._configname)

		for key in (self._keys + self._parse_keys):
			self._config[key] = []
		
		self._config_changed()
		self._parse()
		
	def _config_changed(self):
		"""
		Writes True or False to 'self._config_changed' depending if the config has changed

		The comparison are done over a sha1 checksum, which saved on the HD
		"""

		logging.info("Check if config-file has changed")

		self._hexdigest = get_hash(self._path_config)
		
		saved_hash = ''
		try:
			f = open(self._path_hash, 'r')
		except FileNotFoundError:
			logging.info("No hash key for config-file: '" + self._path_config + "'")
		except PermissionError as e:
			log_and_raise("No permission to read hash-file: '" + self._path_hash + "'", e)
			pass
		else:
			saved_hash = f.read()
			saved_hash[:-1]
			f.close()
		
		if self._hexdigest == saved_hash:
			logging.info("config-file has not changed")
			self._config_changed = False
		logging.info("config-file has changed")
		self._config_changed = True
	
	def _save_config_hash(self):
		try:
			f = open(self._path_hash, 'w')
			f.write(self._hexdigest)
		except PermissionError as e:
			log_and_raise("No permission to write hash-file: '" + self._path_hash + "'", e)
		else:
			f.close()
	
	def _parse_exp(self, value):
		"""
		Parses the "ignore" values
		
		Is used to parse the ignore values. After parsing it can be used with "test_string"
		"""
		logging.info("Parse expression: '" + value + "'")
		
		pre, post = 0, 0
		if value[:1] == "*":
			pre = 1
			value = value[1:]
		if value[-1:] == "*":
			post = 1
			value = value[:-1]
		return _filter(value, pre, post, value.split("*"))
	
	def _parse(self):
		"""
		Parse the config-file an test if the config-file match the specifications
		"""
		
		logging.info("Parse config-file: '" + self._path_config + "'")

		try:
			# Open config file and parse content.
			for line in open(self._path_config, 'r'):
				# remove whitespaces
				line = line.strip()
				# ignore if comment and empty line
				if line[0:1] == '#' or len(line) == 0:
					continue
				# split line into key, value
				key, value = line.split("=", 1)
				# remove whitespaces
				key = key.strip()
				value = value.strip()
				if not key in (self._keys + self._parse_keys):
					log_and_raise("Invalid key: '" + key + "' in config-file: '" + self._path_config + "'")
				if key in self._parse_keys:
					value = self._parse_exp(value)
				# save value to key
				config = self._config[key]
				config.append(value)
				
		except FileNotFoundError as e:
			log_and_raise("Config-file: '" + self._path_config + "' does not exist", e)
		
		except PermissionError as e:
			log_and_raise("No permission on config-file: '" + self._path_config + "'", e)
			
		# Check if 2 roots exist
		if len(self._config['root']) != 2:
			log_and_raise("Config-file: '" + self._path_config + "' need 2 root keys", e)

	@property
	def config_dict(self):
		"""
		Returns the dictionary with the parsed config
		"""
		return self._config
	
	@property
	def roots(self):
		"""
		Returns a list with the roots 
		"""
		return self._config['root']
	
	@property
	def config_changed(self):
		"""
		Returns True if the config has changed or is new. Otherwise it returns False
		"""
		return self._config_changed
	
	@property
	def configname(self):
		"""
		Returns the config name
		"""
		return self._configname