#Stefanos Gersch-Koutsogiannis 5046
#Filippos Alexiou 5146

import string
import sys
import os
from typing import List
from pathlib import Path
import shutil

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
                if int(recognized_token) > 10000:
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
        self.tokens = open("log/tokens.txt", "a")
        self.quads = open("log/quadlist.int", "a")
        # new code
        self.quad_ops: QuadList = QuadList()
        self.generated_program = self.quad_ops.program_list

    def syntax_analyzer(self) -> None:
        global token
        token = self.get_token()
        self.program()

    
    def program(self) -> None:
        global token
        if token.recognized_string == "πρόγραμμα":
            token = self.get_token()
            if token.family == "identifier":
                program_name = token.recognized_string
                token = self.get_token()
                self.programblock(program_name)
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
                self.__success_exit()
            else:
                self.__error("SyntaxError", f"The program block is not closed, expected 'τέλος_προγράμματος', got {token}")
        else:
            self.__error("SyntaxError", f"No program block in the source file {self.lex.file}")


    def declarations(self) -> None:
        global token
        while token.recognized_string == "δήλωση":
            token = self.get_token()
            self.varlist()

    def varlist(self) -> None:
        global token
        if token.family == "identifier":
            token = self.get_token()
            while token.recognized_string == ",":
                token = self.get_token()
                if token.family == "identifier":
                    token = self.get_token()
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
            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()
                self.formalparlist()
                if token.recognized_string == ")":
                    token = self.get_token()
                    self.funcblock(function_name)
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
            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()
                self.formalparlist()
                if token.recognized_string == ")":
                    token = self.get_token()
                    self.procblock(procedure_name)
                else:
                    self.__error("SyntaxError", f"Procedure parameter list is not closed, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Procedure parameter list is missing, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Procedure should be named after an identifier, instead got {token.recognized_string}")

    def formalparlist(self) -> None:
        global token
        if token.family == "identifier":
            self.varlist()       

    def funcblock(self, function_name) -> None:
        global token
        if token.recognized_string == "διαπροσωπεία":
            token = self.get_token()
            self.funcinput()
            self.funcoutput()
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_συνάρτησης":

                # code for the beginning of the function block
                self.quad_ops.gen_quad("begin_block", function_name, "_", "_")

                token = self.get_token()
                self.sequence()
                if token.recognized_string == "τέλος_συνάρτησης":
                    self.quad_ops.gen_quad("end_block", function_name, "_", "_")
                    token = self.get_token()
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
            self.funcinput()
            self.funcoutput()
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_διαδικασίας":

                # code for the beginning of the procedure block
                self.quad_ops.gen_quad("begin_block", procedure_name, "_", "_")
                token = self.get_token()
                self.sequence()
                if token.recognized_string == "τέλος_διαδικασίας":
                    token = self.get_token()
                else:
                    self.__error("SyntaxError", f"Unclosed procedure block, expected 'τέλος_διαδικασίας', instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Missing procedure block declaration, expected 'αρχή_διαδικασίας', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Procedure block's 'διαπροσωπεία' is missing, instead got {token.recognized_string}")

    def funcinput(self) -> None:
        global token
        if token.recognized_string == "είσοδος":
            token = self.get_token()
            self.varlist()

    def funcoutput(self) -> None:
        global token
        if token.recognized_string == "έξοδος":
            token = self.get_token()
            self.varlist()

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
            # error or nothing?
            return


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
        self.condition()
        if token.recognized_string == "τότε":
            token = self.get_token()
            self.sequence()
            self.else_part()
            if token.recognized_string == "εάν_τέλος":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed 'εάν' statement, expected 'εάν_τέλος', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Expected 'τότε', instead got {token.recognized_string}")


    def while_stat(self) -> None:
        global token
        self.condition()
        if token.recognized_string == "επανάλαβε":
            token = self.get_token()
            self.sequence()
            if token.recognized_string == "όσο_τέλος":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed 'όσο' statement, expected 'όσο_τέλος', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Expected 'όσο', instead got {token.recognized_string}")

    def do_stat(self) -> None:
        global token
        self.sequence()
        if token.recognized_string == "μέχρι":
            token = self.get_token()
            self.condition()
        else:
            self.__error("SyntaxError", f"Expeted 'μέχρι', instead got {token.recognized_string}")

    def for_stat(self) -> None:
        global token
        if token.family == "identifier":
            token = self.get_token()
            if token.recognized_string == ":=":
                token = self.get_token()
                self.expression()
                if token.recognized_string == "έως":
                    token = self.get_token()
                    self.expression()
                    self.step()
                    if token.recognized_string == "επανάλαβε":
                        token = self.get_token()
                        self.sequence()
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

    # function call if function has not parameters is call function_name without ()
    def call_stat(self) -> None:
        global token
        if token.family == "identifier":
            id_name = token.recognized_string

            token = self.get_token()
            if token.recognized_string == "(":
                self.idtail(id_name)
        else:
            self.__error("SyntaxError", f"Expected an identifier, instead got {token.recognized_string}")

    def else_part(self) -> None:
        global token
        if token.recognized_string == "αλλιώς":
            token = self.get_token()
            self.sequence()

    def step(self) -> None:
        global token
        if token.recognized_string == "με_βήμα":
            token = self.get_token()
            self.expression()

    # here add ret value
    def idtail(self, id_name) -> str:
        global token
        if token.recognized_string == "(":
            token = self.get_token()
            self.actualpars()

            self.quad_ops.gen_quad("call", id_name, "_", "_")

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
        elif token.family in ["number", "identifier"] or token.recognized_string == "(":
                par = self.expression()

                #is this even correct?
                self.quad_ops.gen_quad("par", par, "CV", "_")
        else:
            self.__error("SyntaxError", f"Expected an identifier or an expresion, instead got {token.recognized_string}")

    def condition(self) -> None:
        global token
        self.boolterm()
        if token.recognized_string == "ή":
            token = self.get_token()
            self.boolterm()

    def boolterm(self) -> None:
        global token
        self.boolfactor()
        while token.recognized_string == "και":
            token = self.get_token()
            self.boolfactor()

    def boolfactor(self) -> None:
        global token
        if token.recognized_string == "όχι":
            token = self.get_token()
            if token.recognized_string == "[":
                token = self.get_token()
                self.condition()
                if token.recognized_string == "]":
                    token = self.get_token()
                else:
                    self.__error("SyntaxError", f"Unclosed condition, expected ']', instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Expected condition group symbol '[' after 'όχι' keyword, instead got {token.recognized_string}")
        elif token.recognized_string == "[":
            token = self.get_token()
            self.condition()
            if token.recognized_string == "]":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed condition, expected '], instead got {token.recognized_string}")
        elif token.family in ["digit", "identifier"] or token.recognized_string == "(":
            self.expression()
            self.relational_oper()
            self.expression()
        else:
            self.__error("SyntaxError", f"Not a valid condition")

    def expression(self) -> str:
        global token
        # add it?
        self.optional_sign()
        term_1_place = self.term()
        while token.family == "addOper":
            add_oper_symbol = self.add_oper()
            term_2_place = self.term()

            w = self.quad_ops.new_temp()
            self.quad_ops.gen_quad(add_oper_symbol, term_1_place, term_2_place, w)
        
        expression_place = term_1_place
        return expression_place

    def term(self) -> str:
        global token
        factor_1_place = self.factor()
        while token.family == "mulOper":
            mul_oper_symbol = self.mul_oper()
            factor_2_place = self.factor()

            w = self.quad_ops.new_temp()
            self.quad_ops.gen_quad(mul_oper_symbol, factor_1_place, factor_2_place, w)
        
        term_place = factor_1_place

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

            # not certain
            factor_place = self.idtail(id_name)

            #self.quad_ops.gen_quad()
        else:
            self.__error("SyntaxError", f"Not a valid expression")

    def relational_oper(self) -> None:
        global token
        if token.recognized_string in RELATIONAL_SYMBOLS:
            token = self.get_token()

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

    def optional_sign(self) -> None:
        global token
        if token.family == "addOper":
            self.add_oper()

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
        exit(1)

    def __set_up_log(self):
        path = os.path.abspath(os.getcwd() + "/log")
        if Path(os.path.abspath(os.getcwd() + "/log")).exists():
            shutil.rmtree(path)
        
        os.makedirs(path)
    
class Quad:

    def __init__(self, label: str, op: str, op1: str, op2:str, op3:str) -> None:
        self.label = label
        self.op = op
        self.op1 = op1
        self.op2 = op2
        self.op3 = op3

    def __str__(self):
        return f"Label: {self.label}, op: {self.op}, op1: {self.op1}, op2: {self.op2}, op3: {self.op3}"

class QuadList:

    def __init__(self):
        self.program_list: List[Quad] = []
        self.quad_counter = 0

    def back_patch(self, list:List[str], z: str):
        for i in range(self.program_list):
            for j in range(list):
                if self.program_list[i].label == list[j]:
                    self.program_list[i].op3 = z

    def gen_quad(self, op: str, op1: str, op2: str, op3: str):
        self.quad_counter += 1
        generated_quad = Quad(self.quad_counter, op, op1, op2, op3)
        self.program_list.append(generated_quad)
        return generated_quad

    # needs fixing
    def next_quad(self) -> int:
        #self.quad_counter += 1
        return self.quad_counter+1

    def empty_list(self) -> List[str]:
        return []

    def make_list(self, item: str) -> List[str]:
        return [item]

    def merge_list(self, list1: List[str], list2: List[str]) -> List[str]:
        return list1 + list2

    def new_temp(self):
        global TEMP_COUNTER 
        TEMP_COUNTER += 1
        return f"T_{TEMP_COUNTER}"

#Usage: type in terminal python3 compiler.py your_file_name
if __name__ == "__main__":

    file = "test.gpp"
    #file = sys.argv[1]
    lex: Lex = Lex(file)
    parser: Parser = Parser(lex)
    parser.syntax_analyzer()    