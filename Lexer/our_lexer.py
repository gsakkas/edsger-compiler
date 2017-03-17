import ply.lex as lex
import re
import os
import sys

# List of reserved words
reserved = {
	'bool': 'BOOLEAN',
	'break': 'BREAK',
	'byref': 'BYREF',
	'char': 'CHARACTER',
	'continue': 'CONTINUE',
	'delete': 'DELETE',
	'double': 'DOUBLE',
	'else': 'ELSE',
	'for': 'FOR',
	'false': 'FALSE',
	'if': 'IF',
	'int': 'INT',
	'new': 'NEW',
	'NULL': 'NULL',
	'return': 'RETURN',
	'true': 'TRUE',
	'void': 'VOID'
}

# List of tokens
tokens = [
	'INTEGERS',
	'REALS',
	'CHARS',
	'STRINGS',
	'OPERATORS',
	'LPAREN',
	'RPAREN',
	'LBRACKET',
	'RBRACKET',
	'LBRACE',
	'RBRACE',
	'SEMICOLON',
	'WHITESPACES',
	'COMMENTS',
	'INCLUDE',
	'IDS'
] + list(reserved.values())

# Regular expression rules for simple tokens

t_OPERATORS = r'==|!=|>=|<=|\+=|-=|\*=|/=|%=|>|<|=|\+\+|\+|--|-|\*|/|%|&&|&|\|\||:|!|,'

t_CHARS = r'\'(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))\''

t_STRINGS = r'\"(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))*\"'

t_LPAREN = r'\('

t_RPAREN = r'\)'

t_LBRACKET = r'\['

t_RBRACKET = r'\]'

t_LBRACE = r'{'

t_RBRACE = r'}'

t_SEMICOLON = r';'

included = {}
last_newline = 0


def t_INCLUDE(t):
	r'\#[ \t]*include[ \t]+\"(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))*\"'
	include_file = re.split('[ \t]+', t.value)[-1].strip('\"')
	if include_file in included.keys():
		print('Warning: File "%s" already included!' % include_file)
		pass
	else:
		if not os.path.isfile(include_file):
			print('Error: No such file or directory: "%s"!' % include_file)
			sys.exit()
		elif not os.access(include_file, os.R_OK):
			print('Error: Can\'t open file or directory: "%s"!' % include_file)
			sys.exit()
		elif t.lexpos == last_newline:
			included[include_file] = '1'
			include_lexer = lex.lex()
			include_fin = open(include_file, 'r')
			include_data = include_fin.read()
			include_fin.close()
			include_lexer.input(include_data)
			while True:
				toke = include_lexer.token()
				if not toke:
					break  # No more input
				print(toke)
			pass
		else:
			print('Error: "#include" is not at the beginning of the line!')
			sys.exit()


def t_COMMENTS(t):
	r'(/\*([^*]|[\n]|(\*+([^*/]|[\n])))*\*+/)|(//.*)'
	t.lexer.lineno += t.value.count('\n')
	pass


def t_INTEGERS(t):
	r'[+-]?\d+'
	t.value = int(t.value)
	return t


def t_REALS(t):
	r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'
	t.value = float(t.value)
	return t


def t_IDS(t):
	r'[a-zA-Z][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value, 'IDS')  # Check for reserved words
	return t


# Define a rule so we can track line numbers
def t_newline(t):
	r'\n+'
	global last_newline
	last_newline = t.lexpos + len(t.value)
	t.lexer.lineno += len(t.value)
	pass


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'


# Error handling rule
def t_error(t):
	print('Error: Illegal character "%s"!' % t.value[0])
	t.lexer.skip(1)
	sys.exit()


arguments = sys.argv
if len(arguments) < 2:
	print('Error: No input file!')
	print('\tUsage: python3 our_lexer.py <input_file>')
	sys.exit()
elif len(arguments) > 2:
	print('Error: Too many arguments!\n')
	print('\tUsage: python3 our_lexer.py <input_file>')
	sys.exit()
else:
	input_file_name = arguments[-1]
	if not os.path.isfile(input_file_name):
		print('Error: No such file or directory: "%s"!' % input_file_name)
		sys.exit()
	elif not os.access(input_file_name, os.R_OK):
		print('Error: Can\'t open file or directory: "%s"!' % input_file_name)
		sys.exit()
	else:
		fin = open(input_file_name, 'r')
		data = fin.read()
		fin.close()

lexer = lex.lex()
included[input_file_name] = '1'
lexer.input(data)

# Tokenize
while True:
	tok = lexer.token()
	if not tok:
		break  # No more input
	print(tok)
