'''
Bhavik Joshi
UCLA CS 131: Programming Languages
Fall 2023
'''
from intbase import *
from element import *
from brewparse import *
from nil import *
from var_scope import *

class Interpreter(InterpreterBase):

    NIL = Nil()

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Initialize needed variable
        self.trace_output = trace_output
        self.vars = VarScope()
        if self.trace_output:
            print("Interpreter initialized.")

    def run(self, program):
        ast = parse_program(program)
        if not ast:
            pass # ast already checked for None in brewparse.py
        if self.trace_output:
            print("Got AST from parser.")
        # Reset program's variables
        self.vars = VarScope()
        # Run program if contains main function
        if ast.elem_type == "program":
            # Find finctions
            if "functions" in ast.dict:
                for func_elem in ast.dict["functions"]:
                    # Get main function
                    if func_elem.dict.get("name", None) == "main":
                        self.__do_function(func_elem)
                        break
                else:
                    super().error(ErrorType.NAME_ERROR,
                                  "No main() function was found",
                    )

    def __do_function(self, func_elem):
        # Verify function structure
        if func_elem.elem_type != "func" or "name" not in func_elem.dict or  "statements" not in func_elem.dict:
            print("ERROR: Running __do_function on invalid function element! Aborting.")
            exit()
        # Trace output
        if self.trace_output:
            print(f'Running function: {func_elem.dict["name"]}.')
        # Function logic
        self.vars.push()
        # TODO: allow returning from nested statements all the way up to here, make sure VarScope functionality is maintained
        for statement in func_elem.dict["statements"]:
            if statement.elem_type == "return":
                res = self.__do_statement(statement)
                return res
            self.__do_statement(statement)
        self.vars.pop()
    
    def __do_statement(self, statement_elem):
        # Trace output
        if self.trace_output:
            print(f'Running statement {statement_elem.elem_type}.')

        # Statement logic (assignment)
        if statement_elem.elem_type == "=":
            # Verify assignment struvture
            if "expression" not in statement_elem.dict or "name" not in statement_elem.dict:
                print("ERROR: Statement element has no expression or name! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print(f'Statement is assignment with name {statement_elem.dict["name"]}.')
            # Assignment logic
            value = self.__get_expr(statement_elem.dict["expression"])
            self.vars.set(statement_elem.dict["name"], value)

        # Statment logic (fcall)
        elif statement_elem.elem_type == "fcall":
            # Verify fcall structure
            if "args" not in statement_elem.dict or "name" not in statement_elem.dict:
                print("ERROR: Fcall element has no args or name! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print("Statement is fcall.")
            # Fcall logic
            self.__do_fcall(statement_elem)
            
        elif statement_elem.elem_type == "if":
            if "condition" not in statement_elem.dict or "statements" not in statement_elem.dict or \
            "else_statements" not in statement_elem.dict:
                print("ERROR: Statement if element has no condition or statements or else_statements! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print("Statement is if.")
            cond = self.__get_expr(statement_elem.dict["condition"])
            statements = []
            if cond:
                statements = statement_elem.dict["statements"]
            else:
                if statement_elem.dict["else_statements"] is not None:
                    statements = statement_elem.dict["else_statements"]
            for statement in statements:
                if statement.elem_type == "return":
                    res = self.__do_statement(statement)
                    return res
                self.__do_statement(statement)
        
        elif statement_elem.elem_type == "while":
            if "condition" not in statement_elem.dict or "statements" not in statement_elem.dict:
                print("ERROR: Statement while element has no condition or statements Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print("Statement is while.")
            cond = self.__get_expr(statement_elem.dict["condition"])
            while cond:
                for statement in statement_elem.dict["statements"]:
                    if statement.elem_type == "return":
                        res = self.__do_statement(statement)
                        return res
                    self.__do_statement(statement)

        else:
            print(f"ERROR: Unknown statement type {statement_elem.elem_type}. Aborting.")
            exit()
        '''elif statement_elem.elem_type == "return":
            if "expression" not in statement_elem.dict:
                print("ERROR: Statement return element has no expression Aborting.")
                exit()
            if statement_elem.dict["expression"] is not None:
                res = self.__get_expr(statement_elem.dict["expression"])
            else:
                res = Interpreter.NIL
            return res'''
  

        # UNREACHABLE

    def __get_expr(self, expr_elem):

        INT_OPS = { "+" : lambda x, y: x + y,
                    "-" : lambda x, y: x - y,
                    "*" : lambda x, y: x * y,
                    "/" : lambda x, y: x // y,
                    "==" : lambda x, y: x == y,
                    "!=" : lambda x, y: x != y,
                    "<" : lambda x, y: x < y,
                    "<=" : lambda x, y: x <= y,
                    ">" : lambda x, y: x > y,
                    ">=": lambda x, y: x >= y,
                    "neg" : lambda x, y: -x,
                }
        
        STR_OPS = { "+" : lambda x, y: x + y,
                    "==" : lambda x, y: x == y,
                    "!=" : lambda x, y: x != y,
                }
        
        BOOL_OPS = { "||" : lambda x, y: x or y,
                     "&&" : lambda x, y: x and y,
                     "!" : lambda x, y: not x,
                     "==" : lambda x, y: x == y,
                     "!=" : lambda x, y: x != y,
                }

        OPS = { int: INT_OPS,
                str: STR_OPS,
                bool: BOOL_OPS,
            }

        DIFF_TYPES = { "==" : False,
                       "!=" : True,
                    }

        VAR = ["var"]
        VALUE = ["int", "string", "bool", "nil"]
        EXPR = ["+", "-", '*', '/','==', '<', '<=', '>', '>=', '!=', 'neg', '!']
        FCALL = ["fcall"]

        res = None

        # Variable type
        if expr_elem.elem_type in VAR:
            # Verify variable structure
            if "name" not in expr_elem.dict:
                print("ERROR: Variable expression has no name! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print(f'Evaluating variable with name {expr_elem.dict["name"]}.')
            # Variable logic
            var_name = expr_elem.dict["name"]
            res = self.vars.get(var_name, None)
            if res is None:
                super().error(ErrorType.NAME_ERROR,
                             f"Variable {var_name} has not been defined"
                )

        # Value type
        elif expr_elem.elem_type in VALUE:
            # Verify value structure
            if expr_elem.elem_type != "nil" and "val" not in expr_elem.dict:
                print("ERROR: Non-nil value expression has no val! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print(f'Evaluting value w val {expr_elem.dict.get("val", None)}.')
            # Value logic
            res = expr_elem.dict.get("val", Interpreter.NIL)

        # Expr type
        elif expr_elem.elem_type in EXPR:
            # Verify operator structure
            if "op1" not in expr_elem.dict:
                print("ERROR: Expression expression has no op1! Aborting.")
                exit()
            # Get operands
            op1 = self.__get_expr(expr_elem.dict["op1"])
            if "op2" not in expr_elem.dict:
                # Unary operation, no op2 needed
                if expr_elem.elem_type == "neg" or expr_elem.elem_type == "!":
                    # Just set op2 to op1 to maintain same type, but op2 is un-used in lambda functions
                    op2 = op1
                else:
                    super().error(ErrorType.NAME_ERROR,
                        "No op2 named in a binary operation",
                    )
            else:
                op2 = self.__get_expr(expr_elem.dict["op2"])
            # Trace output
            if self.trace_output:
                print(f"Evaluting operator expression {expr_elem.elem_type} {op1} {op2}.")
            # Operator logic
            if type(op1) != type(op2):
                if expr_elem.elem_type not in DIFF_TYPES:
                    super().error(ErrorType.TYPE_ERROR,
                        "Incompatible types for arithmetic operation",
                    )
                res = DIFF_TYPES[expr_elem.elem_type](op1, op2)
            else:
                if type(op1) not in OPS:
                    super().error(ErrorType.TYPE_ERROR,
                       f"No supported operations for type {type(op1)}",
                    )
                if expr_elem.elem_type not in OPS[type(op1)]:
                    super().error(ErrorType.NAME_ERROR,
                       f"Unsupported operation {expr_elem.elem_type} for type {type(op1)}",
                    )
                res = OPS[type(op1)][expr_elem.elem_type](op1, op2)
     
        elif expr_elem.elem_type in FCALL:
            res = self.__do_fcall(expr_elem)

        # Not var, value, expr, or fcall
        else:
            print("ERROR: expression type not VAR, VALUE, or EXPR! Aborting.")
            exit()  

        return res

    def __do_fcall(self, fcall_elem):
        # Verify fcall structure
        if fcall_elem.elem_type != "fcall" or "name" not in fcall_elem.dict or "args" not in fcall_elem.dict:
            print("ERROR: Running __do_fcall on invalid fcall element! Aborting.")
            exit()
        # Trace output
        if self.trace_output:
            print(f'Performing function call {fcall_elem.dict["name"]}')
        # Fcall logic
        if fcall_elem.dict["name"] == "print":
            to_print = "".join([str(self.__get_expr(arg_elem)) for arg_elem in fcall_elem.dict["args"]])
            super().output(to_print)
            return Interpreter.NIL
        elif fcall_elem.dict["name"] == "inputi":
            args = fcall_elem.dict["args"]
            if len(args) > 1:
                super().error(ErrorType.NAME_ERROR,
                              f"No inputi() function found that takes > 1 parameter",
                )
            else:
                if args:
                    prompt = str(self.__get_expr(args[0]))
                    super().output(prompt)
                user_input = int(super().get_input())
                return user_input
        elif fcall_elem.dict["name"] == "inputs":
            args = fcall_elem.dict["args"]
            if len(args) > 1:
                super().error(ErrorType.NAME_ERROR,
                              f"No inputs() function found that takes > 1 parameter",
                )
            else:
                if args:
                    prompt = str(self.__get_expr(args[0]))
                    super().output(prompt)
                user_input = str(super().get_input())
                return user_input
        else:
            super().error(ErrorType.NAME_ERROR,
                          f'No matching function {fcall_elem.dict["name"]} found.',
            )
        return None