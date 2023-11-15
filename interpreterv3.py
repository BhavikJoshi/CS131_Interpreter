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
        self.vars = VarScope(self.trace_output)
        if self.trace_output:
            print("Interpreter initialized.")

    def run(self, program):
        ast = parse_program(program)
        if not ast:
            pass # ast already checked for None in brewparse.py
        if self.trace_output:
            print("Got AST from parser.")
        # Reset program's variables
        self.vars = VarScope(self.trace_output)
        self.vars.push()
        # Run program if contains main function
        if ast.elem_type == "program":
            # Find finctions
            if "functions" in ast.dict:
                for func_elem in ast.dict["functions"]:
                    # Add to function mapping dictionary
                    func_name = func_elem.dict.get("name", None)
                    func_num_args = len(func_elem.dict.get("args", []))
                    # If a function with the name already exists
                    if self.vars.get(func_name) is not None:
                        # If a function with the num params already exists
                        if self.vars.get(func_name).get(func_num_args) is not None:
                            super().error(ErrorType.NAME_ERROR,
                                    "Two functions declared with the same name and argument count. Aborting.",
                            )
                        else:
                            # Add function
                            self.vars.get(func_name).set(func_num_args, func_elem, closure = None)
                    else:
                        # Add function
                        self.vars.set(func_name, BrewinFunction(init_term=(func_num_args, func_elem, None)))
            # Find main with 0 arguments
            if self.vars.get("main") is None or self.vars.get("main").get(0) is None:
                super().error(ErrorType.NAME_ERROR,
                                "No main() function was found",
                )
            main_func, closure = self.vars.get("main").get(0)
            self.__do_function(main_func, [], closure)

    def __do_function(self, func_elem, args_expr, closure = None):
        # Verify function structure
        if (func_elem.elem_type != "func" and func_elem.elem_type != "lambda") or "statements" not in func_elem.dict or "args" not in func_elem.dict:
            print("ERROR: Running __do_function on invalid function element! Aborting.")
        # Trace output
        if self.trace_output:
            if func_elem.elem_type == "func":
                print(f'Running function: {func_elem.dict["name"]}.')
            elif func_elem.elem_type == "lambda":
                print(f'Running lambda function.')
        # Function logic
        self.vars.push(is_func = True, closure = closure)
        # Add all refargs
        for arg, arg_expr in zip(func_elem.dict["args"], args_expr):
            if arg.elem_type == "refarg":
                self.__add_refarg(self.vars, arg, arg_expr, closure)
        # Add all args
        for arg, arg_expr in zip(func_elem.dict["args"], args_expr):
            if arg.elem_type == "arg":
                self.__add_arg(self.vars, arg, arg_expr)
        for statement in func_elem.dict["statements"]:
            res, returns = self.__do_statement(statement)
            if returns == True:
                break
        self.vars.pop(is_func = True, closure = closure)
        return res

    
    def __do_statement(self, statement_elem):
        # Trace output
        if self.trace_output:
            print(f'Running statement {statement_elem.elem_type}.')

        res, returns = None, False
        # Statement logic (assignment)
        # TODO: split __do_statement() into =, fcall, if, while, return
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
            cond = self.__coerce_to_bool(self.__get_expr(statement_elem.dict["condition"]))
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
            cond = self.__coerce_to_bool(self.__get_expr(statement_elem.dict["condition"]))
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
                cond = self.__coerce_to_bool(self.__get_expr(statement_elem.dict["condition"]))
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
                    "!" : lambda x, y:  Interpreter.TRUE if (not self.__coerce_to_bool(x).value)  else Interpreter.FALSE,
                    "==" : lambda x, y: Interpreter.TRUE if (x == y)  else Interpreter.FALSE,
                    "!=" : lambda x, y: Interpreter.TRUE if (x != y)  else Interpreter.FALSE,
                    "<" : lambda x, y:  Interpreter.TRUE if (x < y)   else Interpreter.FALSE,
                    "<=" : lambda x, y: Interpreter.TRUE if (x <= y)  else Interpreter.FALSE,
                    ">" : lambda x, y:  Interpreter.TRUE if (x > y)   else Interpreter.FALSE,
                    ">=": lambda x, y:  Interpreter.TRUE if (x >= y)  else Interpreter.FALSE,
                    "||" : lambda x, y: Interpreter.TRUE if (self.__coerce_to_bool(x).value or self.__coerce_to_bool(y).value) else Interpreter.FALSE,
                    "&&" : lambda x, y: Interpreter.TRUE if (self.__coerce_to_bool(x).value and self.__coerce_to_bool(y).value) else Interpreter.FALSE,
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
                     "+" : lambda x, y:  self.__coerce_to_int(x) + self.__coerce_to_int(y),
                     "-" : lambda x, y:  self.__coerce_to_int(x) - self.__coerce_to_int(y),
                     "*" : lambda x, y:  self.__coerce_to_int(x) * self.__coerce_to_int(y),
                     "/" : lambda x, y:  self.__coerce_to_int(x) / self.__coerce_to_int(y),
        }

        NIL_OPS = {
                    "==" : lambda x, y: Interpreter.TRUE,
                    "!=" : lambda x, y: Interpreter.FALSE,
        }

        INT_BOOL_COERCION_OPS = {
                    "||"  : lambda ix, by: Interpreter.TRUE if (self.__coerce_to_bool(ix).value or by.value) else Interpreter.FALSE,
                    "&&" : lambda  ix, by: Interpreter.TRUE if (self.__coerce_to_bool(ix).value and by.value) else Interpreter.FALSE,
                    "==" : lambda  ix, by: Interpreter.TRUE if (self.__coerce_to_bool(ix).value == by.value)  else Interpreter.FALSE,
                    "!=" : lambda  ix, by: Interpreter.TRUE if (self.__coerce_to_bool(ix).value != by.value)  else Interpreter.FALSE,
                    "+" :  lambda  ix, by: ix + self.__coerce_to_int(by),
                    "-" :  lambda  ix, by: ix - self.__coerce_to_int(by),
                    "*" :  lambda  ix, by: ix * self.__coerce_to_int(by),
                    "/" :  lambda  ix, by: ix // self.__coerce_to_int(by),
        }

        BOOL_INT_COERCION_OPS = {
                    "||" : lambda bx, iy: Interpreter.TRUE if (bx.value or self.__coerce_to_bool(iy).value) else Interpreter.FALSE,
                    "&&" : lambda bx, iy: Interpreter.TRUE if (bx.value and self.__coerce_to_bool(iy).value) else Interpreter.FALSE,
                    "==" : lambda bx, iy: Interpreter.TRUE if (bx.value == self.__coerce_to_bool(iy).value)  else Interpreter.FALSE,
                    "!=" : lambda bx, iy: Interpreter.TRUE if (bx.value != self.__coerce_to_bool(iy).value)  else Interpreter.FALSE,
                    "+"  :  lambda bx, iy: self.__coerce_to_int(bx) + iy,
                    "-"  :  lambda bx, iy: self.__coerce_to_int(bx) - iy,
                    "*"  :  lambda bx, iy: self.__coerce_to_int(bx) * iy,
                    "/"  :  lambda bx, iy: self.__coerce_to_int(bx) / iy,
        }

        FUNCTION_OPS = {
                    '==': lambda x, y: Interpreter.TRUE if (x is y)     else Interpreter.FALSE,
                    '!=': lambda x, y: Interpreter.TRUE if (x is not y) else Interpreter.FALSE,
        }

        OPS = { (int, int): INT_OPS,
                (str, str): STR_OPS,
                (BrewinBool, BrewinBool): BOOL_OPS,
                (BrewinNil, BrewinNil): NIL_OPS,
                (int, BrewinBool): INT_BOOL_COERCION_OPS,
                (BrewinBool, int): BOOL_INT_COERCION_OPS,
                (BrewinFunction, BrewinFunction): FUNCTION_OPS,
        }

        DIFF_TYPES = { "==" : lambda x, y: Interpreter.FALSE,
                       "!=" : lambda x, y: Interpreter.TRUE,
        }

        VAR = ["var"]
        VALUE = ["int", "string", "bool", "nil", "lambda"]
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
            if isinstance(res, BrewinFunction) and res.is_overloaded():
                super().error(ErrorType.NAME_ERROR,
                             f"Ambiguous reference to overloaded function"
                )

        # Value type
        elif expr_elem.elem_type in VALUE:
            # Verify value structure
            if (expr_elem.elem_type != "nil" and expr_elem.elem_type != "lambda") and "val" not in expr_elem.dict:
                print("ERROR: Non-nil and non-lambda value expression has no val")
            # Trace output
            if self.trace_output:
                print(f'Evaluting {expr_elem.elem_type} value w val {expr_elem.dict.get("val", None)}.')
            # Value logic
            if expr_elem.elem_type == "bool":
                res = Interpreter.TRUE if expr_elem.dict["val"] else Interpreter.FALSE
            elif expr_elem.elem_type == "lambda":
                if "args" not in expr_elem.dict or "statements" not in expr_elem.dict:
                    print(f"Error: Lambda function declaration node has no args or statements!")
                num_args = len(expr_elem.dict["args"])
                res = BrewinFunction(init_term = (num_args, expr_elem, copy.deepcopy(self.vars)))
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
            if expr_elem.elem_type not in OPS.get((type(op1), type(op2)), DIFF_TYPES):
                super().error(ErrorType.TYPE_ERROR,
                    f"Unsupported operation {expr_elem.elem_type} for typs {type(op1)} {type(op2)}",
                )
            res = OPS.get((type(op1), type(op2)), DIFF_TYPES)[expr_elem.elem_type](op1, op2)
     
        elif expr_elem.elem_type in FCALL:
            res = self.__do_fcall(expr_elem)

        # Not var, value, expr, or fcall
        else:
            print("ERROR: expression type not VAR, VALUE, or EXPR! Aborting.")

        return res

    def __do_fcall(self, fcall_elem):
        # Verify fcall structure
        if fcall_elem.elem_type != "fcall" or "name" not in fcall_elem.dict or "args" not in fcall_elem.dict:
            print("ERROR: Running __do_fcall on invalid fcall element! Aborting.")
        # Trace output
        if self.trace_output:
            print(f'Performing function call {fcall_elem.dict["name"]}')

        res = None
        # Fcall logic
        # print
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
        elif self.vars.get(fcall_elem.dict["name"]) is not None:
            if not isinstance(self.vars.get(fcall_elem.dict["name"]), BrewinFunction):
                super().error(ErrorType.TYPE_ERROR,
                    f'Cannot treat non function variable as a function.',
                )
            elif self.vars.get(fcall_elem.dict["name"]).get(len(fcall_elem.dict["args"])) is not None:
                func_to_call, closure = self.vars.get(fcall_elem.dict["name"]).get(len(fcall_elem.dict["args"]))
                res = self.__do_function(func_to_call, fcall_elem.dict["args"], closure)
            else:
                super().error(ErrorType.TYPE_ERROR,
                    f'Function {fcall_elem.dict["name"]} exists, but not with  {len(fcall_elem.dict["args"])} arguments.',
                )
        
        # Else
        else:
            super().error(ErrorType.NAME_ERROR,
                f'No matching function {(fcall_elem.dict["name"], len(fcall_elem.dict["args"]))} found.',
            )

        return res

    def __add_arg(self, vars, arg_elem, expr_elem):
        if arg_elem.elem_type != "arg" or "name" not in arg_elem.dict:
            print(f"ERROR: Running __add_arg on invalid arg element {arg_elem.elem_type}")
        # Evaluate the expression and set to arg
        vars.add_arg(arg_elem.dict["name"], copy.deepcopy(self.__get_expr(expr_elem)))

    def __add_refarg(self, vars, arg_elem, expr_elem, closure):
        if arg_elem.elem_type != "refarg" or "name" not in arg_elem.dict:
            print(f"ERROR: Running __add_refarg on invalid refarg element {arg_elem.elem_type}")
        # If the refarg expr is not a VAR, just evaluate and add as a normal argument
        if expr_elem.elem_type != "var":
            vars.add_arg(arg_elem.dict["name"], self.__get_expr(expr_elem))
        # Otherwise, create an alias for the refarg
        else:
            prev_name = expr_elem.dict["name"]
            res = self.vars.get(prev_name, None)
            if res is None:
                super().error(ErrorType.NAME_ERROR,
                            f"Variable {prev_name} has not been defined"
                )
            vars.add_alias(arg_elem.dict["name"], expr_elem.dict["name"], closure)


    def __coerce_to_bool(self, val):
        if isinstance(val, BrewinBool):
            return val
        if isinstance(val, int):
            return Interpreter.TRUE if val != 0 else Interpreter.FALSE
        else:
            super().error(ErrorType.TYPE_ERROR,
                f"Condition expressions must be bool or coerced int to bool types, got {type(val)}" ,
            )

    def __coerce_to_int(self, val):
        if isinstance(val, int):
           return val
        if isinstance(val, BrewinBool):
            return 1 if val.value else 0
        else:
            super().error(ErrorType.TYPE_ERROR,
                f"Condition expressions must be int or coerced bool to int types, got {type(val)}" ,
            )