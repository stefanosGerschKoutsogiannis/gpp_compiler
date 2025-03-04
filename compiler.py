import string
import sys

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

TEMP_COUNTER = 0
DELIMETERS = [",",";", ":"]
BY_REFERENCE_OPERATOR = "%"

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
                exit()

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
        # new code
        #self.generated_program: QuadList = QuadList()

    def syntax_analyzer(self) -> None:
        global token
        token = self.get_token()
        self.program()

    
    def program(self) -> None:
        global token
        if token.recognized_string == "πρόγραμμα":
            token = self.get_token()
            if token.family == "identifier":
                token = self.get_token()
                self.programblock()
            else:
                self.__error("SyntaxError", "Expected an identifier after 'πρόγραμμα' keyword, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", "Program should start with 'πρόγραμμα' keyword, instead got {token.recognized_string}")


    def programblock(self) -> None:
        global token
        self.declarations()
        self.subprograms()
        if token.recognized_string == "αρχή_προγράμματος":
            token = self.get_token()
            self.sequence()
            if token.recognized_string == "τέλος_προγράμματος":
                #token = self.get_token()
                print("Success")
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
            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()
                self.formalparlist()
                if token.recognized_string == ")":
                    token = self.get_token()
                    self.funcblock()
                else:
                    self.__error("SyntaxError", f"Function parameter list is not closed, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Function parameter list is missing, instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Function should be named after an identifier, instead got {token.recognized_string}")

    def proc(self) -> None:
        global token
        if token.family == "identifier":
            token = self.get_token()
            if token.recognized_string == "(":
                token = self.get_token()
                self.formalparlist()
                if token.recognized_string == ")":
                    token = self.get_token()
                    self.procblock()
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

    def funcblock(self) -> None:
        global token
        if token.recognized_string == "διαπροσωπεία":
            token = self.get_token()
            self.funcinput()
            self.funcoutput()
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_συνάρτησης":
                token = self.get_token()
                self.sequence()
                if token.recognized_string == "τέλος_συνάρτησης":
                    token = self.get_token()
                else:
                    self.__error("SyntaxError", f"Unclosed function block, expected 'τέλος_συνάρτησης' keyword, instead got {token.recognized_string}")
            else:
                self.__error("SyntaxError", f"Missing function block declaration, expected 'αρχή_συνάρτησης', instead got {token.recognized_string}")
        else:
            self.__error("SyntaxError", f"Function block's 'διαπροσωπεία' is missing, instead got {token.recognized_string}")

    def procblock(self) -> None:
        global token
        if token.recognized_string == "διαπροσωπεία":
            token = self.get_token()
            self.funcinput()
            self.funcoutput()
            self.declarations()
            self.subprograms()
            if token.recognized_string == "αρχή_διαδικασίας":
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
            token = self.get_token()
            self.assignment_stat()
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


    def assignment_stat(self) -> None:
        global token
        if token.recognized_string == ":=":
            token = self.get_token()
            self.expression()
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
            token = self.get_token()
        else:
            self.__error("SyntaxError", f"Expected an identifier after 'διάβασε' statement, got {token.recognized_string}")

    def print_stat(self) -> None:
        global token
        if token.family in ["digit", "identifier"] or token.recognized_string == "(":
            self.expression()
        else:
            self.__error("SyntaxError", f"Expected an expresion after 'γράψε' keyword, instead got {token.recognized_string} ")

    # function call if function has not parameters is call function_name without ()
    def call_stat(self) -> None:
        global token
        if token.family == "identifier":
            token = self.get_token()
            if token.recognized_string == "(":
                self.idtail()
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

    def idtail(self) -> None:
        global token
        if token.recognized_string == "(":
            token = self.get_token()
            self.actualpars()

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
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Expected an identifier after '%' operator, instead got {token.recognized_string}")
        elif token.family in ["number", "identifier"] or token.recognized_string == "(":
             self.expression()
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

    def expression(self) -> None:
        global token
        self.optional_sign()
        self.term()
        while token.family == "addOper":
            self.add_oper()
            self.term()

    def term(self) -> None:
        global token
        self.factor()
        while token.family == "mulOper":
            self.mul_oper()
            self.factor()

    def factor(self) -> None:
        global token
        if token.family == "digit":
            token = self.get_token()
        elif token.recognized_string == "(":
            token = self.get_token()
            self.expression()
            if token.recognized_string == ")":
                token = self.get_token()
            else:
                self.__error("SyntaxError", f"Unclosed expression, expected ')', instead got {token.recognized_string}")
        elif token.family == "identifier":
            token = self.get_token()
            self.idtail()
        else:
            self.__error("SyntaxError", f"Not a valid expression")

    def relational_oper(self) -> None:
        global token
        if token.recognized_string in RELATIONAL_SYMBOLS:
            token = self.get_token()

    def add_oper(self) -> None:
        global token
        if token.recognized_string in ["+", "-"]:
            token = self.get_token()
        else:
            self.__error("SyntaxError", f"Expected add operation symbols, intead got {token.recognized_string}")
        

    def mul_oper(self) -> None:
        global token
        if token.recognized_string in ["*", "/"]:
            token = self.get_token()
        else:
            self.__error("SyntaxError", f"Expected mul operation symbol, instead got {token.recognized_string}")

    def optional_sign(self) -> None:
        global token
        if token.family == "addOper":
            self.add_oper()

    def get_token(self) -> Token:
        return self.lex.next_token()
    
    def __error(self, error_type, msg):
        print(f"{error_type} ({self.lex.current_line}): {msg}")
        exit(-1)
    
#Usage: type in terminal python3 compiler.py your_file_name
if __name__ == "__main__":

    file = "fact.gpp"
    #file = sys.argv[1]
    lex: Lex = Lex(file)
    parser: Parser = Parser(lex)
    parser.syntax_analyzer()

    