'''
Bhavik Joshi
UCLA CS 131: Programming Languages
Fall 2023
'''
from intbase import *
from element import *
from brewparse import *
from brewin_types import *
from var_scope import *
import copy


class Interpreter(InterpreterBase):

    NIL = BrewinNil()
    TRUE = BrewinBool(True)
    FALSE = BrewinBool(False)

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
        self.funcs = {}
        # Run program if contains main function
        if ast.elem_type == "program":
            # Find finctions
            if "functions" in ast.dict:
                for func_elem in ast.dict["functions"]:
                    # Add to function mapping dictionary
                    func_tup = (func_elem.dict.get("name", None), len(func_elem.dict.get("args", [])))
                    if func_tup in self.funcs:
                        super().error(ErrorType.NAME_ERROR,
                                "Two functions declared with the same name and argument count. Aborting.",
                        )
                    self.funcs[func_tup] = func_elem
            if ("main", 0) not in self.funcs:
                super().error(ErrorType.NAME_ERROR,
                                "No main() function was found",
                )
            self.__do_function(self.funcs[("main", 0)], [])

    def __do_function(self, func_elem, args_expr):
        # Verify function structure
        if func_elem.elem_type != "func" or "name" not in func_elem.dict or "statements" not in func_elem.dict or "args" not in func_elem.dict:
            print("ERROR: Running __do_function on invalid function element! Aborting.")
        # Trace output
        if self.trace_output:
            print(f'Running function: {func_elem.dict["name"]}.')
        # Function logic
        self.vars.push(is_func = True)
        for arg, arg_expr in zip(func_elem.dict["args"], args_expr):
            self.vars.add_arg(self.__get_arg_name(arg), self.__get_expr(arg_expr))
        for statement in func_elem.dict["statements"]:
            res, returns = self.__do_statement(statement)
            if returns == True:
                break
        self.vars.pop(is_func = True)
        return res

    
    def __do_statement(self, statement_elem):
        # Trace output
        if self.trace_output:
            print(f'Running statement {statement_elem.elem_type}.')

        res, returns = None, False
        # Statement logic (assignment)
        if statement_elem.elem_type == "=":
            # Verify assignment struvture
            if "expression" not in statement_elem.dict or "name" not in statement_elem.dict:
                print("ERROR: Statement element has no expression or name! Aborting.")
            # Trace output
            if self.trace_output:
                print(f'Statement is assignment with name {statement_elem.dict["name"]}.')
            # Assignment logic
            value = self.__get_expr(statement_elem.dict["expression"])
            self.vars.set(statement_elem.dict["name"], value)
            res, returns = None, False

        # Statment logic (fcall)
        elif statement_elem.elem_type == "fcall":
            # Verify fcall structure
            if "args" not in statement_elem.dict or "name" not in statement_elem.dict:
                print("ERROR: Fcall element has no args or name! Aborting.")
            # Trace output
            if self.trace_output:
                print("Statement is fcall.")
            # Fcall logic
            res, returns = self.__do_fcall(statement_elem), False
            
        elif statement_elem.elem_type == "if":
            if "condition" not in statement_elem.dict or "statements" not in statement_elem.dict or \
            "else_statements" not in statement_elem.dict:
                print("ERROR: Statement if element has no condition or statements or else_statements! Aborting.")
            # Trace output
            if self.trace_output:
                print("Statement is if.")
            cond = self.__get_expr(statement_elem.dict["condition"])
            if not isinstance(cond, BrewinBool):
                super().error(ErrorType.TYPE_ERROR,
                    f"Condition expressions must be bool types.",
                )
            # If logic
            self.vars.push()
            statements = []
            if cond.value:
                statements = statement_elem.dict["statements"]
            else:
                if statement_elem.dict["else_statements"] is not None:
                    statements = statement_elem.dict["else_statements"]
            res, returns = None, False
            for statement in statements:
                res, returns = self.__do_statement(statement)
                if returns == True:
                    break
            self.vars.pop()
        
        elif statement_elem.elem_type == "while":
            if "condition" not in statement_elem.dict or "statements" not in statement_elem.dict:
                print("ERROR: Statement while element has no condition or statements Aborting.")
            # Trace output
            if self.trace_output:
                print("Statement is while.")
            cond = self.__get_expr(statement_elem.dict["condition"])
            if not isinstance(cond, BrewinBool):
                super().error(ErrorType.TYPE_ERROR,
                    f"Condition expressions must be bool types.",
                )
            res, returns = None, False
            # While logic
            self.vars.push()
            while cond.value:
                for statement in statement_elem.dict["statements"]:
                    res, returns = self.__do_statement(statement)
                    if returns == True:
                        break
                if returns == True:
                    break
                cond = self.__get_expr(statement_elem.dict["condition"])
                if returns == False and not isinstance(cond, BrewinBool):
                    super().error(ErrorType.TYPE_ERROR,
                        f"Condition expressions must be bool types.",
                )
            self.vars.pop()

        elif statement_elem.elem_type == "return":
            if "expression" not in statement_elem.dict:
                print("ERROR: Statement return element has no expression Aborting.")
            if statement_elem.dict["expression"] is not None:
                res = self.__get_expr(statement_elem.dict["expression"])
            else:
                res = Interpreter.NIL
            returns = True

        else:
            print(f"ERROR: Unknown statement type {statement_elem.elem_type}. Aborting.")
  
        return copy.deepcopy(res), returns

    def __get_expr(self, expr_elem):

        INT_OPS = { "+" : lambda x, y: x + y,
                    "-" : lambda x, y: x - y,
                    "*" : lambda x, y: x * y,
                    "/" : lambda x, y: x // y,
                    "neg" : lambda x, y: x * -1,
                    "==" : lambda x, y: Interpreter.TRUE if (x == y)  else Interpreter.FALSE,
                    "!=" : lambda x, y: Interpreter.TRUE if (x != y)  else Interpreter.FALSE,
                    "<" : lambda x, y:  Interpreter.TRUE if (x < y)   else Interpreter.FALSE,
                    "<=" : lambda x, y: Interpreter.TRUE if (x <= y)  else Interpreter.FALSE,
                    ">" : lambda x, y:  Interpreter.TRUE if (x > y)   else Interpreter.FALSE,
                    ">=": lambda x, y:  Interpreter.TRUE if (x >= y)  else Interpreter.FALSE,
        }
        
        STR_OPS = { "+" : lambda x, y: x + y,
                    "==" : lambda x, y: Interpreter.TRUE if (x == y)  else Interpreter.FALSE,
                    "!=" : lambda x, y: Interpreter.TRUE if (x != y)  else Interpreter.FALSE,
        }
        
        BOOL_OPS = { "||" : lambda x, y: Interpreter.TRUE if (x.value or y.value)  else Interpreter.FALSE,
                     "&&" : lambda x, y: Interpreter.TRUE if (x.value and y.value) else Interpreter.FALSE,
                     "!" : lambda x, y:  Interpreter.TRUE if (not x.value)         else Interpreter.FALSE,
                     "==" : lambda x, y: Interpreter.TRUE if (x.value == y.value)  else Interpreter.FALSE,
                     "!=" : lambda x, y: Interpreter.TRUE if (x.value != y.value)  else Interpreter.FALSE,
        }

        NIL_OPS = {
                    "==" : lambda x, y: Interpreter.TRUE,
                    "!=" : lambda x, y: Interpreter.FALSE,
        }

        OPS = { int: INT_OPS,
                str: STR_OPS,
                BrewinBool: BOOL_OPS,
                BrewinNil: NIL_OPS,
        }

        DIFF_TYPES = { "==" : lambda x, y: Interpreter.FALSE,
                       "!=" : lambda x, y: Interpreter.TRUE,
        }

        VAR = ["var"]
        VALUE = ["int", "string", "bool", "nil"]
        EXPR = ["+", "-", '*', '/','==', '<', '<=', '>', '>=', '!=', 'neg', '!', '||', '&&']
        FCALL = ["fcall"]

        res = None

        # Variable type
        if expr_elem.elem_type in VAR:
            # Verify variable structure
            if "name" not in expr_elem.dict:
                print("ERROR: Variable expression has no name! Aborting.")
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
            # Trace output
            if self.trace_output:
                print(f'Evaluting value w val {expr_elem.dict.get("val", None)}.')
            # Value logic
            if expr_elem.elem_type == "bool":
                res = Interpreter.TRUE if expr_elem.dict["val"] else Interpreter.FALSE
            else:
                res = expr_elem.dict.get("val", Interpreter.NIL)

        # Expr type
        elif expr_elem.elem_type in EXPR:
            # Verify operator structure
            if "op1" not in expr_elem.dict:
                print("ERROR: Expression expression has no op1! Aborting.")
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
                    super().error(ErrorType.TYPE_ERROR,
                       f"Unsupported operation {expr_elem.elem_type} for type {type(op1)}",
                    )
                res = OPS[type(op1)][expr_elem.elem_type](op1, op2)
     
        elif expr_elem.elem_type in FCALL:
            res = self.__do_fcall(expr_elem)

        # Not var, value, expr, or fcall
        else:
            print("ERROR: expression type not VAR, VALUE, or EXPR! Aborting.")

        return copy.deepcopy(res)

    def __do_fcall(self, fcall_elem):
        # Verify fcall structure
        if fcall_elem.elem_type != "fcall" or "name" not in fcall_elem.dict or "args" not in fcall_elem.dict:
            print("ERROR: Running __do_fcall on invalid fcall element! Aborting.")
        # Trace output
        if self.trace_output:
            print(f'Performing function call {fcall_elem.dict["name"]}')

        res = None
        # Fcall logic
        if fcall_elem.dict["name"] == "print":
            to_print = "".join([str(self.__get_expr(arg_elem)) for arg_elem in fcall_elem.dict["args"]])
            super().output(to_print)
            res = Interpreter.NIL

        # Inputi
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
                res = user_input

        #Inputs
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
                res = user_input
        
        # Function node
        elif (fcall_elem.dict["name"], len(fcall_elem.dict["args"])) in self.funcs:
            res = self.__do_function(self.funcs[(fcall_elem.dict["name"], len(fcall_elem.dict["args"]))], fcall_elem.dict["args"])
        
        # Else
        else:
            super().error(ErrorType.NAME_ERROR,
                          f'No matching function {(fcall_elem.dict["name"], len(fcall_elem.dict["args"]))} found.',
            )

        return res

    def __get_arg_name(self, arg_elem):
        if arg_elem.elem_type != "arg" or "name" not in arg_elem.dict:
            print("ERROR: Running __get_arg_name on invalid arg element! Aborting.")
        return arg_elem.dict["name"]