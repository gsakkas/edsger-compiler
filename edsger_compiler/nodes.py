from __future__ import print_function
import re

nested = {}

class Node:
    def __init__(self, n_type, children=None, leaf=None, filename=''):
        self.type = n_type
        self.count = 0
        self.leaf = leaf
        if children:
            self.children = children
        else:
            self.children = []


    def print_ast(self, num_of_tabs):
        tabs = '\t' * num_of_tabs

        print(tabs + "Node(" + str(self.type) + ", " + str(self.leaf) + ")")

        if self.children:
            for child in traverse(self.children):
                child.print_ast(num_of_tabs + 1)
        pass

    def insert_in_children(self, idx, child):
        self.children.insert(idx, child)
        return self

    def check(self, variables = {}, funs_dec = {}, funs_def = {}):
        if self.type == 'program':
            funs = (funs_dec, funs_def)

            for child in self.children:
                if child.type == 'include':
                    (variables, funs_dec, funs_def) = child.check_include(variables, funs_dec, funs_def)
                elif child.type == 'variable_declaration':
                    variables = child.check_variable_declaration(variables, funs_dec, funs_def)
                elif child.type == 'function_declaration':
                    funs_dec = child.check_function_declaration(variables, funs_dec, funs_def)
                elif child.type == 'function_definition':
                    funs_def = child.check_function_definition(variables, funs_dec, funs_def)
            return (variables, funs_dec, funs_def)

    def check_include(self, variables, funs_dec, funs_def):
        variables = {}
        for child in self.children:
            if child.type == 'program':
                (variables, funs_dec, funs_def) = child.check(variables, funs_dec, funs_def)
            elif child.type == 'include':
                (variables, funs_dec, funs_def) = child.check_include(variables, funs_dec, funs_def)
            elif child.type == 'variable_declaration':
                variables = child.check_variable_declaration(variables, funs_dec, funs_def, [])
            elif child.type == 'function_declaration':
                funs_dec = child.check_function_declaration(variables, funs_dec, funs_def, [])
            elif child.type == 'function_definition':
                funs_def = child.check_function_definition(variables, funs_dec, funs_def)
        return (variables, funs_dec, funs_def)

    def check_variable_declaration(self, variables, funs_dec, funs_def):
        for child in self.children[0].children:
            if child.leaf not in variables:
                if child.children[0].type == 'not_array':
                    if '*' in self.leaf:
                        variables[child.leaf] = 'dynamic' + self.leaf
                    else:
                        variables[child.leaf] = self.leaf
                else:
                    temp = child.children[0].children[0].check_expression(variables, funs_dec, funs_def)
                    if temp == 'int' or temp == 'cint':
                        variables[child.leaf] = 'static' + self.leaf
                    else:
                        print("Error: Array size must be of type int")
                        exit(42)
            else:
                print("Error: conflicting types for '" + child.leaf + "'")
                exit(42)

        return variables

    def check_function_declaration(self, variables, funs_dec, funs_def):
        fun = self.leaf
        local_variables = {}

        if self.children[1].leaf != 'empty':
            for child in self.children[1].children:
                if child.leaf not in local_variables:
                    if '*' in child.children[0].leaf:
                        local_variables[child.leaf] = 'dynamic' + child.children[0].leaf
                    else:
                        local_variables[child.leaf] = child.children[0].leaf
                    fun = fun + child.children[0].leaf
                else:
                    print(
                        "Error: conflicting types for '" + child.leaf + "' in function '" + self.leaf + "' declaration")
                    exit(42)

        if fun not in funs_dec and fun not in funs_def:
            if '*' in self.children[0].leaf:
                funs_dec[fun] = 'dynamic' + self.children[0].leaf
            else:
                funs_dec[fun] = self.children[0].leaf
        else:
            print("Error: Function " + self.leaf + " has multiple declarations")
            exit(42)

        return funs_dec

    def check_function_definition(self, variables, funs_dec, funs_def):
        fun = (self.leaf)
        local_variables = {}
        nested_variables = {}
        labels = []
        rem = []
        global nested

        if self.children[1].leaf != 'empty':
            for child in self.children[1].children:
                if child.leaf not in local_variables:
                    if '*' in child.children[0].leaf:
                        local_variables[child.leaf] = 'dynamic' + child.children[0].leaf
                    else:
                        local_variables[child.leaf] = child.children[0].leaf
                    fun = fun + child.children[0].leaf
                else:
                    print(
                        "Error: conflicting types for '" + child.leaf + "' in function '" + self.leaf + "' declaration")
                    exit(42)

        if fun not in funs_def:
            if '*' in self.children[0].leaf:
                funs_def[fun] = 'dynamic' + 'c' + self.children[0].leaf
            else:
                funs_def[fun] = 'c' + self.children[0].leaf
        else:
            print("Error: Function " + self.leaf + " has multiple declarations")
            exit(42)

        local_funs_dec = funs_dec.copy()
        local_funs_def = funs_def.copy()

        self.children[2].sort()

        for child in self.children[2].children:
            if child.type == 'variable_declaration':
                local_variables = child.check_variable_declaration(local_variables, funs_dec, funs_def)
            elif child.type == 'function_declaration':
            	name = child.find_name()
                try :
                    nested[name]
                except:
                    nested[name] = [0, True]
                else:
                    aba = nested[name]
                    nested[name] = [aba[0]+1, True]
                rem.append(name)
                child.leaf = '_' + str(nested[name][0]) + '_' + child.leaf
                local_funs_dec = child.check_function_declaration(nested_variables, local_funs_dec, local_funs_def)
            elif child.type == 'function_definition':
            	name = child.find_name()
                for var in variables:
                    nested_variables[var] = variables[var]
                for var in local_variables:
                    nested_variables[var] = local_variables[var]
                try :
                    nested[name]
                except:
                    nested[name] = [0, True]
                else:
                	if name not in rem:
	                    aba = nested[name]
	                    nested[name] = [aba[0]+1, True]
                rem.append(name)
                child.leaf = '_' + str(nested[name][0]) + '_' + child.leaf
                local_funs_def = child.check_function_definition(nested_variables, local_funs_dec, local_funs_def)

        for var in variables:
            if var not in local_variables:
                local_variables[var] = variables[var]

        child = self.children[3]

        result = child.check_statement(local_variables, local_funs_dec, local_funs_def, labels)
        return_found = False
        fun_type = funs_def[fun]

        for statement in result:
            if statement == 'break' or statement == 'continue':
                print("Error: \"" + statement + "\" statement not within a loop")
                exit(42)
            elif 'break' in statement or 'continue' in statement:
                label = statement.split()[1]
                if label not in labels:
                    print("Error: undefined label: " + label)
                    exit(42)
            elif 'return' in statement:
                if fun_type == statement.split()[1]:
                    return_found = True
                elif fun_type == 'c' + statement.split()[1] or fun_type[7:] == 'c' + statement.split()[1][7:]:
                    return_found = True
                elif fun_type == 'dynamicchar*' and (
                        statement.split()[1] == 'staticchar*' or statement.split()[1] == 'cstring'):
                    return_found = True
                elif 'dynamic' in fun_type and 'static' in statement.split()[1]:
                    if fun_type.replace('dynamic', '') == statement.split()[1].replace('static', ''):
                        return_found = True
                    else:
                        print("Error: Return type not the same as function definition of \"" + self.leaf + "\"")
                        exit(42)
                else:
                    print("Error: Return type not the same as function definition of \"" + self.leaf + "\"")
                    exit(42)
        if not return_found and fun_type != 'cvoid':
            print("Error: No \"return\" for the function \"" + self.leaf + "\"")
            exit(42)

        for r in rem:
            nested[r][1] = False

        return funs_def

    def check_expression(self, local_variables, funs_dec, funs_def):
        if self.type == 'constant':
            if self.leaf == "true" or self.leaf == "false":
                return "cbool"
            else:
                return self.leaf.split(' ')[0]
        elif self.type == 'variable':
            if self.leaf in local_variables:
                return local_variables[self.leaf]
            else:
                print("Error: Undeclared variable '" + self.leaf + "'")
                exit(42)
        elif self.type == 'function_call':
            flag = 0
            fun = self.leaf
            for child in self.children[0].children:
                param = child.check_expression(local_variables, funs_dec, funs_def)
                if 'static' in param:
                    param = param.replace('static', '') + '*'
                if param == 'cint':
                    param = 'int'
                elif param == 'cdouble':
                    param = 'double'
                elif param == 'cchar':
                    param = 'char'
                elif param == 'cstring':
                    param = 'char*'
                elif param == 'true' or param == 'false':
                    param = 'bool'
                elif 'dynamic' in param:
                    param = param[7:]
                elif param == 'NULL':
                    param = '(int|char|double|bool)*+'
                    flag = 1
                fun += param
            if fun in nested:
                if nested[fun][1]:
                    fun = '_' + str(nested[fun][0]) + '_' + fun

            if flag == 1:
                keys = funs_dec.keys()
                temp = '^' + fun + '$'
                temp = temp.replace('*', '\*')
                for key in keys:
                    searchObj = re.search(temp, key)
                    if searchObj:
                        return funs_dec[searchObj.group()]
                keys = funs_def.keys()
                for key in keys:
                    searchObj = re.search(temp, key)
                    if searchObj:
                        return funs_def[searchObj.group()]
            elif fun in funs_dec:
                self.leaf = fun
                return funs_dec[fun]
            elif fun in funs_def:
                self.leaf = fun
                return funs_def[fun]
            else:
                print("Error: Function '" + fun + "' is undefined")
                exit(42)
        elif self.leaf == 'typecast':
            expr_type = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if expr_type[0] == 'c' and expr_type[1] != 'h':
                expr_type = expr_type[1:]
            if expr_type == self.children[0].leaf:
                return self.children[0].leaf
            elif self.children[0].leaf == 'int':
                if expr_type == 'char':
                    self.leaf = 'charint'
                    return self.children[0].leaf
                elif expr_type == 'double':
                    self.leaf = 'doubleint'
                    return self.children[0].leaf
                elif expr_type == 'bool':
                    self.leaf = 'boolint'
                    return self.children[0].leaf
                else:
                    print("Error: You can't cast from " + expr_type + " to " + self.children[0].leaf)
                    exit(42)
            elif self.children[0].leaf == 'double':
                if expr_type == 'int':
                    self.leaf = 'intdouble'
                    return self.children[0].leaf
                elif expr_type == 'char':
                    self.leaf = 'chardouble'
                    return self.children[0].leaf
                else:
                    print("Error: You can't cast from " + expr_type + " to " + self.children[0].leaf)
                    exit(42)
            elif self.children[0].leaf == 'bool':
                if expr_type == 'int':
                    self.leaf = 'intbool'
                    return self.children[0].leaf
                elif expr_type == 'char':
                    self.leaf = 'charbool'
                    return self.children[0].leaf
                elif expr_type == 'double':
                    self.leaf = 'doublebool'
                    return self.children[0].leaf
                else:
                    print("Error: You can't cast from " + expr_type + " to " + self.children[0].leaf)
                    exit(42)
            elif self.children[0].leaf == 'char':
                if expr_type == 'int':
                    self.leaf = 'intchar'
                    return self.children[0].leaf
                else:
                    print("Error: You can't cast from " + expr_type + " to " + self.children[0].leaf)
                    exit(42)
            else:
                print("Error: You can't cast from " + expr_type + " to " + self.children[0].leaf)
                exit(42)
        elif self.leaf == 'condop':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'bool'or temp == 'cbool':
                type1 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
                type2 = self.children[2].check_expression(local_variables, funs_dec, funs_def)
                if type1 == type2:
                    return type1
                elif type1.replace('static', '') == type2.replace('dynamic', '')[:-1]:
                    return type1
                elif type1.replace('dynamic', '')[:-1] == type2.replace('static', ''):
                    return type2
                elif type1.replace('dynamic', '')[:-1] == type2.replace('dynamic', '')[:-1]:
                    return type1
                elif type1 == 'NULL' and ('static' in type2 or 'dynamic' in type2):
                    return type2
                elif ('static' in type1 or 'dynamic' in type1) and type2 == 'NULL':
                    return type1
                else:
                    print("Error: \"?:\" operator must have same types and your expressions are of type: " +
                          type1 + " and " + type2 + "!")
                    exit(42)
            else:
                print("Error: \"?:\" operator needs bool expression, your expression is of type: " + self.children[
                    0].check_expression(local_variables, funs_dec, funs_def) + "!")
                exit(42)
        elif self.leaf == '&&' or self.leaf == '||':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'bool' or temp == 'true' or temp == 'false' or temp == 'cbool':
                if temp2 == 'bool' or temp2 == 'true' or temp2 == 'false' or temp2 == 'cbool':
                    return 'cbool'
                else:
                    print(
                        "Error: " + self.leaf + " operator parameters must be bool, but yours are: " + temp + ", " + temp2)
                    exit(42)
            else:
                print("Error: " + self.leaf + " operator parameters must be bool, but yours are: " + temp + ", " + temp2)
                exit(42)
        elif self.leaf == ',':
            self.children[0].check_expression(local_variables, funs_dec, funs_def)
            return self.children[1].check_expression(local_variables, funs_dec, funs_def)
        elif self.leaf == 'new':
            if self.children[1].type == 'not_array':
                return 'dynamic' + self.children[0].leaf + '*'
            else:
                temp2 = self.children[1].children[0].check_expression(local_variables, funs_dec, funs_def)
                if temp2 == 'int' or temp2 == 'cint':
                    return 'dynamic' + self.children[0].leaf + '*'
                else:
                    print("Error: size of array has non-integer type: " + self.children[1].children[0].check_expression(
                        local_variables, funs_dec, funs_def))
                    exit(42)
        elif self.leaf == 'delete':
            tempstr = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if 'dynamic' in tempstr or '*' in tempstr:
                return tempstr
            else:
                print("Error: Cannot delete memory that was not dynamically allocated!")
                exit(42)
        elif self.leaf == 'array':
            tempstr = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'array'
            if 'static' in tempstr or '*' in tempstr:
                temp = self.children[1].children[0].check_expression(local_variables, funs_dec, funs_def)
                if temp == 'int' or temp == 'cint':
                    if 'static' in tempstr:
                        if len(tempstr.split('*')) > 2:
                            return tempstr.replace('static', 'dynamic')
                        else:
                            return tempstr.replace('static', '')
                    else:
                        if len(tempstr.split('*')) > 2:
                            return tempstr[:-1]
                        else:
                            return tempstr.replace('dynamic', '')[:-1]
                else:
                    print("Error: size of array has non-integer type: " + temp)
                    exit(42)
            else:
                print("Error: subscripted value is neither array nor pointer")
                exit(42)
        elif self.leaf == '&':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'unary_operator'
            if 'dynamic' not in temp:
                temp = 'dynamic' + temp
            return temp + '*'
        elif self.leaf == '*' and len(self.children) == 1:
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'unary_operator'
            if len(temp.split('*')) > 1 or 'static' in temp:
                if "NULL" not in temp:
                    if 'static' in temp:
                        return temp.replace('static', '')
                    else:
                        return temp.replace('dynamic', '')[:-1]
                else:
                    print("Error: dereferencing NULL pointer")
                    exit(42)
            else:
                print("Error: trying dereference something that isn't pointer")
                exit(42)
        elif self.leaf == '-' and len(self.children) == 1:
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'unary_operator'
            if temp == 'int' or temp == 'double' or temp == 'cint' or temp == 'cdouble':
                return temp
            else:
                print("Error: wrong type argument to unary minus")
                exit(42)
        elif self.leaf == '+' and len(self.children) == 1:
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'unary_operator'
            if temp == 'int' or temp == 'double' or temp == 'cint' or temp == 'cdouble':
                return temp
            else:
                print("Error: wrong type argument to unary plus")
                exit(42)
        elif self.leaf == '!':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'unary_operator'
            if temp == 'bool' or temp == 'true' or temp == 'false' or temp == 'cbool':
                return 'cbool'
            else:
                print("Error: wrong type argument to logical not")
                exit(42)
        elif self.leaf == '++':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if 'static' in temp:
                print("Error: lvalue required as increment operand")
                exit(42)
            elif temp == 'int' or temp == 'double':
                self.type += '_' + temp
                return temp
            elif temp.find('*') != -1:
                self.type += '_pointer'
                return temp
            else:
                print("Error: can only increment integer, double or pointer type variables")
                exit(42)
        elif self.leaf == '--':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if 'static' in temp:
                print("Error: lvalue required as increment operand")
                exit(42)
            elif temp == 'int' or temp == 'double':
                self.type += '_' + temp
                return temp
            elif temp.find('*') != -1:
                self.type += '_pointer'
                return temp
            else:
                print("Error: can only decrease integer, double or pointer type variables")
                exit(42)
        elif self.leaf == '+':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint' or temp2.find('*') != -1 or 'static' in temp2:
                    if 'static' in temp2 or '*' in temp2:
                        self.children[1].leaf = (self.children[0].leaf, 'p')
                        self.type = 'binary_operator_int'
                        return temp2
                    else:
                        self.type = 'binary_operator_int'
                        return 'cint'
                else:
                    print("Error: invalid operands to binary +")
                    exit(42)
            elif temp.find('*') != -1 or 'static' in temp:
                if temp2 == 'int' or temp2 == 'cint':
                    self.children[0].leaf = (self.children[0].leaf, 'p')
                    self.type = 'binary_operator_int'
                    return temp
                else:
                    print("Error: invalid operands to binary +")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '+' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary +")
                exit(42)
        elif self.leaf == '-':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint' or temp2.find('*') != -1 or 'static' in temp2:
                    if 'static' in temp2 or '*' in temp2:
                        self.children[1].leaf = (self.children[0].leaf, 'p')
                        self.type = 'binary_operator_int'
                        return temp2
                    else:
                        self.type = 'binary_operator_int'
                        return 'cint'
                else:
                    print("Error: invalid operands to binary -")
                    exit(42)
            elif temp.find('*') != -1 or 'static' in temp:
                if temp2 == 'int' or temp2 == 'cint':
                    self.children[0].leaf = (self.children[0].leaf, 'p')
                    self.type = 'binary_operator_int'
                    return temp
                else:
                    print("Error: invalid operands to binary -")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '-' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary -")
                exit(42)
        elif self.leaf == '*':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint':
                    self.type = 'binary_operator_int'
                    return 'cint'
                else:
                    print("Error: both arguments to binary '*' must be of same type")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '*' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary *")
                exit(42)
        elif self.leaf == '/':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint':
                    self.type = 'binary_operator_int'
                    return 'cint'
                else:
                    print("Error: both arguments to binary '/' must be of same type")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '/' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary /")
                exit(42)
        elif self.leaf == '%':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint':
                    self.type = 'binary_operator_int'
                    return 'cint'
                else:
                    print("Error: both arguments to binary '%' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary %")
                exit(42)
        elif self.leaf == '=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if temp == temp2:
                if 'static' not in temp:
                    return temp
                else:
                    print("Error: assignment to expression with array type")
                    exit(42)
            elif 'dynamic' in temp or '*' in temp:
                if temp.replace('dynamic', '')[:-1] == temp2.replace('static', ''):
                    return temp
                elif temp.replace('dynamic', '')[:-1] == temp2.replace('dynamic', '')[:-1]:
                    return temp
                elif temp2 == 'NULL':
                    self.children[1].leaf += ' ' + temp.replace('dynamic', '')[:-1]
                    return 'NULL'
                else:
                    print("Error: assignment to expression with array type")
                    exit(42)
            elif 'c' + temp == temp2:
                return temp
            elif temp == 'bool' and (temp2 == 'true' or temp2 == 'false' or temp2 == 'cbool' or temp2 == 'bool'):
                return temp
            else:
                print("Error: both arguments to assignement must be of same type")
                exit(42)
        elif self.leaf == '+=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            self.leaf = '='
            if 'int' in temp:
                a = 'int'
            elif 'double' in temp:
                a = 'float'
            self.children = [self.children[0], Node('binary_operator_' + a, self.children,'+')]
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint' or temp2.find('*') != -1 or 'static' in temp2:
                    if 'static' in temp2 or '*' in temp2:
                        self.children[1].children[1].leaf = (self.children[1].children[0].leaf, 'p')
                        self.children[1].type = 'binary_operator_int'
                        return temp2
                    else:
                        self.children[1].type = 'binary_operator_int'
                        return 'cint'
                else:
                    print("Error: invalid operands to binary +")
                    exit(42)
            elif temp.find('*') != -1 or 'static' in temp:
                if temp2 == 'int' or temp2 == 'cint':
                    self.children[1].children[0].leaf = (self.children[1].children[0].leaf, 'p')
                    self.children[1].type = 'binary_operator_int'
                    return temp
                else:
                    print("Error: invalid operands to binary +")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.children[1].type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '+' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary +")
                exit(42)
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if temp == temp2 or 'c' + temp == temp2:
                return temp
            elif '*' in temp and (temp2 == 'int' or temp2 == 'cint'):
                return temp
            elif 'dynamic' in temp and (temp2 == 'int' or temp2 == 'cint'):
                return temp[7:]
            else:
                print("Error: invalid operands to binary +=")
                exit(42)
        elif self.leaf == '-=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            self.leaf = '='
            self.children = [self.children[0], Node('binary_operator_' + temp, self.children,'-')]
            if temp == 'int' or temp == 'cint':
                if temp2 == 'int' or temp2 == 'cint' or temp2.find('*') != -1 or 'static' in temp2:
                    if 'static' in temp2 or '*' in temp2:
                        self.children[1].children[1].leaf = (self.children[1].children[0].leaf, 'p')
                        self.children[1].type = 'binary_operator_int'
                        return temp2
                    else:
                        self.children[1].type = 'binary_operator_int'
                        return 'cint'
                else:
                    print("Error: invalid operands to binary -")
                    exit(42)
            elif temp.find('*') != -1 or 'static' in temp:
                if temp2 == 'int' or temp2 == 'cint':
                    self.children[1].children[0].leaf = (self.children[1].children[0].leaf, 'p')
                    self.children[1].type = 'binary_operator_int'
                    return temp
                else:
                    print("Error: invalid operands to binary -")
                    exit(42)
            elif temp == 'double' or temp == 'cdouble':
                if temp2 == 'double' or temp2 == 'cdouble':
                    self.children[1].type = 'binary_operator_float'
                    return 'cdouble'
                else:
                    print("Error: both arguments to binary '-' must be of same type")
                    exit(42)
            else:
                print("Error: invalid operands to binary -")
                exit(42)
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if temp == temp2 or 'c' + temp == temp2:
                return temp
            elif 'dynamic' in temp and (temp2 == 'int' or temp2 == 'cint'):
                return temp[7:]
            elif '*' in temp and (temp2 == 'int' or temp2 == 'cint'):
                return temp
            else:
                print("Error: invalid operands to binary -=")
                exit(42)
        elif self.leaf == '*=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            self.leaf = '='
            self.children = [self.children[0], Node('binary_operator_' + temp, self.children,'*')]
            self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if (temp == temp2 or 'c' + temp == temp2) and ('int' in temp or 'double' in temp) and ('*' not in temp) and ('*' not in temp2):
                return temp
            else:
                print("Error: invalid operands to binary *=")
                exit(42)
        elif self.leaf == '/=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            self.leaf = '='
            self.children = [self.children[0], Node('binary_operator_' + temp, self.children,'/')]
            self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if (temp == temp2 or 'c' + temp == temp2) and ('int' in temp or 'double' in temp) and ('*' not in temp) and ('*' not in temp2):
                return temp
            else:
                print("Error: invalid operands to binary /=")
                exit(42)
        elif self.leaf == '%=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            self.type = 'binary_operator_equal'
            self.leaf = '='
            self.children = [self.children[0], Node('binary_operator_' + temp, self.children,'%')]
            self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if self.children[0].leaf == 'new' or self.children[0].leaf == 'delete' or 'function ' in self.children[0].leaf or 'static' in temp:
                print("Error: lvalue required as left operand of assignment")
                exit(42)
            if (temp == temp2 or 'c' + temp == temp2) and ('int' in temp or 'double' in temp):
                return temp
            else:
                print("Error: invalid operands to binary %=")
                exit(42)
        elif self.leaf == '==' or self.leaf == '!=' or self.leaf == '<' or self.leaf == '>' or self.leaf == '<=' or self.leaf == '>=':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            temp2 = self.children[1].check_expression(local_variables, funs_dec, funs_def)
            if ('*' in temp or 'static' in temp) and ('*' in temp2 or 'static' in temp2):
                self.type = 'binary_operator_int'
                return 'cbool'
            elif '*' in temp and temp2 == 'NULL':
                self.children[1].leaf += ' ' + temp.replace('dynamic', '')[:-1]
                self.type = 'binary_operator_int'
                return 'cbool'
            elif 'static' in temp and temp2 == 'NULL':
                self.children[1].leaf += ' ' + temp.replace('static', '')
                self.type = 'binary_operator_int'
                return 'cbool'
            elif temp == 'NULL' and temp2 == 'NULL':
                self.type = 'binary_operator_int'
                return 'cbool'
            elif temp == temp2 or 'c' + temp == temp2 or 'c' + temp2 == temp:
                if 'double' in temp:
                    temp = 'float'
                if temp[0] != 'c' or temp[0:2] == 'ch':
                    self.type = 'binary_operator_' + temp
                else:
                    self.type = 'binary_operator_' + temp[1:]
                return 'cbool'
            elif temp == 'bool' or temp == 'true' or temp == 'false' or temp == 'cbool':
                if temp2 == 'bool' or temp2 == 'true' or temp2 == 'false' or temp2 == 'cbool':
                    self.type = 'binary_operator_int'
                    return 'cbool'
                else:
                    print("Error: both arguments of a comparison must be of the same type")
                    exit(42)
            else:
                print("Error: both arguments of a comparison must be of the same type")
                exit(42)

    def check_statement(self, local_variables, funs_dec, funs_def, labels):
        if self.type == 'statements':
            result = []
            if self.children:
                for child in self.children:
                    if child.type == 'statement' or child.type == 'statements':
                        result += child.check_statement(local_variables, funs_dec, funs_def, labels)
                    else:
                        child.check_expression(local_variables, funs_dec, funs_def)
            return result
        elif not self.children and self.leaf == ';':
            return []
        elif not self.children and self.leaf == 'return':
            return ['return void']
        elif self.leaf == 'return':
            child = self.children[0]
            return ['return ' + child.check_expression(local_variables, funs_dec, funs_def)]
        elif self.leaf == 'continue':
            return ['continue']
        elif self.leaf == 'continue_to':
            label = self.children[0].leaf
            return ['continue ' + label]
        elif self.leaf == 'break':
            return ['break']
        elif self.leaf =='break_to':
            label = self.children[0].leaf
            return ['break ' + label]
        elif self.leaf == 'for':
            for idx in range(len(self.children) - 1):
                if self.children[idx].type != 'no_expression':
                    temp = self.children[idx].check_expression(local_variables, funs_dec, funs_def)
                    if idx == 1 and temp != 'bool' and temp != 'cbool':
                        print("Error: \"for\" statement: condition not a \"bool\" type!")
                        exit(42)
            result = []
            child = self.children[-1]
            result += child.check_statement(local_variables, funs_dec, funs_def, labels)
            if 'break' in result or 'continue' in result:
                result = list(filter(('break').__ne__, result))
                result = list(filter(('continue').__ne__, result))
            return result
        elif self.leaf == 'for_with_label':
            kid = self.children[0]
            if kid.leaf in labels:
                print("Error: \"label\": " + kid.leaf + "already exists!")
                exit(42)
            else:
                labels.append(kid.leaf)
            for idx in range(1, len(self.children) - 1):
                if self.children[idx].type != 'no_expression':
                    temp = self.children[idx].check_expression(local_variables, funs_dec, funs_def)
                    if idx == 2 and temp != 'bool' and temp != 'cbool':
                        print("Error: \"for\" statement: condition not a \"bool\" type!")
                        exit(42)
            result = []
            child = self.children[-1]
            if child.children:
                result += child.check_statement(local_variables, funs_dec, funs_def, labels)
            if 'break' in result or 'continue' in result:
                result = list(filter(('break').__ne__, result))
                result = list(filter(('continue').__ne__, result))
            return result
        elif self.leaf == 'if':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if temp != 'bool' and temp != 'cbool':
                print("Error: \"if\" statement: condition not a \"bool\" type!")
                exit(42)
            return self.children[1].check_statement(local_variables, funs_dec, funs_def, labels)
        elif self.leaf == 'if_else':
            temp = self.children[0].check_expression(local_variables, funs_dec, funs_def)
            if temp != 'bool' and temp != 'cbool':
                print("Error: \"if\" statement: condition not a \"bool\" type!")
                exit(42)
            result = self.children[1].check_statement(local_variables, funs_dec, funs_def, labels)
            result += self.children[2].check_statement(local_variables, funs_dec, funs_def, labels)
            return result
        else:
            self.check_expression(local_variables, funs_dec, funs_def)
        return []


    def find_name(self):
    	name = self.leaf
        if self.children[1].leaf != 'empty':
            for child in self.children[1].children:
                name = name + child.children[0].leaf
        return name


    def sort(self):
    	tempv = []
    	tempf = []
    	for child in self.children:
    		if child.type == 'variable_declaration':
    			tempv.append(child)
    		else:
    			tempf.append(child)
    	self.children = tempv+tempf
    	pass


def traverse(o):
    if isinstance(o, list):
        for value in o:
            yield value
    else:
        yield o

