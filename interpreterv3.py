from bparser import BParser
from intbase import InterpreterBase, ErrorType
from classesv3 import ClassDefinition, ClassInstance, Value, Type, Variable, TemplateClassDefinition
from copy import copy

#Have an interpreter field that always refers to the latest exception variable, to carry to new function calls

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.classes = {}
        self.templated_classes = {}
        self.types = [InterpreterBase.NULL_DEF, InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF, InterpreterBase.STRING_DEF, InterpreterBase.EXCEPTION_VARIABLE_DEF]
        self.latest_exception_dictionary = {InterpreterBase.EXCEPTION_VARIABLE_DEF : Variable(InterpreterBase.STRING_DEF, InterpreterBase.EXCEPTION_VARIABLE_DEF, Value('""'), self)}

    def __discover_all_classes_and_track_them(self, parsed_program):
        for c in parsed_program:
            if c[0] == InterpreterBase.CLASS_DEF:
                # print(f"Detected class {c[1]}. Adding to dictionary.")
                if c[1] in self.types:
                    self.error(ErrorType.TYPE_ERROR)
                
                if c[2] == InterpreterBase.INHERITS_DEF:
                    parent_class_name = c[3]
                    if parent_class_name not in self.types:
                        self.error(ErrorType.TYPE_ERROR)

                    self.classes[c[1]] = ClassDefinition(c[1], c[2:], self, self.classes[parent_class_name])
                else:
                    self.classes[c[1]] = ClassDefinition(c[1], c[2:], self)
                
                self.types.append(c[1])

            elif c[0] == InterpreterBase.TEMPLATE_CLASS_DEF:
                self.templated_classes[c[1]] = TemplateClassDefinition(c[1], c[2], c[3:], self)

    def create_parameterized_class(self, type):
        if not isinstance(type, str):
            return
            
        deliminated_type = type.split(InterpreterBase.TYPE_CONCAT_CHAR)

        if deliminated_type[0] not in self.templated_classes.keys():
            self.error(ErrorType.TYPE_ERROR)

        self.classes[type] = self.templated_classes[deliminated_type[0]].create_class(deliminated_type[1:])
        self.types.append(type)

    def run(self, program):
        result, parsed_program = BParser.parse(program)

        if not result:
            print("Parsing failed. There must have been a mismatched parenthesis.")

        self.__discover_all_classes_and_track_them(parsed_program)
        self.__check_valid_method_types()

        # for _, c in self.classes.items():
        #     c.print()

        obj = ClassInstance(self, InterpreterBase.MAIN_CLASS_DEF, self.classes[InterpreterBase.MAIN_CLASS_DEF])

        environment_stack = []

        main_object = Value(obj)

        self.call_function(environment_stack, main_object, InterpreterBase.MAIN_FUNC_DEF, [])

    # Before calling this function, must merge fields and other environment variables into a single dictionary. Must add a "me" key mapped to "self".
    def call_function(self, environment_stack, object, method_name, arguments_passed, variable_type=None):
        obj = object.value

        passed_argument_types = []

        for argument_passed in arguments_passed:
            passed_argument_types.append(argument_passed.type)

        fields, method, obj = obj.find_method_from_override_stack(method_name, passed_argument_types)

        if variable_type is not None:
            if isinstance(variable_type, str) and variable_type not in self.classes[method.type].valid_types:
                self.error(ErrorType.TYPE_ERROR)

        environment_stack.append(fields)
        environment_stack.append(self.latest_exception_dictionary)

        return_value = obj.run_method(environment_stack, method, arguments_passed)
        
        environment_stack.pop()
        environment_stack.pop()

        if return_value is not None and return_value.type == Type.NULL:
            return_value = Value('null', null_type=method.type)

        return return_value

    def __check_valid_method_types(self):
        valid_methods = True
        classes = self.classes

        for value in classes.values():
            methods = value.methods
            for method in methods.values():
                return_type = method.type
                parameter_types = copy(method.parameter_types)

                if isinstance(return_type, str) and return_type not in self.types:
                    self.create_parameterized_class(return_type)

                while parameter_types and valid_methods:
                    parameter_type = Type.string_to_type(parameter_types.pop())
                    if isinstance(parameter_type, str) and parameter_type not in self.types:
                        self.create_parameterized_class(parameter_type)

        if not valid_methods:
            self.error(ErrorType.TYPE_ERROR)

    