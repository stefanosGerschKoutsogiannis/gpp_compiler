#Stefanos Gersch-Koutsogiannis 5046
#Filippos Alexiou 5146

# IMPORTANT, PLEASE READ ME, IT ONLY TAKES ONE MINUTE
# note: sometimes read(char) works unexpectedly when moving file descriptor pointer back
# to avoid it, add spaces between all characters(safe option)

"""
NOTES:   

1. final code is not used, did not create everything needed for the creation of it
2. when printing and writing symbol table, starting quad is not filled, but in debugging
3. Function calling with functions as inputs does not work properly
4. No semantic analysis
5. beware of the important note above, file pointer goes wild when there are not spaces 

"""

import string
import sys
import os
from typing import List, Tuple
from pathlib import Path
import shutil
from abc import ABC

RESERVED_KEYWORDS = [
    "πρόγραμμα", "δήλωση", "εάν", "τότε", "αλλιώς",
    "εάν_τέλος", "επανάλαβε", "μέχρι", "όσο", "όσο_τέλος",
    "για", "έως", "με_βήμα", "για_τέλος", "διάβασε", "γράψε",
    "συνάρτηση", "διαδικασία", "διαπροσωπεία", "είσοδος", "έξοδος",
    "αρχή_συνάρτησης", "αρχή_διαδικασίας", "αρχή_προγράμματος",
    "τέλος_συνάρτησης", "τέλος_διαδικασίας", "τέλος_προγράμματος",
    "ή", "και", "εκτέλεσε"
]

ADD_OPERATORS = ["+", "-"]
MUL_OPERATORS = ["*", "/"]
LOGICAL_OPERATORS = ["και", "ή"]

ENGLISH_LETTERS = list(string.ascii_letters)
GREEK_LETTERS = [chr(code) for code in range(0x03B1, 0x03C9 + 1)] + [chr(code) for code in range(0x0391, 0x03A9 + 1)]
DIGITS = list(string.digits)
GREEK_PUNCTUATIONS = ['ά', 'ό', 'ί', 'έ', 'ή', 'ύ', 'ώ']
GROUP_SYMBOLS = ["(", ")", "[", "]"]
RELATIONAL_SYMBOLS = ["=", "<", ">", "<>", "<=", ">="]

LETTERS = ENGLISH_LETTERS+GREEK_LETTERS+GREEK_PUNCTUATIONS

DELIMETERS = [",",";", ":"]
BY_REFERENCE_OPERATOR = "%"

TEMP_COUNTER = 0

SYMBOL_TABLE_START = 12 # in bytes
NESTING_LEVEL = -1    # at start, incr to zero

class Token:

    def __init__(self, recognized_string: str, family: str, line_number: int) -> None:
        self.recognized_string = recognized_string
        self.family = family
        self.line_number = line_number
    
    def __str__(self) -> str:
        return f"Recognized token: {self.recognized_string} , Family: {self.family} , Line: {self.line_number}"

class Lex:

    def __init__(self, file_name:string) -> None:
        self.current_line = 1
        self.file_name = file_name
        self.token = None

        self.file = open(self.file_name, 'r', encoding="utf-8")

    def next_token(self)  -> Token:
        recognized_token: str = ""
        character: chr = self.__read_character()

        while character == "\n":
            self.current_line += 1
            character = self.__read_character()
        
        while character.isspace():
            character = self.__read_character()

        recognized_token += character

        if recognized_token in LETTERS:
            character = self.__read_character()

            while character in LETTERS or character in DIGITS or character == "_":
                recognized_token += character
                if len(recognized_token) > 30:
                    self.__error("InvalidLengthError", f"Identifier {recognized_token} exceeds maximum supported length of 30 characters")
                character = self.__read_character()

            if character not in LETTERS and character not in DIGITS and character != "_":
                self.__move_fp_back()

            if recognized_token in RESERVED_KEYWORDS:
                self.token = self.__create_token(recognized_token, "keyword")
            else:
                self.token = self.__create_token(recognized_token, "identifier")

            return self.token

        elif recognized_token in DIGITS:
            character = self.__read_character()
            while character in DIGITS:
                recognized_token += character
                # add bound
                if int(recognized_token) > 32767 or int(recognized_token) < -32767:
                    self.__error("NumberOutOfRangeError", f"{recognized_token} exceeds maximum number supported")
                character = self.__read_character()
                if character in LETTERS:
                    self.__error("InvalidNumberError", f"{recognized_token} is not a valid number")
            self.__move_fp_back()
            self.token = self.__create_token(recognized_token, "digit")
            return self.token
            
        elif recognized_token in ADD_OPERATORS:
            self.token = self.__create_token(recognized_token, "addOper")
            return self.token

            
        elif recognized_token in MUL_OPERATORS:
            self.token = self.__create_token(recognized_token, "mulOper")
            return self.token

        elif recognized_token == ":":
            character = self.__read_character()
            if character == "=":
                recognized_token += character
                self.token = self.__create_token(recognized_token, "assignment")
                return self.token
            else:
                self.__error("InvalidTokenError", f"Token {recognized_token} is not used properly")

        elif recognized_token in RELATIONAL_SYMBOLS:
            character = self.__read_character()
            if recognized_token == "<":
                if character == "=":
                    self.token = self.__create_token(recognized_token+character, "relOper")
                elif character == ">":
                    self.token = self.__create_token(recognized_token+character, "relOper")
                else:
                    self.__move_fp_back()
                    self.token = self.__create_token(recognized_token, "relOper")
            else:
                if character == "=":
                    self.token = self.__create_token(recognized_token+character, "relOper")
                else:
                    self.__move_fp_back()
                    self.token = self.__create_token(recognized_token, "relOper")
            return self.token
        
        elif recognized_token in GROUP_SYMBOLS:
            self.token = self.__create_token(recognized_token, "groupSymbol")
            return self.token
        
        elif recognized_token == "{":
            character = self.__read_character()
            while character != "}":
                character = self.__read_character()
                if not character:   #eof
                    self.__error("UnclosedCommentsError", f"Comment block is not closed")
                elif character == "\n":
                    self.current_line += 1
            self.token = self.next_token()
            return self.token

        elif recognized_token in DELIMETERS:
            self.token = self.__create_token(recognized_token, "delimeter")
            return self.token
        
        elif recognized_token == BY_REFERENCE_OPERATOR:
            self.token = self.__create_token(recognized_token, "byRefOp")
            return self.token
        
        elif recognized_token == '':
            return ''

        else:
            self.__error("InvalidCharacterError", f"Character {recognized_token} is not supported")
    
    def __read_character(self) -> chr:
        return self.file.read(1)

    def __create_token(self, recognized_token: str, family: str) -> Token:
        return Token(recognized_token, family, self.current_line)
    
    def __move_fp_back(self) -> None:
        self.file.seek(self.file.tell() - 1)

    def __error(self, error_type, msg):
        print(f"{error_type} ({self.current_line}): {msg}")
        exit(-1)

class Parser:

    def __init__(self, lex: Lex) -> None:
        self.lex: Lex = lex
        self.__set_up_log()
        self.__set_up_asm_file()
        self.tokens = open("log/tokens.txt", "a")
        self.quads = open("log/quadlist.int", "a")
        self.table = open("log/table.sym", "a")
        self.final = open("final.asm", "a")
        self.quad_ops: QuadList = QuadList()
        self.generated_program = self.quad_ops.program_list

        self.symbol_table: Table = Table()

    def syntax_analyzer(self) -> None:
        global token
        token = self.get_token()
        self.program()

    def program(self) -> None:
        global token
        if token.recognized_string == "πρόγραμμα":

            # create scope for program
            self.symbol_table.add_scope()
        
            token = self.get_token()
            if token.family == "identifier":
                program_name = token.recognized_string
                token = self.get_token()
                self.programblock(program_name)

                # delete scope for program
                self.__write_to_sym_file()
                self.symbol_table.delete_scope()

                self.__success_exit()
            else:
                self.__error("SyntaxError", "Expected an identifier after 'πρόγραμμα' keyword, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", "Program should start with 'πρόγραμμα' keyword, instead got {token.recognized_string}")


    def programblock(self, program_name) -> None:
        global token
        self.declarations()
        self.subprograms()
        if token.recognized_string == "αρχή_προγράμματος":

            self.quad_ops.gen_quad("begin_block", program_name, "_", "_")

            token = self.get_token()
            self.sequence()
            if token.recognized_string == "τέλος_προγράμματος":
                self.quad_ops.gen_quad("halt", "_", "_", "_")
                self.quad_ops.gen_quad("end_block", program_name, "_", "_")
            else:
                self.__error("SyntaxError", f"The program block is not closed, expected 'τέλος_προγράμματος', got {token}")
        else:
            self.__error("SyntaxError", f"No program block in the source file {self.lex.file}")


    def declarations(self) -> None:
        global token
        while token.recognized_string == "δήλωση":
            token = self.get_token()
            self.varlist("declarations", "_")

    def varlist(self, caller: str, function_name: str) -> None:
        global token
        if token.family == "identifier":
            id_name = token.recognized_string
            self.__manage_varlist(caller, id_name, function_name)
            token = self.get_token()

            # repeat yourself in here, refactor
            while token.recognized_string == ",":
                token = self.get_token()
                if token.family == "identifier":
                    id_name = token.recognized_string
                    token = self.get_token()
                    self.__manage_varlist(caller, id_name, function_name)
                else:
                    self.__error("SyntaxError", f"Expected an identifier, instead got {token.recognized_string}")
            
    def subprograms(self) -> None:
        global token
        while token.recognized_string in ["συνάρτηση", "διαδικασία"]:
            if token.recognized_string == "συνάρτηση":
                token = self.get_token()

                self.func()
            elif token.recognized_string == "διαδικασία":
                token = self.get_token()

                self.proc()
            else:
                self.__error("SyntaxError", f"No subprograms declared in program")

    def func(self) -> None:
        global token
        if token.family == "identifier":
            function_name = token.recognized_string
            self.symbol_table.add_entity(Function(function_name, "_", "int", "_"))
            self.symbol_table.add_scope()

            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()
                self.formalparlist(function_name)
                if token.recognized_string == ")":
                    token = self.get_token()
                    
                    self.funcblock(function_name)

                    # remove from symbol table, compilation of this function is done
                    self.__write_to_sym_file()
                    self.symbol_table.delete_scope()
                else:
                    self.__error("SyntaxError", f"Function parameter list is not closed, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Function parameter list is missing, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Function should be named after an identifier, instead got {token.recognized_string}")

    def proc(self) -> None:
        global token
        if token.family == "identifier":
            procedure_name = token.recognized_string
            self.symbol_table.add_entity(Procedure(procedure_name, "_", "_"))
            self.symbol_table.add_scope()
            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()

                # keep them and then in funcblock compare if they match
                self.formalparlist(procedure_name)
                if token.recognized_string == ")":
                    token = self.get_token()
                    self.procblock(procedure_name)

                    # remove the scope when procedure ends
                    self.__write_to_sym_file()
                    self.symbol_table.delete_scope()
                else:
                    self.__error("SyntaxError", f"Procedure parameter list is not closed, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Procedure parameter list is missing, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Procedure should be named after an identifier, instead got {token.recognized_string}")

    def formalparlist(self, name: str) -> None:
        global token
        if token.family == "identifier":
            self.varlist("formalparlist", name)   

    def funcblock(self, function_name: str) -> None:
        global token

        if token.recognized_string == "διαπροσωπεία":
            token = self.get_token()
            self.funcinput(function_name)
            self.funcoutput(function_name)
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_συνάρτησης":

                self.quad_ops.gen_quad("begin_block", function_name, "_", "_")
                starting_quad = self.quad_ops.next_quad()   # first executable command

                token = self.get_token()
                self.sequence()
                if token.recognized_string == "τέλος_συνάρτησης":
                    self.quad_ops.gen_quad("end_block", function_name, "_", "_")
                    token = self.get_token()

                    framelength = self.symbol_table.scope_list[-1].offset

                    function, _ = self.symbol_table.search_entity(function_name)
                    function.starting_quad = starting_quad
                    function.frame_length = framelength

                else:
                    self.__error("SyntaxError", f"Unclosed function block, expected 'τέλος_συνάρτησης' keyword, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Missing function block declaration, expected 'αρχή_συνάρτησης', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Function block's 'διαπροσωπεία' is missing, instead got {token.recognized_string}")

    def procblock(self, procedure_name) -> None:
        global token

        if token.recognized_string == "διαπροσωπεία":
            token = self.get_token()
            self.funcinput(procedure_name)

            # should it even be here
            self.funcoutput(procedure_name)
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_διαδικασίας":

                self.quad_ops.gen_quad("begin_block", procedure_name, "_", "_")
                starting_quad = self.quad_ops.next_quad()   # first executable command

                token = self.get_token()
                self.sequence()
                if token.recognized_string == "τέλος_διαδικασίας":

                    self.quad_ops.gen_quad("end_block", procedure_name, "_", "_")

                    framelength = self.symbol_table.scope_list[-1].offset

                    procedure, _ = self.symbol_table.search_entity(procedure_name)
                    procedure.starting_quad = starting_quad
                    procedure.frame_length = framelength

                    token = self.get_token()
                else:
                    self.__error("SyntaxError", f"Unclosed procedure block, expected 'τέλος_διαδικασίας', instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Missing procedure block declaration, expected 'αρχή_διαδικασίας', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Procedure block's 'διαπροσωπεία' is missing, instead got {token.recognized_string}")

    def funcinput(self, function_name: str) -> None:
        global token
        if token.recognized_string == "είσοδος":
            token = self.get_token()
            self.varlist("funcinput", function_name)

    def funcoutput(self, function_name: str) -> None:
        global token
        if token.recognized_string == "έξοδος":
            token = self.get_token()
            self.varlist("funcoutput", function_name)  

    def sequence(self) -> None:
        global token
        self.statement()
        while token.recognized_string == ";":
            token = self.get_token()
            self.statement()

    def statement(self) -> None:
        global token
        if token.family == "identifier":
            id_name = token.recognized_string
            token = self.get_token()
            self.assignment_stat(id_name)
        elif token.recognized_string == "εάν":
            token = self.get_token()
            self.if_stat()
        elif token.recognized_string == "όσο":
            token = self.get_token()
            self.while_stat()
        elif token.recognized_string == "επανάλαβε":
            token = self.get_token()
            self.do_stat()
        elif token.recognized_string == "για":
            token = self.get_token()
            self.for_stat()
        elif token.recognized_string == "διάβασε":
            token = self.get_token()
            self.input_stat()
        elif token.recognized_string == "γράψε":
            token = self.get_token()
            self.print_stat()
        elif token.recognized_string == "εκτέλεσε":
            token = self.get_token()
            self.call_stat()
        else:
            self.__error("SyntaxError", "Invalid statement")


    def assignment_stat(self, id_name) -> None:
        global token
        if token.recognized_string == ":=":
            token = self.get_token()
            expression_place = self.expression()

            self.quad_ops.gen_quad(":=", expression_place, "_", id_name)
        else:
            self.__error("SyntaxError", f"Expected ':=', instead got {token.recognized_string}")

    def if_stat(self) -> None:
        global token
        condition_true, condition_false = self.condition()
        if token.recognized_string == "τότε":

            self.quad_ops.back_patch(condition_true, self.quad_ops.next_quad())

            token = self.get_token()
            self.sequence()

            if_list = self.quad_ops.make_list(self.quad_ops.next_quad())
            self.quad_ops.gen_quad("jump", "_", "_", "_")
            self.quad_ops.back_patch(condition_false, self.quad_ops.next_quad())

            self.else_part()

            self.quad_ops.back_patch(if_list, self.quad_ops.next_quad())

            if token.recognized_string == "εάν_τέλος":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed 'εάν' statement, expected 'εάν_τέλος', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Expected 'τότε', instead got {token.recognized_string}")


    def while_stat(self) -> None:
        global token

        cond_quad = self.quad_ops.next_quad()
        condition_true, condition_false =  self.condition()

        if token.recognized_string == "επανάλαβε":

            self.quad_ops.back_patch(condition_true, self.quad_ops.next_quad())

            token = self.get_token()
            self.sequence()

            self.quad_ops.gen_quad("jump", "_", "_", cond_quad)
            self.quad_ops.back_patch(condition_false, self.quad_ops.next_quad())

            if token.recognized_string == "όσο_τέλος":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed 'όσο' statement, expected 'όσο_τέλος', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Expected 'όσο', instead got {token.recognized_string}")

    def do_stat(self) -> None:
        global token

        sequence_quad = self.quad_ops.next_quad()

        self.sequence()
        if token.recognized_string == "μέχρι":
            token = self.get_token()
            condition_true, condition_false = self.condition()

            self.quad_ops.back_patch(condition_false, sequence_quad)
            self.quad_ops.back_patch(condition_true, self.quad_ops.next_quad())

        else:
            self.__error("SyntaxError", f"Expeted 'μέχρι', instead got {token.recognized_string}")

    def for_stat(self) -> None:
        global token
        if token.family == "identifier":

            start_variable = token.recognized_string

            token = self.get_token()
            if token.recognized_string == ":=":
                token = self.get_token()

                start_value = self.expression()   # the starting value for the for loop
                self.quad_ops.gen_quad(":=", start_value, "_", start_variable)

                if token.recognized_string == "έως":
                    token = self.get_token()

                    end_value = self.expression() # the ending value for the for loop
                    end_temp_variable = self.quad_ops.new_temp()
                    self.quad_ops.gen_quad(":=", end_value, "_", end_temp_variable)

                    step_value = self.step()  # step returns step if "with step" exists else returns zero (strings)
                    step_temp_variable = self.quad_ops.new_temp()
                    self.quad_ops.gen_quad(":=", step_value, "_", step_temp_variable)

                    if token.recognized_string == "επανάλαβε":
                        token = self.get_token()

                        # to determine jump condition
                        if int(step_value) >= 0:
                            jump_operation = ">="
                        else:
                            jump_operation = "<="

                        check_quad = self.quad_ops.next_quad()
                        fill_out = self.quad_ops.make_list(check_quad)
                        self.quad_ops.gen_quad(jump_operation, start_variable, end_temp_variable, "_")
                    
                        self.sequence()
                        
                        # perform addition and go to check
                        self.quad_ops.gen_quad("+", start_variable, step_temp_variable, start_variable)
                        self.quad_ops.gen_quad("jump", "_", "_", check_quad)

                        # fill jump out
                        self.quad_ops.back_patch(fill_out, self.quad_ops.next_quad())
                

                        if token.recognized_string == "για_τέλος":
                            token = self.get_token()
                        else:
                            self.__error("SyntaxError", f"Unclosed 'για' statement, expected 'για_τέλος', instead got {token.recognized_string}")
                    else:
                        self.__error("SyntaxError", f"Expected 'επανάλαβε', instead got {token.recognized_string}")
                else:
                    self.__error("SyntaxError", f"Expected 'έως', instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Expected ':=' , instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Expected 'για', instead got {token.recognized_string}")


    def input_stat(self) -> None:
        global token
        if token.family == "identifier":

            self.quad_ops.gen_quad("inp", token.recognized_string, "_", "_")

            token = self.get_token()
        else:
            self.__error("SyntaxError", f"Expected an identifier after 'διάβασε' statement, got {token.recognized_string}")

    def print_stat(self) -> None:
        global token
        if token.family in ["digit", "identifier"] or token.recognized_string == "(":
            expression_place = self.expression()

            self.quad_ops.gen_quad("out", expression_place, "_", "_")

        else:
            self.__error("SyntaxError", f"Expected an expresion after 'γράψε' keyword, instead got {token.recognized_string} ")

    def call_stat(self) -> None:
        global token
        if token.family == "identifier":
            id_name = token.recognized_string

            token = self.get_token()
            if token.recognized_string == "(":

                self.idtail(id_name)

                # here call
                self.quad_ops.gen_quad("call", id_name, "_", "_")
        else:
            self.__error("SyntaxError", f"Expected an identifier, instead got {token.recognized_string}")

    def else_part(self) -> None:
        global token
        if token.recognized_string == "αλλιώς":
            token = self.get_token()
            self.sequence()

    def step(self) -> str:  # or maybe an integer
        global token
        if token.recognized_string == "με_βήμα":
            token = self.get_token()
            step = self.expression()
            return step

        return "1"

    # functions calling others do not work well, find the bug
    def idtail(self, id_name) -> Tuple[str, str]:
        global token
        if token.recognized_string == "(":
            token = self.get_token()
            self.actualpars()
            return id_name, "function"

        return id_name, "no-tail"

    def actualpars(self) -> None:
        global token
        self.actualparlist()
        if token.recognized_string == ")":
            token = self.get_token()
        else:
            self.__error("SyntaxError", f"Unclosed parameter list, expected ')', instead got {token.recognized_string}")

    def actualparlist(self) -> None:
        global token
        self.actualparitem()
        while token.recognized_string == ",":
            token = self.get_token()
            self.actualparitem()

    def actualparitem(self) -> None:
        global token
        if token.recognized_string == "%":
            token = self.get_token()
            if token.family == "identifier":

                # code for call by reff
                self.quad_ops.gen_quad("par", token.recognized_string, "REF", "_")

                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Expected an identifier after '%' operator, instead got {token.recognized_string}")
        elif token.family in ["digit", "identifier"] or token.recognized_string == "(":
                par = self.expression()

                #is this even correct?
                self.quad_ops.gen_quad("par", par, "CV", "_")
        else:
            self.__error("SyntaxError", f"Expected an identifier or an expresion, instead got {token.recognized_string}")

    def condition(self) -> Tuple[List[str], List[str]]:
        global token
        boolterm_1_place = self.boolterm()

        condition_true = boolterm_1_place[0]
        condition_false = boolterm_1_place[1]

        while token.recognized_string == "ή":

            self.quad_ops.back_patch(condition_false, self.quad_ops.next_quad())

            token = self.get_token()
            boolterm_2_place = self.boolterm()
            
            condition_true = self.quad_ops.merge_list(condition_true, boolterm_2_place[0])
            condition_false = boolterm_2_place[1] 

        return condition_true, condition_false

    def boolterm(self) -> Tuple[List[str], List[str]]:
        global token
        boolfactor_1_place = self.boolfactor()

        boolterm_true = boolfactor_1_place[0]
        boolterm_false = boolfactor_1_place[1]

        while token.recognized_string == "και":
            self.quad_ops.back_patch(boolterm_true, self.quad_ops.next_quad())

            token = self.get_token()
            boolfactor_2_place = self.boolfactor()

            boolterm_false = self.quad_ops.merge_list(boolterm_false, boolfactor_2_place[1])
            boolterm_true = boolfactor_2_place[0]

        return boolterm_true, boolterm_false


    def boolfactor(self) -> Tuple[List[str], List[str]]:
        global token
        if token.recognized_string == "όχι":
            token = self.get_token()
            if token.recognized_string == "[":
                token = self.get_token()
            
                boolfactor_place = self.condition()
                boolfactor_true = boolfactor_place[1]
                boolfactor_false = boolfactor_place[0]

                if token.recognized_string == "]":
                    token = self.get_token()

                    return boolfactor_true, boolfactor_false
                else:
                    self.__error("SyntaxError", f"Unclosed condition, expected ']', instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Expected condition group symbol '[' after 'όχι' keyword, instead got {token.recognized_string}")
        elif token.recognized_string == "[":
            token = self.get_token()

            boolfactor_place = self.condition()
            boolfactor_true = boolfactor_place[0]
            boolfactor_false = boolfactor_place[1]

            if token.recognized_string == "]":
                token = self.get_token()

                return boolfactor_true, boolfactor_false
            else:
                self.__error("SyntaxError", f"Unclosed condition, expected '], instead got {token.recognized_string}")
        else:
            expression_1_place = self.expression()
            rel_oper_symbol = self.relational_oper()
            expression_2_place = self.expression()

            boolfactor_true = self.quad_ops.make_list(self.quad_ops.next_quad())
            self.quad_ops.gen_quad(rel_oper_symbol, expression_1_place, expression_2_place, "_")
            boolfactor_false = self.quad_ops.make_list(self.quad_ops.next_quad())
            self.quad_ops.gen_quad("jump", "_", "_", "_")

            return boolfactor_true, boolfactor_false


    def expression(self) -> str:
        global token
        opt_sign = self.optional_sign()
        if opt_sign == "+" or opt_sign == '':
            term_1_place = self.term()
        else:
            value = self.term()
            w = self.quad_ops.new_temp()
            self.quad_ops.gen_quad(opt_sign, "0", value, w)
            term_1_place = w
        while token.family == "addOper":
            add_oper_symbol = self.add_oper()
            term_2_place = self.term()

            w = self.quad_ops.new_temp()

            self.symbol_table.add_entity(TemporaryVariable(w, "int", self.symbol_table.scope_list[-1].offset))

            self.quad_ops.gen_quad(add_oper_symbol, term_1_place, term_2_place, w)
            term_1_place = w
        
        expression_place = term_1_place
        return expression_place

    def term(self) -> str:
        global token
        factor_1_place = self.factor()
        while token.family == "mulOper":
            mul_oper_symbol = self.mul_oper()
            factor_2_place = self.factor()

            w = self.quad_ops.new_temp()

            self.symbol_table.add_entity(TemporaryVariable(w, "int", self.symbol_table.scope_list[-1].offset))

            self.quad_ops.gen_quad(mul_oper_symbol, factor_1_place, factor_2_place, w)
            factor_1_place = w
        
        term_place = factor_1_place
        return term_place

    def factor(self) -> str:
        global token
        if token.family == "digit":

            factor_place = token.recognized_string
            token = self.get_token()

            return factor_place
        elif token.recognized_string == "(":
            token = self.get_token()

            expression_place = self.expression()

            if token.recognized_string == ")":

                factor_place = expression_place

                token = self.get_token()
                
                return factor_place
            else:
                self.__error("SyntaxError", f"Unclosed expression, expected ')', instead got {token.recognized_string}")
        elif token.family == "identifier":
            id_name = token.recognized_string
            token = self.get_token()

            # not certain if it should return, might get none if identifier and not function
            factor_place, type = self.idtail(id_name)

            if type == "function":
                w = self.quad_ops.new_temp()

                self.symbol_table.add_entity(TemporaryVariable(w, "int", self.symbol_table.scope_list[-1].offset))

                self.quad_ops.gen_quad("par", w, "ret", "_")
                self.quad_ops.gen_quad("call", id_name, "_", "_")

                factor_place = w

            # propably return the name, if function the function, else the identifier
            #look it
            return factor_place
        else:
            self.__error("SyntaxError", f"Not a valid expression")

    def relational_oper(self) -> str:
        global token
        if token.recognized_string in RELATIONAL_SYMBOLS:
            rel_oper_symbol = token.recognized_string
            token = self.get_token()
            return rel_oper_symbol

    def add_oper(self) -> str:
        global token
        if token.recognized_string in ["+", "-"]:
            add_oper_symbol = token.recognized_string
            token = self.get_token()
            return add_oper_symbol
        else:
            self.__error("SyntaxError", f"Expected add operation symbols, intead got {token.recognized_string}")
        

    def mul_oper(self) -> str:
        global token
        if token.recognized_string in ["*", "/"]:
            mul_oper_symbol = token.recognized_string
            token = self.get_token()
            return mul_oper_symbol
        else:
            self.__error("SyntaxError", f"Expected mul operation symbol, instead got {token.recognized_string}")

    def optional_sign(self) -> str:
        global token
        ret = ""
        if token.family == "addOper":
            ret += self.add_oper()
            
        return ret

    def get_token(self) -> Token:
        ret_token = self.lex.next_token()
        self.tokens.write(str(ret_token)+"\n")
        return ret_token
    
    def __error(self, error_type, msg):
        print(f"{error_type} ({self.lex.current_line}): {msg}")
        self.tokens.close()
        exit(-1)

    def __success_exit(self):
        for quad in self.generated_program:
            self.quads.write(str(quad) + "\n")

        self.quads.close()
        self.tokens.close()
        self.table.close()
        self.final.close()
        return 1

    def __write_to_sym_file(self):
        write_values = self.symbol_table.print_table()
        self.table.write(write_values)
        self.table.write('\n\n')

    def __set_up_log(self):
        path = os.path.abspath(os.getcwd() + "/log")
        print(os.getcwd())
        if Path(path).exists():
            shutil.rmtree(path)
        
        os.makedirs(path)

    def __set_up_asm_file(self):
        path = os.path.abspath(os.getcwd() + "/final.asm")
        if os.path.isfile(path):
            os.remove(path)
    
    def __manage_varlist(self, caller: str, id_name: str, function_name: str) -> None:
        if caller == "declarations":
            self.symbol_table.add_entity(Variable(id_name, "int", self.symbol_table.scope_list[-1].offset))
        elif caller == "formalparlist":
            function, _ = self.symbol_table.search_entity(function_name)
            self.symbol_table.add_argument(function, FormalParameter(id_name, "int", "_"))    # fill later
        elif caller == "funcinput":
            self.symbol_table.add_entity(Parameter(id_name, self.symbol_table.scope_list[-1].offset, "int", "CV"))
            formal_parameter = self.symbol_table.find_argument(function_name, id_name)
            if formal_parameter == None:
                self.__error("SemanticError", "Argument does not exist")
            formal_parameter.mode = "CV"
        elif caller == "funcoutput":
            self.symbol_table.add_entity(Parameter(id_name, self.symbol_table.scope_list[-1].offset, "int", "REF"))
            formal_parameter = self.symbol_table.find_argument(function_name, id_name)
            if formal_parameter == None:
                self.__error("SemanticError", "Argument does not exist")
            formal_parameter.mode = "REF"

class Quad:

    def __init__(self, label: str, op: str, op1: str, op2:str, op3:str) -> None:
        self.label: str = label
        self.op: str = op
        self.op1: str = op1
        self.op2: str = op2
        self.op3: str = op3

    def __str__(self):
        return f"L{self.label}: {self.op}, {self.op1}, {self.op2}, {self.op3}"

class QuadList:

    def __init__(self):
        self.program_list: List[Quad] = []
        self.quad_counter: int = 0

    def back_patch(self, list: List[str], label: str) -> None:
        for quad_label in list:
            self.program_list[int(quad_label)-1].op3 = label

    def gen_quad(self, op: str, op1: str, op2: str, op3: str):
        self.quad_counter += 1
        generated_quad = Quad(self.quad_counter, op, op1, op2, op3)
        self.program_list.append(generated_quad)
        return generated_quad

    def next_quad(self) -> str:
        return f"{self.quad_counter+1}"

    def empty_list(self) -> List[str]:
        return []

    def make_list(self, label: str) -> List[str]:
        return [label]

    def merge_list(self, list1: List[str], list2: List[str]) -> List[str]:
        return list1 + list2

    def new_temp(self) -> str:
        global TEMP_COUNTER 
        ret = f"T_{TEMP_COUNTER}"
        TEMP_COUNTER += 1
        return ret

class Entity(ABC):

    def __init__(self, name: str) -> None:
        self.name: str = name

class Variable(Entity):

    def __init__(self, name: str, datatype: int, offset: int) -> None:
        super().__init__(name)
        self.datatype: int = datatype
        self.offset: int = offset

    def __str__(self):
        return f'Variable: Name: {self.name}, Datatype: {self.datatype}, Offset: {self.offset}\n' 

class TemporaryVariable(Variable):

    def __init__(self, name: str, datatype: str, offset: int) -> None:
        super().__init__(name, datatype, offset)

    def __str__(self):
        return f'Temporary Variable: Name: {self.name}, Datatype: {self.datatype}, Offset: {self.offset}\n'

class FormalParameter(Entity):

    def __init__(self, name: str, datatype: int, mode: int) -> None:
        super().__init__(name)
        self.datatype: int = datatype
        self.mode: int = mode

    def __str__(self):
        return f'Formal Parameter: Name: {self.name}, Datatype: {self.datatype}, Mode: {self.mode}\n'

class Parameter(Entity):

    def __init__(self, name: str, offset: int, datatype: int, mode: int) -> None:
        #Variable.__init__(self, name, datatype, offset)
        #FormalParameter.__init__(self, name, datatype, mode)
        super().__init__(name)
        self.offset = offset
        self.datatype = datatype
        self.mode = mode
    
    def __str__(self):
        return f'Parameter: Name: {self.name}, Offset: {self.offset}, Datatype: {self.datatype}, Mode: {self.mode}\n'

class Procedure(Entity):

    def __init__(self, name: str, starting_quad_label: str, frame_length: int) -> None:
        super().__init__(name)
        self.starting_quad_label: str = starting_quad_label
        self.frame_length: int = frame_length
        self.arguments: List[FormalParameter] = []

    def __str__(self):
        proc =  f'Procedure: Name: {self.name}, Startind Quad Label: {self.starting_quad_label}, Frame Length: {self.frame_length}\n'
        args = f'\t\tFormal Parameters of procedure {self.name}: \n'
        for formalpar in self.arguments:
            args += f'\t\t\t{formalpar}' 
        return proc+args

class Function(Procedure):

    def __init__(self, name: str, starting_quad_label: str, datatype: int, frame_length: int) -> None:
        super().__init__(name, starting_quad_label, frame_length)
        self.datatype: int = datatype

    def __str__(self):
        func = f'Function: Name: {self.name}, Startind Quad Label: {self.starting_quad_label}, Datatype: {self.datatype}, Frame Length: {self.frame_length}\n'
        args = f'\t\tFormal Parameters of function {self.name}: \n'
        for formalpar in self.arguments:
            args += f'\t\t\t{formalpar}' 
        return func+args
    

class Scope():

    def __init__(self, nesting_level) -> None:
        self.entity_list: List[Entity] = []
        self.nesting_level: int = nesting_level
        self.offset = SYMBOL_TABLE_START

class Table():

    def __init__(self) -> None:
        self.scope_list: List[Scope] = []

    def print_table(self)  -> str:
        global NESTING_LEVEL
        current_level: int = NESTING_LEVEL
        accumulator = ''
        while current_level >= 0:
            header = f'Level {current_level}\n'
            accumulator += header
            for entity in self.scope_list[current_level].entity_list:
                body = f'\t{entity}'
                accumulator += body
            current_level -= 1
        
        return accumulator

    def add_scope(self) -> None:
        global NESTING_LEVEL
        NESTING_LEVEL += 1
        self.scope_list.append(Scope(NESTING_LEVEL))

    def delete_scope(self) -> None:
        global NESTING_LEVEL
        self.scope_list.pop()
        NESTING_LEVEL -= 1

    def add_entity(self, entity: Entity) -> None:
        scope = self.scope_list[-1]
        scope.entity_list.append(entity)
        if isinstance(entity, Function) or isinstance(entity, Procedure):
            return
        scope.offset += 4

    def add_argument(self, entity: Entity, argument: FormalParameter):
        #self.scope_list[-1].entity_list[-1].arguments.append(argument)
        entity.arguments.append(argument)

    def search_entity(self, name: str) -> Tuple[Entity, int]:
        levels_up: int = 0
        for scope in reversed(self.scope_list):
            for entity in scope.entity_list:
                if entity.name == name:
                    return entity, levels_up
            levels_up += 1

        return None
    
    def find_argument(self, function_name: str, argument_name: str) -> FormalParameter:
        function, _ = self.search_entity(function_name)
        for argument in function.arguments:
            if argument.name == argument_name:
                return argument
        
        return None


    def __check_if_entity_exists(self, name: str, entity_types: Tuple[str]) -> Tuple[str, str]:
        entity, _ = self.search_entity(name)
        if entity == None:
            return "SemanticError", f"Entity {name} does not exist"

        return entity
    
    def __check_if_already_declared_in_scope(self, name: str, entity_type: Tuple[str, str]) -> Tuple[str, str]:
        scope: Scope = self.scope_list[-1] #current scope
        for entity in scope:
            if entity.name == name:
                return ""
        return "SemanticError", f"Entity {name} is not declared in the current scope"
    
# coding mess, refactor
class Assembler():
        
    def __init__(self, parser: Parser):
        self.parser = parser

    """
    stores into t0 the address of a non local variable
    finds from the symbol table how many levels up(down) the local variable exists
    and through the access link it finds it
    """
    def gnvlcode(self, name: str):
        # bug, searches also in each own scope
        self.parser.final.write("lw t0, -4(sp)\n")  # currect link
        entity, levels_up = self.parser.symbol_table.search_entity(name)

        # should not be none, semantic analysis before hand
        if entity != None:
            for i in range(levels_up-1):    # if two levels up, since current already loaded link access, only one more needed (level_up-1+1 levels above)
                self.parser.final.write("lw t0, -4(sp)")

            # non local variables
            if isinstance(entity, Variable) or isinstance(entity, Parameter):
                self.parser.final.write(f"addi t0, t0, -{entity.offset}")



    """
    load data(value) into register(register)
    the loading can happen from memory
    or assign an immidiate to register r
    """
    def loadvr(self, value: str, register: str):
        
        # if value is an immidiate
        if value.lstrip("-") in DIGITS:
            self.parser.final.write(f"li {register}, {value}\n")
        
        else:


            entity, levels_up = self.parser.symbol_table.search_entity(value)  # get entity and how many levels up above it is
            entity_scope = self.parser.symbol_table.scope_list[levels_up]  # scope in which entity exists
            current_scope = self.parser.symbol_table.scope_list[-1]
            
            # global variable, exists in main frame
            if entity_scope.nesting_level == 0 and (isinstance(entity, Variable) or isinstance(entity, TemporaryVariable)):
                self.parser.final.write(f"lw {register}, -{entity.offset}(gp)")
            
            # value declared in the function that is executing  and it is local variable, formal parameter passed by value or temporary variable
            elif entity_scope.nesting_level == current_scope.nesting_level and (isinstance(entity, Variable) or (isinstance(entity, FormalParameter) and entity.mode == "CV") or isinstance(entity, TemporaryVariable)):
                self.parser.final.write(f"lw {register}, -{entity.offset}(sp)")

            # value declared in the function that is executing and it is formal parameter that is passed by referrence
            elif entity_scope.nesting_level == current_scope.nesting_level and (isinstance(entity, FormalParameter) and entity.mode == "REF"):
                asm_code = f"lw t0, -{entity.offset}(sp)\nlw {register}, (t0)\n"
                self.parser.final.write(asm_code)

            # value declared in some ancestor and it is local variable or formal parameter passed by value
            # ancestor declared in previous level, nesting_level(ancestor) < nesting_level(current)
            elif entity_scope.nesting_level < current_scope.nesting_level and (isinstance(entity, Variable) or (isinstance(entity, FormalParameter) and entity.mode == "CV")):
                self.gnvlcode(value)
                self.parser.final.write(f"lw {register}, (t0)\n")

            # value declared in some ancestor and it is local variable or formal parameter passed by referrence
            elif entity_scope.nesting_level < current_scope.nesting_level and (isinstance(entity, FormalParameter) and entity.mode == "REF"):
                self.gnvlcode(value)
                asm_code = f"lw t0, (t0)\nlw {register}, (t0)"
                self.parser.final.write(asm_code)


    """
    load data from the registe(register) into memory(variable v)
    """
    def storerv(self, register: str, value: str):
        entity, levels_up = self.parser.symbol_table.search_entity(value)  # get entity and how many levels up above it is
        entity_scope = self.parser.symbol_table.scope_list[levels_up]  # scope in which entity exists
        current_scope = self.parser.symbol_table.scope_list[-1]

        # value is global variable, exist into main program
        if entity_scope.nesting_level == 0 and (isinstance(entity, Variable) or isinstance(entity, TemporaryVariable)):
            self.parser.final.write(f"sw {register}, -{entity.offset}(gp)")

        # value is local variable, formal parameter passed by value and nesting level equal to the current, or temp variable
        elif entity_scope.nesting_level == current_scope.nesting_level and (isinstance(entity, Variable) or (isinstance(entity, FormalParameter) and entity.mode == "CV") or isinstance(entity, TemporaryVariable)):
            self.parser.final.write(f"sw {register}, -{entity.offset}(sp)")

        # value is formal parameter passed by referrence and nesting level equal with the current
        elif entity_scope.nesting_level == current_scope.nesting_level and (isinstance(entity, FormalParameter) and entity.mode == "REF"):
            asm_code = f"lw t0, -{entity.offset}(sp)\nsw {register}, (t0)"
            self.parser.final.write(asm_code)

        # value is local variable, formal parameter passed by value and nesting level smaller than current
        elif entity_scope.nesting_level < current_scope.nesting_level and (isinstance(entity, Variable) or (isinstance(entity, FormalParameter) and entity.mode == "CV")):
            self.gnvlcode(value)
            self.parser.final.write(f"sw {register}, (t0)")

         # value is local variable, formal parameter passed by referrence and nesting level smaller than current
        elif entity_scope.nesting_level < current_scope.nesting_level and (isinstance(entity, FormalParameter) and entity.mode == "REF"):
            self.gnvlcode(value)
            asm_code = f"lw t0, (t0)\nsw {register}, (t0)"
            self.parser.final.write(asm_code)


    def create_assembly_code(self):
        asm_file = self.parser.final
        for quad in self.parser.generated_program:
            
            asm_file.write(f"L{quad.label}:\n")

            if quad.op == "inp":
                asm_code = f"li a7, 63\necall\n"
                asm_file.write(asm_code)
                self.storerv("a0", quad.op1)
            
            elif quad.op == "out":
                self.loadvr(quad.op1, "a0")
                asm_code = f"li a7, 1\necall"
                asm_file.write()

            elif quad.op == "halt":
                asm_code = f"li a0, 0\nli a7, 93\necall"
                asm_file.write(asm_code)

            elif quad.op == "jump":
                asm_file.write(f"b {quad.op3}")

            elif quad.op in RELATIONAL_SYMBOLS:
                symbol = quad.op
                self.loadvr(quad.op1, "t1")
                self.loadvr(quad.op2, "t2")
                jump_label = quad.op3

                if symbol == ">":
                    asm_file.write(f"bqt t1, t2, {jump_label}\n")
                elif symbol == ">=":
                    asm_file.write(f"bge t1, t2, {jump_label}\n")
                elif symbol == "<":
                    asm_file.write(f"blt t1, t2, {jump_label}\n")
                elif symbol == "<=":
                    asm_file.write(f"ble t1, t2 {jump_label}\n")
                elif symbol == "=":
                    asm_file.write(f"beq t1, t2, {jump_label}\n")
                elif symbol == "<>":
                    asm_file.write(f"bne t1, t2, {jump_label}\n")

            elif quad.op == ":=":
                self.loadvr(quad.op1, "t1")
                self.storerv("t1", quad.op3)

            elif quad.op in ADD_OPERATORS+MUL_OPERATORS:
                operation = quad.op
                self.loadvr(quad.op1, "t1")
                self.loadvr(quad.op2, "t2")

                if operation == "+":
                    asm_file.write(f"add t1, t1, t2")
                elif operation == "-":
                    asm_file.write(f"sub t1, t1, t2")
                elif operation == "*":
                    asm_file.write(f"mul t1, t1, t2")
                elif operation == "/":
                    asm_file.write(f"div t1, t1, t2")
                
                self.storerv("t1", quad.op3)

            # ret value, parameter passing, begin/end block
            # ret value not implemented correctly so no impl here

            elif quad.op == "par":
                pass



#Usage: type in terminal python3 compiler.py your_file_name
if __name__ == "__main__":

    file = sys.argv[1]
    lex: Lex = Lex(file)
    parser: Parser = Parser(lex)
    parser.syntax_analyzer()    