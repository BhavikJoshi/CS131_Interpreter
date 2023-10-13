'''
Bhavik Joshi
UCLA CS 131: Programming Languages
Fall 2023
'''
from intbase import *
from element import *
from brewparse import *

class Interpreter(InterpreterBase):

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
        # Initialize needed variable
        self.trace_output = trace_output
        self.vars = {}
        if self.trace_output:
            print("Interpreter initialized.")

    def run(self, program):
        ast = parse_program(program)
        if not ast:
            pass # ast already checked for None in brewparse.py
        if self.trace_output:
            print("Got AST from parser.")
        # Reset program's variables
        self.vars = {}
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
        for statement in func_elem.dict["statements"]:
            self.__do_statement(statement)
    
    def __do_statement(self, statement_elem):
        # Verify statement structure
        if statement_elem.elem_type not in ["=", "fcall"] or "name" not in statement_elem.dict:
            print("ERROR: Running __do_statement on invalid statement element! Aborting.")
            exit()

        # Trace output
        if self.trace_output:
            print(f'Running statement {statement_elem.elem_type} {statement_elem.dict["name"]}.')

        # Statement logic (assignment)
        if statement_elem.elem_type == "=":
            # Verify assignment struvture
            if "expression" not in statement_elem.dict:
                print("ERROR: Statement element has no expression! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print("Statement is assignment.")
            # Assignment logic
            value = self.__get_expr(statement_elem.dict["expression"])
            self.vars[statement_elem.dict["name"]] = value

        # Statment logic (fcall)
        if statement_elem.elem_type == "fcall":
            # Verify fcall structure
            if "args" not in statement_elem.dict:
                print("ERROR: Statement element has no args! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print("Statement is fcall.")
            # Fcall logic
            self.__do_fcall(statement_elem)
            # TODO: fcall logic

        # UNREACHABLE

    def __get_expr(self, expr_elem):

        OPERATORS = { "+" : lambda x, y: x + y,
                      "-" : lambda x, y: x - y
                    }

        VAR = ["var"]
        VALUE = ["int", "string"]
        EXPR = ["+", "-", "fcall"]

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
            if var_name not in self.vars:
                super().error(ErrorType.NAME_ERROR,
                             f"Variable {var_name} has not been defined"
                )
                return None
            res = self.vars[var_name]

        # Value type
        elif expr_elem.elem_type in VALUE:
            # Verify value structure
            if "val" not in expr_elem.dict:
                print("ERROR: Value expression has no val! Aborting.")
                exit()
            # Trace output
            if self.trace_output:
                print(f'Evaluting value w val {expr_elem.dict["val"]}.')
            # Value logic
            res = expr_elem.dict["val"]  

        # Expr type
        elif expr_elem.elem_type in EXPR:
            # Operator expression
            if expr_elem.elem_type in OPERATORS:
                # Verify operator structure
                if "op1" not in expr_elem.dict or "op2" not in expr_elem.dict:
                    print("ERROR: Expression expression has no op1 or op2! Aborting.")
                    exit()
                
                op1 = self.__get_expr(expr_elem.dict["op1"])
                op2 = self.__get_expr(expr_elem.dict["op2"])
                # Trace output
                if self.trace_output:
                    print(f"Evaluting operator expression {expr_elem.elem_type} {op1} {op2}.")
                # Operator logic
                if not isinstance(op1, int) or not isinstance(op2, int):
                    super().error(ErrorType.TYPE_ERROR,
                                 "Incompatible types for arithmetic operation",
                    )
                    return None
                res =  OPERATORS[expr_elem.elem_type](op1, op2)
            # Fcall expression
            elif expr_elem.elem_type == "fcall":
                res = self.__do_fcall(expr_elem)
                # TODO: check for NULL res
            # Not op or fcall
            else:
                print ("ERROR: Expression expression not operator or fcall! Aborting.")
                exit()

        # Not var, value, or expr
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
            return None
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
        else:
            super().error(ErrorType.NAME_ERROR,
                          f'No matching function {fcall_elem.dict["name"]} found.',
            )
        return None