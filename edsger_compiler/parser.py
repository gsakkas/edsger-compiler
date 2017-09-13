#!/usr/bin/env python

import sys
import os.path
import ply.yacc as yacc
import lexer
from lexer import tokens  # Import lexer information
from nodes import Node

precedence = (
	('nonassoc', 'FUN'),
	('right', 'BIN_ASSIGN'),
	('right', 'EQUALS', 'PLUSEQUAL', 'MINUSEQUAL', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL'),
	('nonassoc', 'CONDOP', 'COLON'),
	('left', 'LOR'),
	('left', 'LAND'),
	('left', 'BIN_REL'),
	('left', 'LT', 'GT', 'GE', 'LE', 'EQ', 'NE'),
	('left', 'BIN_ADD'),
	('left', 'PLUS', 'MINUS'),
	('left', 'BIN_MULT'),
	('left', 'TIMES', 'DIVIDE', 'MOD'),
	('nonassoc', 'TYPECAST'),
	('right', 'PRE_UN'),
	('right', 'PLUSPLUS', 'MINUSMINUS'),
	('right', 'NEW', 'DELETE'),
	('right', 'AND', 'LNOT'),
	('right', 'UN_OP'),
	('left', 'POST_UN'),
	('nonassoc', 'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN'),
)


def p_program(p):
	'''program : declaration program
			   | includes program
			   | declaration includes
			   | declaration'''
	if len(p) == 3:
		if p[2].type == 'program':
			p[0] = p[2].insert_in_children(0, p[1])
		else:
			p[0] = Node("program", [p[1], p[2]], "program")
	else:
		p[0] = Node("program", [p[1]], "program")


def p_includes(p):
	'''includes : INCLUDE program END_INCLUDE includes
			   	| INCLUDE program END_INCLUDE'''
	if len(p) == 5:
		p[0] = Node("include", [p[2], p[4]], p[1])
	else:
		p[0] = Node("include", [p[2]], p[1])


def p_declarations_maybe(p):
	'''declarations_maybe : declaration declarations_maybe
						  | '''
	if len(p) == 3:
		p[0] = p[2].insert_in_children(0, p[1])
	else:
		p[0] = Node('declarations', leaf='declarations_maybe')


def p_declaration(p):
	'''declaration : variable_declaration
				   | function_declaration
				   | function_definition'''
	p[0] = p[1]


def p_variable_declaration(p):
	'''variable_declaration : type declarators SEMICOLON'''
	p[0] = Node("variable_declaration", [p[2]], p[1].leaf)


def p_type(p):
	'''type : basic_type
			| basic_type mult_T'''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = Node("pointer", leaf=(p[1].leaf + p[2].leaf))

def p_mult_T(p):
	'''mult_T : TIMES
			  | mult_T TIMES'''
	if len(p) == 2:
		p[0] = Node("times", leaf='*')
	else:
		p[0] = Node("times", leaf='*'+p[1].leaf)


def p_basic_type(p):
	'''basic_type : INT
				  | CHARACTER
				  | DOUBLE
				  | BOOLEAN'''
	p[0] = Node("basic_type", leaf=p[1])


def p_declarators(p):
	'''declarators : declarator COMMA declarators
				   | declarator'''
	if len(p) == 4:
		p[0] = p[3].insert_in_children(0, p[1])
	else:
		p[0] = Node('declarators', [p[1]], 'declarators')


def p_declarator(p):
	'''declarator : ID array_maybe'''
	if not p[2]:
		p[0] = Node("declarator", leaf=p[1])
	else:
		p[0] = Node("declarator", [p[2]], p[1])


def p_function_declaration(p):
	'''function_declaration : type ID LPAREN parameter_list_maybe RPAREN SEMICOLON
							| VOID ID LPAREN parameter_list_maybe RPAREN SEMICOLON'''
	if p[1] == 'void':
		temp = Node("void", leaf="void")
		p[0] = Node("function_declaration", [temp, p[4]], p[2])
	else:
		p[0] = Node("function_declaration", [p[1], p[4]], p[2])


def p_parameter_list_maybe(p):
	'''parameter_list_maybe : parameter_list
							| '''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = Node('parameter_list', leaf='empty')


def p_parameter_list(p):
	'''parameter_list : parameter COMMA parameter_list
					  | parameter'''
	if len(p) == 4:
		p[0] = p[3].insert_in_children(0, p[1])
	else:
		p[0] = Node('parameter_list', [p[1]], 'parameter_list')


def p_parameter(p):
	'''parameter : type ID
				 | BYREF type ID'''
	if len(p) == 3:
		p[0] = Node("parameter", [p[1]], p[2])
	else:
		p[0] = Node("byref_parameter", [p[2]], p[3])


def p_function_definition(p):
	'''function_definition : type ID LPAREN parameter_list_maybe RPAREN LBRACE declarations_maybe statements_maybe RBRACE
						   | VOID ID LPAREN parameter_list_maybe RPAREN LBRACE declarations_maybe statements_maybe RBRACE'''
	if p[1] == "void":
		temp = Node("void", leaf="void")
		p[0] = Node("function_definition", [temp, p[4], p[7], p[8]], p[2])
	else:
		p[0] = Node("function_definition", [p[1], p[4], p[7], p[8]], p[2])


def p_statements_maybe(p):
	'''statements_maybe : statement statements_maybe
					    | '''
	if len(p) == 3:
		p[0] = p[2].insert_in_children(0, p[1])
	else:
		p[0] = Node('statements', leaf='statements_maybe')


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
	if p[1] == ";":
		p[0] = Node('statement', leaf=p[1])
	elif p[1] == "{":
		p[0] = p[2]
	elif p[1] == 'return' and len(p) == 3:
		p[0] = Node('statement', leaf='return')
	elif p[1] == 'return':
		p[0] = Node('statement', [p[2]], 'return')
	elif len(p) == 8:
		p[0] = Node('statement', [p[3], p[5], p[7]], 'if_else')
	elif p[1] == "if":
		p[0] = Node('statement', [p[3], p[5]], 'if')
	elif len(p) == 11:
		if p[1].type == "label":
			p[0] = Node('statement', [p[1], p[4], p[6], p[8], p[10]], 'for_with_label')
		else:
			p[0] = Node('statement', [p[4], p[6], p[8], p[10]], 'for')
	elif p[1] == 'continue' and len(p) == 3:
		p[0] = Node('statement', leaf=p[1])
	elif p[1] == 'continue':
		p[0] = Node('statement', [Node('label', leaf=str(p[2]))], 'continue_to')
	elif p[1] == 'break' and len(p) == 3:
		p[0] = Node('statement', leaf=p[1])
	elif p[1] == 'break':
		p[0] = Node('statement', [Node('label', leaf=str(p[2]))], 'break_to')
	else:
		p[0] = p[1]



def p_label_maybe(p):
	'''label_maybe : ID COLON
				   | '''
	if len(p) == 3:
		p[0] = Node('label', leaf=p[1])
	else:
		p[0] = Node('no_label')


def p_expression_maybe(p):
	'''expression_maybe : expression
						| '''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = Node('no_expression')


def p_array(p):
	'''array : LBRACKET expression RBRACKET'''
	p[0] = Node('array', [p[2]], 'array')


def p_array_maybe(p):
	'''array_maybe : array
				   | '''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = Node('not_array')


def p_expression_list_maybe(p):
	'''expression_list_maybe : expression_list
							| '''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = Node('expression_list', leaf='empty')


def p_expression_list(p):
	'''expression_list : expression COMMA expression_list
					   | expression'''
	if len(p) == 4:
		p[0] = p[3].insert_in_children(0, p[1])
	else:
		p[0] = Node('expression_list', [p[1]], 'expression_list')

def p_expression(p):
	'''expression : ID
				  | constant
				  | LPAREN expression RPAREN
				  | ID LPAREN expression_list_maybe RPAREN %prec FUN
				  | unary_operator expression %prec UN_OP
				  | expression array
				  | expression unary_assignment %prec POST_UN
				  | unary_assignment expression %prec PRE_UN
				  | expression binary_addition_operator expression %prec BIN_ADD
				  | expression binary_mult_operator expression %prec BIN_MULT
				  | expression binary_rel_operator expression %prec BIN_REL
				  | expression LAND expression
				  | expression LOR expression
				  | expression COMMA expression
				  | expression binary_assignment expression %prec BIN_ASSIGN
				  | LPAREN type RPAREN expression %prec TYPECAST
				  | expression CONDOP expression COLON expression
				  | NEW type array_maybe
				  | DELETE expression'''
	if len(p) == 2 and isinstance(p[1], Node):
		p[0] = Node('constant', [p[1]], p[1].leaf)
	elif len(p) == 2:
		p[0] = Node('variable', leaf=p[1])
	elif p[1] == '(' and len(p) == 4:
		p[0] = p[2]
	elif p[2] == '(':
		p[0] = Node('function_call', [p[3]], p[1])
	elif p[1] == '(':
		p[0] = Node('typecast', [p[2], p[4]], 'typecast')
	elif p[2] == '?':
		p[0] = Node('condop', [p[1], p[3], p[5]], 'condop')
	elif p[2] == '&&' or p[2] == '||' or p[2] == ',':
		p[0] = Node('binary_logical_operator', [p[1], p[3]], p[2])
	elif p[1] == 'new':
		p[0] = Node('new', [p[2], p[3]], p[1])
	elif p[1] == 'delete':
		p[0] = Node('delete', [p[2]], p[1])
	elif p[2].type == 'array':
		p[0] = Node('expression', [p[1], p[2]], 'array')
	elif p[1].type == 'unary_operator':
		p[0] = Node('expression', [p[2]], p[1].leaf)
	elif p[1].type == 'unary_assignment':
		p[0] = Node('unary_assignment_bef', [p[2]], p[1].leaf)
	elif p[2].type == 'unary_assignment':
		p[0] = Node('unary_assignment_aft', [p[1]], p[2].leaf)
	else:
		p[0] = Node('binary_operator', [p[1], p[3]], p[2].leaf)


def p_constant(p):
	'''constant : TRUE
				| FALSE
				| NULL
				| ICONST
				| CCONST
				| FCONST
				| SCONST'''
	p[0] = Node('constant', leaf=p[1])


def p_unary_operator(p):
	'''unary_operator : AND
					  | TIMES
					  | PLUS
					  | MINUS
					  | LNOT'''
	p[0] = Node('unary_operator' , leaf=p[1])


def p_unary_assignment(p):
	'''unary_assignment : PLUSPLUS
						| MINUSMINUS'''
	p[0] = Node('unary_assignment' , leaf=p[1])


def p_binary_assignment(p):
	'''binary_assignment : EQUALS
						 | TIMESEQUAL
						 | DIVEQUAL
						 | MODEQUAL
						 | PLUSEQUAL
						 | MINUSEQUAL'''
	p[0] = Node('binary_assignment' , leaf=p[1])


def p_binary_addition_operator(p):
	'''binary_addition_operator : PLUS
					   			| MINUS'''
	p[0] = Node('binary_addition_operator' , leaf=p[1])


def p_binary_mult_operator(p):
	'''binary_mult_operator : TIMES
					   		| DIVIDE
					   		| MOD'''
	p[0] = Node('binary_mult_operator' , leaf=p[1])


def p_binary_rel_operator(p):
	'''binary_rel_operator : LT
				  	   	   | GT
				  	   	   | LE
					   	   | GE
						   | EQ
				  	   	   | NE'''
	p[0] = Node('binary_rel_operator' , leaf=p[1])


def p_error(p):
	print("Error: Failed to parse line {0} with token ({1}, {2}).".format(p.lineno, p.type, p.value))
	exit(-1)


def token_func():
	if len(lexer.token_list):
		return lexer.token_list.pop(0)


def our_parser(arguments):
	input_file_name = arguments

	parser = yacc.yacc()
	lexer.our_lexer(input_file_name)

	fin = open(input_file_name, 'r')
	data = fin.read()
	fin.close()


	result = parser.parse(data, tokenfunc=token_func, tracking=True)
	# result.print_ast(0)
	result.check()

	return result