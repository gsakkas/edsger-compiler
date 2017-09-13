import llvmlite.binding as llvm
import llvmlite.ir as ir
import numpy as np
import sys
import parser
import __builtin__

class longDouble(ir.types._BaseFloatType):
    null = '0.0'
    intrinsic_name = 'x86_fp80'
    width = 128

    def __str__(self):
        return 'x86_fp80'

    def _find_representaion(self, str_val):
        num = np.fromstring(str_val, dtype=np.longdouble, sep=' ')[0]
        byte_array = np.fromstring(num, dtype=np.uint8)
        hex_array = list(reversed(map(hex, byte_array)[:10]))
        for idx in range(len(hex_array)):
            hex_array[idx] = hex_array[idx][2:]
            if int(hex_array[idx], 16) < 16:
                hex_array[idx] = '0' + hex_array[idx]
        ret_val = '0xK' + ''.join(hex_array)
        return ret_val

    def format_constant(self, value):
        return self._find_representaion(value)

longDouble._create_instance()

int16 = ir.IntType(16)
double = longDouble()
char = ir.IntType(8)
boolean = ir.IntType(8)
pointer = ir.PointerType
address_type = pointer(ir.IntType(64))
void = ir.VoidType()

typ = {'int': int16, 'double': double, 'char': char, 'bool': boolean, 'void': void, 'NULL': pointer}
ret = {'int': int16(0), 'double': double(0), 'char': char(0), 'bool': boolean(0)}
asci = {'\\n': 10,'\\t': 9,'\\r': 13,'\\0': 0,'\\\\': 92,'\\\'': 96,'\"': 34, ' ': 32}


class LLVMCodeGenerator(object):
    def __init__(self):

        self.module = ir.Module()
        self.funs = {}
        self.builder = None
        self.label = {'_1': None }
        self.nested = {}
        self.arrays = {}


    def generate_code(self, node):
        return self._codegen(node, {})


    def _create_entry_block_alloca(self, node, var_type, func_symtab):
        builder = ir.IRBuilder()
        builder.position_at_end(self.builder.function.entry_basic_block)
        name = node.leaf

        if node.children[0].leaf != None:
            builder.position_at_start(self.builder.function.entry_basic_block)
            size = self._codegen(node.children[0].children[0], func_symtab)
            builder.position_at_end(self.builder.function.entry_basic_block)
        else:
            size = None
        addr = builder.alloca(var_type, size=size, name=name)
        if node.children[0].leaf != None:
            self.arrays[name] = addr
        return addr


    def _codegen(self, node, func_symtab):
        method = '_codegen_' + node.type
        return getattr(self, method)(node, func_symtab)


    def _codegen_program(self, node, func_symtab):
        for child in node.children:
            if child.type == 'variable_declaration':
                func_symtab = self._codegen(child, func_symtab)
            else:
                self._codegen(child, func_symtab)
        return func_symtab


    def _codegen_include(self, node, func_symtab):
        for child in node.children:
            if child.type == 'variable_declaration':
                func_symtab = self._codegen(child, func_symtab)
            else:
                self._codegen(child, func_symtab)
        return func_symtab


    def _codegen_declarations(self, node, func_symtab):
        for child in node.children:
            if child.type == 'variable_declaration':
                func_symtab = self._codegen(child, func_symtab)
            else:
                self._codegen(child, func_symtab)
        return func_symtab


    def _codegen_constant(self, node, func_symtab):
        val = node.leaf.split(' ')
        if val[0] == 'true':
            return ir.Constant(boolean, 1)
        elif val[0] == 'false':
            return ir.Constant(boolean, 0)
        elif val[0] == 'cchar':
            val[1] = val[1].strip('\'')
            if node.leaf == 'cchar \' \'':
                val = asci[' ']
            elif val[1] in asci:
                val = asci[val[1]]
            elif '\\x' in val[1]:
                val = int(val[1][2:], 16)
            else:
                val = ord(val[1])
            return ir.Constant(char, val)
        elif val[0] == 'cdouble':
            return double(val[1])
        elif val[0] == 'cstring':
            val[1] = node.leaf[8:]
            temp = self.builder.alloca(char, size=len(val[1]+'\\0')+1)
            temp2 = None
            count = 0
            iterable = iter(val[1][1:-1]+'\\0')
            for c in iterable:
                if c != '\\' and temp2 is None:
                    tval = ord(c)
                elif c == '\\' and temp2 is None:
                    temp2 = c
                    continue
                else:
                    if c in asci:
                        tval = asci[c]
                        temp2 = None
                    elif '\\'+c in asci:
                        tval = asci['\\'+c]
                        temp2 = None
                    else:
                        tval = str(iterable.next())
                        tval += str(iterable.next())
                        tval = int(tval, 16)
                    temp2 = None
                self.builder.store(char(tval), self.builder.gep(temp, [int16(count)]))
                count += 1
            return temp
        elif val[0] == 'NULL' and len(val) == 1:
            return ir.Constant(pointer(int16), None)
        elif val[0] == 'NULL':
            dec_typ = typ[val[1].strip('*')]
            while '*' in val[1]:
                dec_type = val[1][:-1]
                dec_typ = pointer(dec_typ)
            return ir.Constant(pointer(dec_typ), None)
        else:
            return ir.Constant(int16, val[1])


    def _codegen_variable_declaration_fun(self, node, func_symtab):
        dec_type = node.leaf
        node = node.children[0]
        dec_typ = typ[dec_type.strip('*')]
        while '*' in dec_type:
            dec_type = dec_type[:-1]
            dec_typ = pointer(dec_typ)

        for child in node.children:
            name = child.leaf
            saved_block = self.builder.block
            var_addr = self._create_entry_block_alloca(child, dec_typ, func_symtab)
            self.builder.position_at_end(saved_block)
            func_symtab[name] = var_addr
        return func_symtab


    def _codegen_variable_declaration(self, node, func_symtab):
        dec_type = node.leaf
        node = node.children[0]
        module = self.module
        dec_typ = typ[dec_type.strip('*')]
        while '*' in dec_type:
            dec_type = dec_type[:-1]
            dec_typ = pointer(dec_typ)

        for child in node.children:
            name = child.leaf
            if child.children[0].leaf != None:
                size = child.children[0].children[0].leaf.split(' ')
                if size[0] != 'cint':
                    print("{0}:Error: variable length array declaration not allowed at file scope".format(node.lineno))
                    exit(42)
                else:
                    size = int(size[1])
                dec_typ = ir.ArrayType(dec_typ, size)
            else:
                size = None

            addr = ir.GlobalVariable(self.module, dec_typ, name)
            addr.linkage = "internal"
            if child.children[0].leaf != None:
                self.arrays[name] = addr
        return func_symtab


    def _codegen_variable(self, node, func_symtab):
        name = node.leaf
        if name in func_symtab:
            if name in self.arrays:
                var_addr = self.arrays[name]
                return self.builder.gep(var_addr,[int16(0)])
            else:
                var_addr = func_symtab[name]
        else:
            var_addr = self.module.get_global(name)
        return self.builder.load(var_addr, name)


    def _codegen_new(self, node, func_symtab):
        childs = node.children
        if childs[0].type == 'pointer':
            size = 8
        else:
            size = typ[childs[0].leaf].width/8
        if not childs[1].type == 'not_array':
            elems = self._codegen(childs[1].children[0], func_symtab)
            size = self.builder.mul(int16(size), elems, 'multmp')
        else:
            size = int16(size)
        if not self.module.get_global('__new'):
            func_ty = ir.FunctionType(address_type, tuple([int16]))
            func_new = ir.Function(self.module, func_ty, '__new')
        func_new = self.module.get_global('__new')
        address = self.builder.call(func_new, [size])

        if not self.module.get_global('_init_mem_nodes'):
            func_ty = ir.FunctionType(int16, ())
            func = ir.Function(self.module, func_ty, '_init_mem_nodes')
            self.struct_size = self.builder.call(func, [])


        struct_addr = self.builder.call(func_new, [self.struct_size])
        stack_point = self.builder.gep(address, [int16(0)])
        if not self.module.get_global('_do_new'):
            func_ty = ir.FunctionType(void, tuple([address.type, address_type]))
            func = ir.Function(self.module, func_ty, '_do_new')
        func = self.module.get_global('_do_new')
        self.builder.call(func, [address, struct_addr])

        point_type = childs[0].leaf
        point_typ = typ[point_type.strip('*')]
        while '*' in point_type:
            point_type = point_type[:-1]
            point_typ = pointer(point_typ)
        point_typ = pointer(point_typ)
        return self.builder.bitcast(address, point_typ)

    def _codegen_delete(self, node, func_symtab):
        childs = node.children

        if not self.module.get_global('_init_mem_nodes'):
            func_ty = ir.FunctionType(int16, ())
            func = ir.Function(self.module, func_ty, '_init_mem_nodes')
            self.struct_size = self.builder.call(func, [])

        stack_point = self._find_addr(childs[0], func_symtab)
        stack_point = self.builder.load(stack_point)
        if not self.module.get_global('_do_delete'):
            func_ty = ir.FunctionType(void, tuple([stack_point.type]))
            func = ir.Function(self.module, func_ty, '_do_delete')
        func = self.module.get_global('_do_delete')
        self.builder.call(func, [stack_point])

        if not self.module.get_global('__delete'):
            func_ty = ir.FunctionType(pointer(int16), ())
            func = ir.Function(self.module, func_ty, '__delete')
        func = self.module.get_global('__delete')
        address = self.builder.call(func, [])

        if 'array' in childs[0].leaf:
            point_type = childs[0].children[0].leaf
        else:
            point_type = childs[0].leaf
        point_typ = func_symtab[point_type].type
        return self.builder.bitcast(address, point_typ)


    def _codegen_function_declaration(self, node, func_symtab):
        funcname = node.leaf
        var_type = node.children[0].leaf
        var_typ = typ[var_type.strip('*')]
        args = []
        arg_list = node.children[1]

        flag = 0
        byref = []
        if arg_list.leaf != 'empty':
            for i, arg in enumerate(arg_list.children):
                arg_type = arg.children[0].leaf
                funcname += arg_type
                arg_typ = typ[arg_type.strip('*')]
                while '*' in arg_type:
                    arg_type = arg_type[:-1]
                    arg_typ = pointer(arg_typ)
                if arg.type == 'byref_parameter':
                    arg_typ = pointer(arg_typ)
                    byref +=[i]
                    flag = 1
                args.append(arg_typ)

        if flag == 1:
            self.funs[funcname] = byref

        while '*' in var_type:
            var_type = var_type[:-1]
            var_typ = pointer(var_typ)

        if self.module.get_global(funcname) != None:
            func = self.module.get_global(funcname)
        else:
            func_ty = ir.FunctionType(var_typ, tuple(args))
            func = ir.Function(self.module, func_ty, funcname)

        return func


    def _codegen_function_declaration_nested(self, node, func_symtab):
        funcname = node.leaf
        var_type = node.children[0].leaf
        var_typ = typ[var_type.strip('*')]
        args = []
        arg_list = node.children[1]

        flag = 0
        byref = []
        names = []
        if arg_list.leaf != 'empty':
            for i, arg in enumerate(arg_list.children):
                names.append(arg.leaf)
                arg_type = arg.children[0].leaf
                funcname += arg_type
                arg_typ = typ[arg_type.strip('*')]
                while '*' in arg_type:
                    arg_type = arg_type[:-1]
                    arg_typ = pointer(arg_typ)
                if arg.type == 'byref_parameter':
                    arg_typ = pointer(arg_typ)
                    byref +=[i]
                    flag = 1
                args.append(arg_typ)

        self.nested[funcname] = []
        targs = []
        i = len(args)
        for key in func_symtab.keys():
            if (key not in names):
                targs.append(func_symtab[key].type)
                self.nested[funcname].append((key, i))
                i += 1
        args += targs
        if flag == 1:
            self.funs[funcname] = byref

        while '*' in var_type:
            var_type = var_type[:-1]
            var_typ = pointer(var_typ)

        if self.module.get_global(funcname) != None:
            func = self.module.get_global(funcname)
        else:
            func_ty = ir.FunctionType(var_typ, tuple(args))
            func = ir.Function(self.module, func_ty, funcname)

        return func


    def _codegen_function_definition(self, node, func_symtab):
        func_symtab = {}
        func = self._codegen_function_declaration(node, func_symtab)
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)
        rem_nest = []
        rem_arrays = self.arrays.copy()
        self.arrays = {}

        for i, arg in enumerate(func.args):
            arg.name = node.children[1].children[i].leaf
            if node.children[1].children[i].type == 'byref_parameter':
                alloca = self.builder.alloca(arg.type, name=arg.name)
                self.builder.store(arg, alloca)
                val = self.builder.gep(alloca, [int16(0)])
                func_symtab[arg.name] = self.builder.load(val)
            else:
                alloca = self.builder.alloca(arg.type, name=arg.name)
                self.builder.store(arg, alloca)
                func_symtab[arg.name] = alloca

        for child in node.children[2].children:
            if child.type == 'variable_declaration':
                func_symtab = self._codegen_variable_declaration_fun(child, func_symtab)
            elif child.type == 'function_declaration':
                ne_fun = self._codegen_function_declaration_nested(child, func_symtab)
                name = ne_fun.name
                rem_nest.append(name)
                self.builder = ir.IRBuilder(bb_entry)
            else:
                ne_fun = self._codegen_function_definition_nested(child, func_symtab)
                name = ne_fun.name
                rem_nest.append(name)
                self.builder = ir.IRBuilder(bb_entry)

        self._codegen(node.children[3], func_symtab)

        if not self.builder.block.is_terminated:
            if node.children[0].type == 'void':
                self.builder.ret_void()
            else:
                var_type = node.children[0].leaf
                var_typ = typ[var_type.strip('*')]
                while '*' in var_type:
                    var_type = var_type[:-1]
                    var_typ = pointer(var_typ)
                var_typ = self.builder.load(self.builder.alloca(var_typ, size=0))
                self.builder.ret(var_typ)

        for fun in rem_nest:
            self.nested.pop(fun, None)
        self.arrays = rem_arrays.copy()

        return func


    def _codegen_function_definition_nested(self, node, func_symtab):
        func = self._codegen_function_declaration_nested(node, func_symtab)
        bb_entry = func.append_basic_block('entry')
        self.builder = ir.IRBuilder(bb_entry)
        rem_nest = []
        fun_symtab = {}
        arg_list = []
        nested_args = len(func_symtab)
        rem_arrays = self.arrays.copy()
        rem_byref = self.funs.copy()

        i = 0
        for arg in node.children[1].children:
            name = arg.leaf
            if arg.type == 'byref_parameter':
                alloca = self.builder.alloca(func.args[i].type, name=name)
                self.builder.store(func.args[i], alloca)
                val = self.builder.gep(alloca, [int16(0)])
                fun_symtab[name] = self.builder.load(val)
            else:
                alloca = self.builder.alloca(func.args[i].type, name=name)
                self.builder.store(func.args[i], alloca)
                fun_symtab[name] = alloca
            i += 1
        for key, i in self.nested[func.name]:
            if key not in self.arrays:
                alloca = self.builder.alloca(func_symtab[key].type, name=key)
                self.builder.store(func.args[i], alloca)
                val =  self.builder.gep(alloca, [int16(0)])
                fun_symtab[key] = self.builder.load(val)
                arg_list.append(key)
            else:
                alloca = self.builder.alloca(func_symtab[key].type, name=key)
                self.builder.store(func.args[i], alloca)
                fun_symtab[key] = alloca
                arg_list.append(key)

        self.arrays = {}
        self.nested[func.name] = [func, arg_list, func.args]
        for child in node.children[2].children:
            if child.type == 'variable_declaration':
                fun_symtab = self._codegen_variable_declaration_fun(child, fun_symtab)
            elif child.type == 'function_declaration':
                ne_fun = self._codegen_function_declaration_nested(child, fun_symtab)
                self.builder = ir.IRBuilder(bb_entry)
            else:
                ne_fun = self._codegen_function_definition_nested(child, fun_symtab)
                self.builder = ir.IRBuilder(bb_entry)


        self._codegen(node.children[3], fun_symtab)

        if not self.builder.block.is_terminated:
            if node.children[0].type == 'void':
                self.builder.ret_void()
            else:
                var_type = node.children[0].leaf
                var_typ = typ[var_type.strip('*')]
                while '*' in var_type:
                    var_type = var_type[:-1]
                    var_typ = pointer(var_typ)
                var_typ = self.builder.load(self.builder.alloca(var_typ, size=0))
                self.builder.ret(var_typ)
        for fun in rem_nest:
            self.nested.pop(fun)
        self.arrays = rem_arrays.copy()
        self.funs = rem_byref.copy()
        return func


    def _codegen_statements(self, node, func_symtab):
        for statement in node.children:
            self._codegen(statement, func_symtab)
            if self.builder.block.is_terminated:
                cont = self.builder.function.append_basic_block('contbr')
                self.builder.position_at_start(cont)
        pass


    def _codegen_statement(self, node, func_symtab):
        method = '_codegen_' + node.leaf
        return getattr(self, method)(node, func_symtab)


    def _codegen_if(self, node, func_symtab):
        cond_val = self._codegen(node.children[0], func_symtab)
        cmpr = self.builder.trunc(cond_val, ir.IntType(1))

        then_bb = self.builder.function.append_basic_block('then')
        merge_bb = ir.Block(self.builder.function, 'ifcont')
        self.builder.cbranch(cmpr, then_bb, merge_bb)

        self.builder.position_at_start(then_bb)
        then_val = self._codegen(node.children[1], func_symtab)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        else:
            cont = self.builder.function.append_basic_block('contbr')
            self.builder.position_at_start(cont)
            self.builder.branch(merge_bb)

        self.builder.function.basic_blocks.append(merge_bb)
        self.builder.position_at_start(merge_bb)
        pass

    def _codegen_if_else(self, node, func_symtab):
        cond_val = self._codegen(node.children[0], func_symtab)
        cmpr = self.builder.trunc(cond_val, ir.IntType(1))

        then_bb = self.builder.function.append_basic_block('then')
        else_bb = ir.Block(self.builder.function, 'else')
        merge_bb = ir.Block(self.builder.function, 'ifcont')
        self.builder.cbranch(cmpr, then_bb, else_bb)

        self.builder.position_at_start(then_bb)
        then_val = self._codegen(node.children[1], func_symtab)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        else:
            cont = self.builder.function.append_basic_block('contbr')
            self.builder.position_at_start(cont)
            self.builder.branch(merge_bb)


        self.builder.function.basic_blocks.append(else_bb)
        self.builder.position_at_start(else_bb)
        else_val = self._codegen(node.children[2], func_symtab)

        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)
        else:
            cont = self.builder.function.append_basic_block('contbr')
            self.builder.position_at_start(cont)
            self.builder.branch(merge_bb)

        self.builder.function.basic_blocks.append(merge_bb)
        self.builder.position_at_start(merge_bb)
        pass


    def _codegen_for(self, node, func_symtab):
        if node.children[0].type != 'no_expression':
            start_val = self._codegen(node.children[0], func_symtab)

        endcond_bb = self.builder.function.append_basic_block('endcond')
        loop_bb = ir.Block(self.builder.function, 'loop')
        step_bb = ir.Block(self.builder.function, 'step')
        afterloop_bb = ir.Block(self.builder.function, 'afterloop')
        temp = self.label['_1']
        self.label['_1'] = [step_bb, afterloop_bb]

        self.builder.branch(endcond_bb)
        self.builder.position_at_start(endcond_bb)

        if node.children[1].type == 'no_expression':
            self.builder.branch(loop_bb)
        else:
            endcond = self._codegen(node.children[1], func_symtab)
            cmpr = self.builder.trunc(endcond, ir.IntType(1))
            self.builder.cbranch(cmpr, loop_bb, afterloop_bb)
        self.builder.function.basic_blocks.append(loop_bb)
        self.builder.position_at_start(loop_bb)

        self._codegen(node.children[3], func_symtab)
        if not self.builder.block.is_terminated:
            self.builder.branch(step_bb)
        else:
            cont = self.builder.function.append_basic_block('contbr')
            self.builder.position_at_start(cont)
            self.builder.branch(step_bb)
        self.builder.function.basic_blocks.append(step_bb)
        self.builder.position_at_start(step_bb)

        if node.children[2].type != 'no_expression':
            stepval = self._codegen(node.children[2], func_symtab)

        self.builder.branch(endcond_bb)
        self.builder.function.basic_blocks.append(afterloop_bb)
        self.builder.position_at_end(afterloop_bb)
        self.label['_1'] = temp

        pass


    def _codegen_for_with_label(self, node, func_symtab):
        if node.children[1].type != 'no_expression':
            start_val = self._codegen(node.children[1], func_symtab)
        label = node.children[0].leaf

        endcond_bb = self.builder.function.append_basic_block('endcond')
        loop_bb = self.builder.function.append_basic_block('loop')
        step_bb = self.builder.function.append_basic_block('step')
        afterloop_bb = self.builder.function.append_basic_block('afterloop')

        self.label[label] = [step_bb, afterloop_bb]
        temp = self.label['_1']
        self.label['_1'] = [step_bb, afterloop_bb]

        self.builder.branch(endcond_bb)
        self.builder.position_at_start(endcond_bb)

        if node.children[2].type == 'no_expression':
            self.builder.branch(loop_bb)
        else:
            endcond = self._codegen(node.children[2], func_symtab)
            cmpr = self.builder.trunc(endcond, ir.IntType(1))
            self.builder.cbranch(cmpr, loop_bb, afterloop_bb)
        self.builder.position_at_start(loop_bb)

        self._codegen(node.children[4], func_symtab)
        if not self.builder.block.is_terminated:
            self.builder.branch(step_bb)
        else:
            cont = self.builder.function.append_basic_block('contbr')
            self.builder.position_at_start(cont)
            self.builder.branch(step_bb)
        self.builder.position_at_start(step_bb)

        if node.children[3].type != 'no_expression':
            stepval = self._codegen(node.children[3], func_symtab)

        self.builder.branch(endcond_bb)
        self.builder.position_at_start(afterloop_bb)
        self.label.pop(label)
        self.label['_1'] = temp
        pass


    def _codegen_continue(self, node, func_symtab):
        self.builder.branch(self.label['_1'][0])


    def _codegen_continue_to(self, node, func_symtab):
        try:
            label = self.label[node.children[0].leaf][1]
        except:
            print "{0}:Error: Trying to continue to a label in a different loop".format(node.children[0].lineno)
            exit(42)
        else:
            self.builder.branch(label)


    def _codegen_break(self, node, func_symtab):
        self.builder.branch(self.label['_1'][1])


    def _codegen_break_to(self, node, func_symtab):
        try:
            label = self.label[node.children[0].leaf][1]
        except:
            print "{0}:Error: Trying to break to a label in a different loop".format(node.children[0].lineno)
            exit(42)
        else:
            self.builder.branch(label)


    def _codegen_return(self, node, func_symtab):
        if node.children:
            self.builder.ret(self._codegen(node.children[0], func_symtab))
        else:
            self.builder.ret_void()
        pass


    def _codegen_expression(self, node, func_symtab):
        method = '_codegen_' + node.type
        return getattr(self, method)(node, func_symtab)


    def _codegen_function_call(self, node, func_symtab):
        callee_func = self.module.get_global(node.leaf)
        call_args = [self._codegen(arg, func_symtab) for arg in node.children[0].children]
        if node.leaf in self.funs:
            for i in self.funs[node.leaf]:
                tnode = node.children[0].children[i]
                if '*' not in tnode.leaf and tnode.leaf != 'array' and tnode.leaf not in func_symtab:
                    alloca = self.builder.alloca(call_args[i].type)
                    self.builder.store(call_args[i], alloca)
                    call_args[i] = alloca
                else:
                    call_args[i] = self._find_addr(node.children[0].children[i], func_symtab)

        if node.leaf in self.nested:
            try:
                self.nested[node.leaf][0].function_type
            except:
                fun_symtab = [x[0] for x in self.nested[node.leaf]]
            else:
                fun_symtab = self.nested[node.leaf][1]

            for name in fun_symtab:
                args = func_symtab[name]
                call_args.append(args)
        return self.builder.call(callee_func, call_args)


    def _codegen_unary_operator(self, node, func_symtab):
        if node.leaf == '&':
            return self._find_addr(node.children[0], func_symtab)
        elif node.leaf == '*':
            var = self._codegen(node.children[0], func_symtab)
            return self.builder.load(self.builder.gep(var, [int16(0)]), node.leaf+node.children[0].leaf)
        elif node.leaf == '+':
            return self._codegen(node.children[0], func_symtab)
        elif node.leaf == '-':
            val = self._codegen(node.children[0], func_symtab)
            if val.type == double:
                return self.builder.fsub(double('0'), val)
            return self.builder.neg(val)
        else:
            return self.builder.not_(self._codegen(node.children[0], func_symtab))


    def _codegen_unary_assignment_aft_int(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)
        if node.leaf == '++':
            new_val = self.builder.add(val, int16(1), 'inctmp')
        else:
            new_val = self.builder.sub(val, int16(1), 'dectmp')
        self.builder.store(new_val, var_addr)
        return val


    def _codegen_unary_assignment_bef_int(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)

        if node.leaf == '++':
            new_val = self.builder.add(val, int16(1), 'inctmp')
        else:
            new_val = self.builder.sub(val, int16(1), 'dectmp')
        self.builder.store(new_val, var_addr)
        return new_val


    def _codegen_unary_assignment_aft_double(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)

        if node.leaf == '++':
            new_val = self.builder.fadd(val, double('1.0'), 'inctmp')
        else:
            new_val = self.builder.fsub(val, double('1.0'), 'dectmp')
        self.builder.store(new_val, var_addr)
        return val


    def _codegen_unary_assignment_bef_double(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)

        if node.leaf == '++':
            new_val = self.builder.fadd(val, double('1.0'), 'inctmp')
        else:
            new_val = self.builder.fsub(val, double('1.0'), 'dectmp')
        self.builder.store(new_val, var_addr)
        return new_val


    def _codegen_unary_assignment_aft_pointer(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)

        if node.leaf == '++':
            new_val = self.builder.gep(val, [int16(1)])
        else:
            new_val = self.builder.gep(val, [int16(-1)])
        self.builder.store(new_val, var_addr)
        return val


    def _codegen_unary_assignment_bef_pointer(self, node, func_symtab):
        val = self._codegen(node.children[0], func_symtab)
        var_addr = self._find_addr(node.children[0], func_symtab)

        if node.leaf == '++':
            new_val = self.builder.gep(val, [int16(1)])
        else:
            new_val = self.builder.gep(val, [int16(-1)])
        self.builder.store(new_val, var_addr)
        return new_val


    def _codegen_binary_operator_equal(self, node, func_symtab):
        var_addr = self._find_addr(node.children[0], func_symtab)
        rhs_val = self._codegen(node.children[1], func_symtab)
        if isinstance(var_addr, tuple):
            var = self.builder.load(var_addr[0])
            temp = self.builder.insert_value(var, rhs_val, var_addr[1])
            self.builder.store(temp, var_addr[0])
        else:
            self.builder.store(rhs_val, var_addr)
        return rhs_val


    def _find_addr(self, node, func_symtab):
        if '*' not in node.leaf and node.type != 'array':
            if node.leaf in func_symtab:
                var_addr = func_symtab[node.leaf]
            else:
                var_addr = self.module.get_global(node.leaf)

        elif node.type == 'array':
            elem = self._codegen(node.children[1].children[0], func_symtab)

            if node.children[0].leaf in func_symtab:
                array = func_symtab[node.children[0].leaf]
            elif self.module.get_global(node.children[0].leaf):
                array = self.module.get_global(node.children[0].leaf)
                if '[' in str(array.type) and 'constant' in str(dir(elem)):
                    return (array, int(elem.constant))
                elif '[' in str(array.type):
                    return self.builder.gep(array, [int16(0), elem])
                else:
                    array =  self.builder.load(array)
                    return self.builder.gep(array, [elem])
            else:
                array = self._codegen(node.children[0], func_symtab)

            if 'value' not in str(array.operands) and array.opname != 'load' and array.opname != 'extractvalue':
                array = self.builder.load(array)

            var_addr = self.builder.gep(array, [elem])
        else:
            count = 0
            var = node.leaf
            t_node = node
            while '*' in var:
                count += 1
                t_node = t_node.children[0]
                var = t_node.leaf
            var_addr = self._codegen(t_node, func_symtab)
            for i in range(count-1):
                var_addr = self.builder.gep(var_addr, [int16(0)])
                var_addr = self.builder.load(var_addr)
        return var_addr


    def _codegen_binary_operator_int(self, node, func_symtab):
        if node.leaf == '+' or node.leaf == '-':
            if isinstance(node.children[0].leaf, tuple):
                f = 1
                node.children[0].leaf = node.children[0].leaf[0]
            else:
                f = 0
            lhs = self._codegen(node.children[0], func_symtab)
            kid = node.children
            if kid[1].type == 'binary_operator_int' and (kid[1].leaf == '+' or kid[1].leaf == '-'):
                if kid[1].children[0].type == 'constant' or kid[1].children[0].type == 'variable':
                    temp = self._codegen(kid[1].children[0], func_symtab)
                    if node.leaf == '+':
                        if f == 1:
                            lhs = self.builder.gep(lhs, [temp])
                        else:
                            lhs = self.builder.add(lhs, temp, 'addtmp')
                    else:
                        if f == 1:
                            temp = self.builder.neg(temp)
                            lhs = self.builder.gep(lhs, [temp])
                        else:
                            lhs = self.builder.sub(lhs, temp, 'subtmp')
                    leaf = kid[1].leaf
                    kid = kid[1].children
                    while kid[1].type == 'binary_operator_int' and (leaf == '+' or leaf == '-'):
                        if isinstance(kid[1].leaf, tuple):
                            f = 1
                            kid[1].leaf = kid[1].leaf[0]
                        else:
                            f = 0
                        temp = self._codegen(kid[1].children[0], func_symtab)
                        if leaf == '+':
                            if f == 1:
                                lhs = self.builder.gep(lhs, [temp])
                            else:
                                lhs = self.builder.add(lhs, temp, 'addtmp')
                        else:
                            if f == 1:
                                temp = self.builder.neg(temp)
                                lhs = self.builder.gep(lhs, [temp])
                            else:
                                lhs = self.builder.sub(lhs, temp, 'subtmp')
                        leaf = kid[1].leaf
                        kid = kid[1].children
                    temp = self._codegen(kid[1], func_symtab)
                    if leaf == '+':
                        if f == 1:
                            return self.builder.gep(lhs, [temp])
                        else:
                            return self.builder.add(lhs, temp, 'addtmp')
                    else:
                        if f == 1:
                            temp = self.builder.neg(temp)
                            return self.builder.gep(lhs, [temp])
                        else:
                            return self.builder.sub(lhs, temp, 'subtmp')
            if isinstance(node.children[1].leaf, tuple):
                f = 2
                node.children[1].leaf = node.children[1].leaf[0]
            rhs = self._codegen(node.children[1], func_symtab)
            if node.leaf == '+':
                if f == 1:
                    return self.builder.gep(lhs, [rhs])
                elif f == 2:
                    return self.builder.gep(rhs, [lhs])
                else:
                    return self.builder.add(lhs, rhs, 'addtmp')
            else:
                if f == 1:
                    temp = self.builder.neg(rhs)
                    return self.builder.gep(lhs, [rhs])
                elif f == 2:
                    temp = self.builder.neg(lhs)
                    return self.builder.gep(rhs, [lhs])
                else:
                    return self.builder.sub(lhs, rhs, 'subtmp')
        elif node.leaf == '*' or node.leaf == '/':
            lhs = self._codegen(node.children[0], func_symtab)
            rhs = self._codegen(node.children[1], func_symtab)
            kid = node.children
            if kid[1].type == 'binary_operator_int' and (kid[1].leaf == '*' or kid[1].leaf == '/'):
                if kid[1].children[0].type == 'constant' or kid[1].children[0].type == 'variable':
                    temp = self._codegen(kid[1].children[0], func_symtab)
                    if node.leaf == '*':
                        lhs = self.builder.mul(lhs, temp, 'multmp')
                    else:
                        lhs = self.builder.sdiv(lhs, temp, 'divtmp')
                    leaf = kid[1].leaf
                    kid = kid[1].children
                    while kid[1].type == 'binary_operator_int' and (leaf == '*' or leaf == '/'):
                        temp = self._codegen(kid[1].children[0], func_symtab)
                        if leaf == '*':
                            lhs = self.builder.mul(lhs, temp, 'multmp')
                        else:
                            lhs = self.builder.sdiv(lhs, temp, 'divtmp')
                        leaf = kid[1].leaf
                        kid = kid[1].children
                    temp = self._codegen(kid[1], func_symtab)
                    if leaf == '*':
                        return self.builder.mul(lhs, temp, 'multmp')
                    else:
                        return self.builder.sdiv(lhs, temp, 'divtmp')
            if node.leaf == '*':
                return self.builder.mul(lhs, rhs, 'multmp')
            else:
                return self.builder.sdiv(lhs, rhs, 'divtmp')
        elif node.leaf == '%':
            lhs = self._codegen(node.children[0], func_symtab)
            rhs = self._codegen(node.children[1], func_symtab)
            return self.builder.srem(lhs, rhs, 'modtmp')
        else:
            lhs = self._codegen(node.children[0], func_symtab)
            rhs = self._codegen(node.children[1], func_symtab)
            cmpr = self.builder.icmp_signed(node.leaf, lhs, rhs, 'cmptmp')
            return self.builder.zext(cmpr, boolean, 'booltmp')


    def _codegen_binary_operator_float(self, node, func_symtab):
        lhs = self._codegen(node.children[0], func_symtab)
        rhs = self._codegen(node.children[1], func_symtab)

        if node.leaf == '+' or node.leaf == '-':
            kid = node.children
            if kid[1].type == 'binary_operator_float' and (kid[1].leaf == '+' or kid[1].leaf == '-'):
                if kid[1].children[0].type == 'constant' or kid[1].children[0].type == 'variable':
                    temp = self._codegen(kid[1].children[0], func_symtab)
                    if node.leaf == '+':
                        lhs = self.builder.fadd(lhs, temp, 'addtmp')
                    else:
                        lhs = self.builder.fsub(lhs, temp, 'subtmp')
                    leaf = kid[1].leaf
                    kid = kid[1].children
                    while kid[1].type == 'binary_operator_float' and (leaf == '+' or leaf == '-'):
                        temp = self._codegen(kid[1].children[0], func_symtab)
                        if leaf == '+':
                            lhs = self.builder.fadd(lhs, temp, 'addtmp')
                        else:
                            lhs = self.builder.fsub(lhs, temp, 'subtmp')
                        leaf = kid[1].leaf
                        kid = kid[1].children
                    temp = self._codegen(kid[1], func_symtab)
                    if leaf == '+':
                        return self.builder.fadd(lhs, temp, 'addtmp')
                    else:
                        return self.builder.fsub(lhs, temp, 'subtmp')
            if node.leaf == '+':
                return self.builder.fadd(lhs, rhs, 'addtmp')
            else:
                return self.builder.fsub(lhs, rhs, 'subtmp')
        elif node.leaf == '*' or node.leaf == '/':
            kid = node.children
            if kid[1].type == 'binary_operator_float' and (kid[1].leaf == '*' or kid[1].leaf == '/'):
                if kid[1].children[0].type == 'constant' or kid[1].children[0].type == 'variable':
                    temp = self._codegen(kid[1].children[0], func_symtab)
                    if node.leaf == '*':
                        lhs = self.builder.fmul(lhs, temp, 'multmp')
                    else:
                        lhs = self.builder.fdiv(lhs, temp, 'divtmp')
                    leaf = kid[1].leaf
                    kid = kid[1].children
                    while kid[1].type == 'binary_operator_float' and (leaf == '*' or leaf == '/'):
                        temp = self._codegen(kid[1].children[0], func_symtab)
                        if leaf == '*':
                            lhs = self.builder.fmul(lhs, temp, 'multmp')
                        else:
                            lhs = self.builder.fdiv(lhs, temp, 'divtmp')
                        leaf = kid[1].leaf
                        kid = kid[1].children
                    temp = self._codegen(kid[1], func_symtab)
                    if leaf == '*':
                        return self.builder.fmul(lhs, temp, 'multmp')
                    else:
                        return self.builder.fdiv(lhs, temp, 'divtmp')
            if node.leaf == '*':
                return self.builder.fmul(lhs, rhs, 'multmp')
            else:
                return self.builder.fdiv(lhs, rhs, 'divtmp')
        elif node.leaf == '%':
            return self.builder.frem(lhs, rhs, 'modtmp')
        else:
            cmpr = self.builder.fcmp_unordered(node.leaf, lhs, rhs, 'cmptmp')
            return self.builder.zext(cmpr, boolean, 'booltmp')


    def _codegen_binary_logical_operator(self, node, func_symtab):
        if node.leaf == '&&':
            check1_bb = self.builder.function.append_basic_block('check1')
            check2_bb = ir.Block(self.builder.function, 'check2')
            ret_bb = ir.Block(self.builder.function, 'afterLAND')
            self.builder.branch(check1_bb)
            self.builder.position_at_start(check1_bb)
            lhs = self._codegen(node.children[0], func_symtab)
            check1_bb = self.builder.block
            cmpr = self.builder.trunc(lhs, ir.IntType(1))
            self.builder.cbranch(cmpr, check2_bb, ret_bb)
            self.builder.function.basic_blocks.append(check2_bb)
            self.builder.position_at_start(check2_bb)
            rhs = self._codegen(node.children[1], func_symtab)
            check2_bb = self.builder.block
            out = self.builder.and_(lhs, rhs,'landtmp')
            self.builder.branch(ret_bb)
            self.builder.function.basic_blocks.append(ret_bb)
            self.builder.position_at_start(ret_bb)
            phi = self.builder.phi(boolean)
            phi.add_incoming(lhs, check1_bb)
            phi.add_incoming(out, check2_bb)
            return phi
        elif node.leaf == '||':
            check1_bb = self.builder.function.append_basic_block('check1')
            check2_bb = ir.Block(self.builder.function, 'check2')
            ret_bb = ir.Block(self.builder.function, 'afterLOR')
            self.builder.branch(check1_bb)
            self.builder.position_at_start(check1_bb)
            lhs = self._codegen(node.children[0], func_symtab)
            check1_bb = self.builder.block
            cmpr = self.builder.trunc(lhs, ir.IntType(1))
            self.builder.cbranch(cmpr, ret_bb, check2_bb)
            self.builder.function.basic_blocks.append(check2_bb)
            self.builder.position_at_start(check2_bb)
            rhs = self._codegen(node.children[1], func_symtab)
            check2_bb = self.builder.block
            out = self.builder.or_(lhs, rhs,'landtmp')
            self.builder.branch(ret_bb)
            self.builder.function.basic_blocks.append(ret_bb)
            self.builder.position_at_start(ret_bb)
            phi = self.builder.phi(boolean)
            phi.add_incoming(lhs, check1_bb)
            phi.add_incoming(out, check2_bb)
            return phi
        else:
            lhs = self._codegen(node.children[0], func_symtab)
            rhs = self._codegen(node.children[1], func_symtab)
            return rhs


    def _codegen_array(self, node, func_symtab):
        elem = self._codegen(node.children[1].children[0], func_symtab)

        if node.children[0].leaf in func_symtab:
            array = func_symtab[node.children[0].leaf]
        else:
            array = self._codegen(node.children[0], func_symtab)
        if self.module.get_global(node.children[0].leaf):
            if '[' in str(array.type):
                array = self.module.get_global(node.children[0].leaf)
                array = self.builder.gep(array, [int16(0), elem])
                elem = self.builder.load(array)
            else:
                array = self.builder.gep(array, [elem])
                elem =  self.builder.load(array)
        else:
            if 'value' not in str(array.operands) and array.opname != 'load' and array.opname != 'extractvalue':
                array = self.builder.load(array)
            elem = self.builder.gep(array, [elem])
            elem = self.builder.load(elem)
        return elem


    def _codegen_condop(self, node, func_symtab):
        cond_val = self._codegen(node.children[0], func_symtab)
        cmpr = self.builder.trunc(cond_val, ir.IntType(1))

        then_bb = self.builder.function.append_basic_block('then')
        else_bb = ir.Block(self.builder.function, 'else')
        merge_bb = ir.Block(self.builder.function, 'ifcont')
        self.builder.cbranch(cmpr, then_bb, else_bb)

        self.builder.position_at_start(then_bb)
        then_val = self._codegen(node.children[1], func_symtab)

        self.builder.branch(merge_bb)

        self.builder.function.basic_blocks.append(else_bb)
        self.builder.position_at_start(else_bb)
        else_val = self._codegen(node.children[2], func_symtab)

        self.builder.branch(merge_bb)

        self.builder.function.basic_blocks.append(merge_bb)
        self.builder.position_at_start(merge_bb)
        result = self.builder.phi(then_val.type)
        result.add_incoming(then_val, then_bb)
        result.add_incoming(else_val, else_bb)
        return result

    def _codegen_typecast(self, node, func_symtab):
        rhs = self._codegen(node.children[1], func_symtab)
        typ = node.leaf

        if typ == 'intdouble':
            return self.builder.sitofp(rhs, double, 'intdouble')
        elif typ == 'chardouble':
            return self.builder.sitofp(rhs, double, 'chardouble')
        elif typ == 'charint':
            return self.builder.zext(rhs, int16, 'charint')
        elif typ == 'charbool':
            return self.builder.trunc(rhs, boolean, 'charbool')
        elif typ == 'doubleint':
            return self.builder.fptosi(rhs, int16, 'doubleint')
        elif typ == 'doublebool':
            return self.builder.fptosi(rhs, boolean, 'doublebool')
        elif typ == 'boolint':
            return self.builder.zext(rhs, int16, 'boolint')
        elif typ == 'intbool':
            return self.builder.trunc(rhs, boolean, 'intbool')
        elif typ == 'intchar':
            return self.builder.trunc(rhs, char, 'intchar')
        else:
            return rhs


if __name__ == "__main__":
    ast = parser.our_parser(sys.argv[1])
    gen = LLVMCodeGenerator()
    gen.generate_code(ast)

    file = open(sys.argv[2], 'w')
    file.truncate()
    file.write(str(gen.module))
    file.close()
    exit(0);

exit(1);