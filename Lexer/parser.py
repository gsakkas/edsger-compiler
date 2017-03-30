#!/usr/bin/env python

import sys
import os.path
import ply.yacc as yacc
import lexer
from lexer import tokens  # Import lexer information

precedence = (
	('left', 'COMMA'),
	('right', 'EQUALS', 'PLUSEQUAL', 'MINUSEQUAL', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL'),
	('nonassoc', 'CONDOP', 'COLON'),
	('left', 'LOR'),
	('left', 'LAND'),
	('nonassoc', 'LT', 'GT', 'GE', 'LE', 'EQ', 'NE'),
	('left', 'PLUS', 'MINUS'),
	('left', 'TIMES', 'DIVIDE', 'MOD'),
	('nonassoc', 'TYPECAST'),
	('right', 'PLUSPLUS', 'MINUSMINUS'),
	('right', 'NEW', 'DELETE'),
	('right', 'AND', 'LNOT'),
	('nonassoc', 'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN'),
)


def p_program(p):
	'''program : declaration program
			   | includes program
			   | declaration includes
			   | declaration'''
	pass


def p_includes(p):
	'''includes : INCLUDE program END_INCLUDE includes
			   	| INCLUDE program END_INCLUDE'''


def p_declarations_maybe(p):
	'''declarations_maybe : declaration declarations_maybe
						  | '''
	pass


def p_declaration(p):
	'''declaration : variable_declaration
				   | function_declaration
				   | function_definition'''
	pass


def p_variable_declaration(p):
	'''variable_declaration : type declarators SEMICOLON'''
	pass


def p_type(p):
	'''type : basic_type 
			| type TIMES'''
	pass


def p_basic_type(p):
	'''basic_type : INT
				  | CHARACTER
				  | DOUBLE
				  | BOOLEAN'''
	pass


def p_declarators(p):
	'''declarators : declarator COMMA declarators
				   | declarator'''
	pass


def p_declarator(p):
	'''declarator : ID array_maybe'''
	pass


def p_function_declaration(p):
	'''function_declaration : type ID LPAREN parameter_list_maybe RPAREN SEMICOLON
							| VOID ID LPAREN parameter_list_maybe RPAREN SEMICOLON'''
	pass


def p_parameter_list_maybe(p):
	'''parameter_list_maybe : parameter_list
							| '''
	pass


def p_parameter_list(p):
	'''parameter_list : parameter COMMA parameter_list
					  | parameter'''
	pass


def p_parameter(p):
	'''parameter : type ID
				 | BYREF type ID'''
	pass


def p_function_definition(p):
	'''function_definition : type ID LPAREN parameter_list_maybe RPAREN LBRACE declarations_maybe statements_maybe RBRACE
						   | VOID ID LPAREN parameter_list_maybe RPAREN LBRACE declarations_maybe statements_maybe RBRACE'''
	pass


def p_statements_maybe(p):
	'''statements_maybe : statement statements_maybe
					    | '''
	pass


def p_statement(p):
	'''statement : SEMICOLON
				 | expression SEMICOLON
				 | LBRACE statements_maybe RBRACE
				 | IF LPAREN expression RPAREN statement ELSE statement
				 | IF LPAREN expression RPAREN statement
				 | label_maybe FOR LPAREN expression_maybe SEMICOLON expression_maybe SEMICOLON expression_maybe RPAREN statement
				 | CONTINUE SEMICOLON
				 | CONTINUE ID SEMICOLON
				 | BREAK SEMICOLON
				 | BREAK ID SEMICOLON
				 | RETURN SEMICOLON
				 | RETURN expression SEMICOLON'''
	pass


def p_label_maybe(p):
	'''label_maybe : ID COLON
				   | '''
	pass


def p_expression_maybe(p):
	'''expression_maybe : expression
						| '''
	pass


def p_array(p):
	'''array : LBRACKET expression RBRACKET'''


def p_array_maybe(p):
	'''array_maybe : array
				   | '''
	pass


def p_expression(p):
	'''expression : ID
				  | TRUE
				  | FALSE
				  | NULL
				  | ICONST
				  | CCONST
				  | FCONST
				  | SCONST
				  | LPAREN expression RPAREN
				  | ID LPAREN expression_maybe RPAREN
				  | expression array
				  | unary_operator expression
				  | expression unary_assignment
				  | unary_assignment expression
				  | expression TIMES expression
				  | expression DIVIDE expression
				  | expression MOD expression
				  | expression PLUS expression
				  | expression MINUS expression
				  | expression LT expression
				  | expression GT expression
				  | expression LE expression
				  | expression GE expression
				  | expression EQ expression
				  | expression NE expression
				  | expression LAND expression
				  | expression LOR expression
				  | expression COMMA expression
				  | expression binary_assignment expression
				  | LPAREN type RPAREN expression %prec TYPECAST
				  | expression CONDOP expression COLON expression
				  | NEW type array_maybe
				  | DELETE expression'''
	pass


def p_expression_maybe(p):
	'''expression_maybe : expression
						| '''
	pass


def p_unary_operator(p):
	'''unary_operator : AND
					  | TIMES
					  | PLUS
					  | MINUS
					  | LNOT'''
	pass


def p_unary_assignment(p):
	'''unary_assignment : PLUSPLUS
						| MINUSMINUS'''
	pass


def p_binary_assignment(p):
	'''binary_assignment : EQUALS
						 | TIMESEQUAL
						 | DIVEQUAL
						 | MODEQUAL
						 | PLUSEQUAL
						 | MINUSEQUAL'''
	pass


def p_empty(p):
	'''empty : '''
	pass


def p_error(p):
	print("Error 42: Failed to parse line {0} with token ({1}, {2}).".format(p.lineno, p.type, p.value))
	pass


parser = yacc.yacc()


def token_func():
	if len(lexer.token_list):
		return lexer.token_list.pop(0)


while True:
	arguments = sys.argv

	input_file_name = arguments[1]
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

	print('\n\nLexer Tokens:\n')

	lexer.my_lexer(input_file_name)
	for i in lexer.token_list:
		print(i)

	print("\nThe End!\n\n")

	result = parser.parse(data, debug=1, tokenfunc=token_func)

	print(result)

	break
