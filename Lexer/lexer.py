#!/usr/bin/env python

import ply.lex as lex
import re
import os
import sys

token_list = []


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
			 'ICONST',
			 'FCONST',
			 'CCONST',
			 'SCONST',
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
			 'ID',
			 'COMMA',
			 'EQ',
			 'NE',
			 'GE',
			 'LE',
			 'PLUSEQUAL',
			 'MINUSEQUAL',
			 'TIMESEQUAL',
			 'DIVEQUAL',
			 'MODEQUAL',
			 'GT',
			 'LT',
			 'EQUALS',
			 'PLUS',
			 'PLUSPLUS',
			 'MINUS',
			 'MINUSMINUS',
			 'TIMES',
			 'DIVIDE',
			 'MOD',
			 'LAND',
			 'AND',
			 'LNOT',
			 'LOR',
			 'CONDOP',
			 'COLON',
			'END_INCLUDE'
		 ] + list(reserved.values())

# Regular expression rules for simple tokens


t_EQ = r'=='

t_NE = r'!='

t_GE = r'>='

t_LE = r'<='

t_PLUSEQUAL = r'\+='

t_MINUSEQUAL = r'-='

t_TIMESEQUAL = r'\*='

t_DIVEQUAL = '/='

t_MODEQUAL = r'%='

t_GT = r'>'

t_LT = r'<'

t_EQUALS = r'='

t_PLUS = r'\+'

t_PLUSPLUS = r'\+\+'

t_MINUS = r'-'

t_MINUSMINUS = r'--'

t_TIMES = r'\*'

t_DIVIDE = r'/'

t_MOD = r'%'

t_LAND = r'&&'

t_AND = r'&'

t_LOR = r'\|\|'

t_CONDOP = r'\?'

t_LNOT = r'!'

t_COLON = r':'

t_CCONST = r'\'(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))\''

t_SCONST = r'\"(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))*\"'

t_LPAREN = r'\('

t_RPAREN = r'\)'

t_LBRACKET = r'\['

t_RBRACKET = r'\]'

t_LBRACE = r'{'

t_RBRACE = r'}'

t_SEMICOLON = r';'

t_COMMA = r','

included = {}
last_newline = 0


def t_INCLUDE(t):
	r'\#[ \t]*include[ \t]+\"(.|(\\[ntr0\'"])|(\\x[0-9a-fA-F][0-9a-fA-F]))*?\"'
	include_file = re.split('[ \t]+', t.value)[-1].strip('\"')
	global last_newline
	if t.lexpos != last_newline:
		print('Error: "#include" is not at the beginning of the line!')
		pass
	elif include_file in included.keys():
		print('Warning: File "%s" already included!' % include_file)
		pass
	elif not os.path.isfile(include_file):
		print('Error: No such file or directory: "%s"!' % include_file)
		sys.exit()
	elif not os.access(include_file, os.R_OK):
		print('Error: Can\'t open file or directory: "%s"!' % include_file)
		sys.exit()
	else:
		token_list.append(t)
		included[include_file] = '1'
		include_lexer = lex.lex()
		include_fin = open(include_file, 'r')
		include_data = include_fin.read()
		include_fin.close()
		last_newline = 0
		include_lexer.input(include_data)
		while True:
			toke = include_lexer.token()
			if not toke:
				break  # No more input
			token_list.append(toke)
		t.value = include_file
		kalimera = lex.LexToken()
		kalimera.type = 'END_INCLUDE'
		kalimera.value = t.value
		kalimera.lineno = 0
		kalimera.lexpos = 0
		token_list.append(kalimera)
		pass


def t_COMMENTS(t):
	r'(/\*([^*]|[\n]|(\*+([^*/]|[\n])))*\*+/)|(//.*)'
	t.lexer.lineno += t.value.count('\n')
	pass

def t_FCONST(t):
	r'((\d*\.\d+)([eE][+-]?\d+)?)|(\d+[eE][+-]?\d+)'
	# t.value = float(t.value)
	return t

def t_ICONST(t):
	r'\d+'
	# t.value = int(t.value)
	return t

def t_ID(t):
	r'[a-zA-Z][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value, 'ID')  # Check for reserved words
	return t


# Define a rule so we can track line numbers
def t_newline(t):
	r'(\r\n)+|(\n+)'
	global last_newline
	last_newline = t.lexpos + len(t.value)
	t.lexer.lineno += len(t.value)
	pass


# A string containing ignored characters (spaces and tabs)
t_ignore = ' \t'


# Error handling rule
def t_error(t):
	print('Error: Illegal character ' + t.value[0] + '!')
	t.lexer.skip(1)
	pass


lexer = lex.lex()


def my_lexer(arguments):
	input_file_name = arguments
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
		token_list.append(tok)


def our_lexer(arguments):
	input_file_name = arguments
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
