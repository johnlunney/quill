
import rply
from rply.token import Token
from rpython.rlib.runicode import str_decode_utf_8, unicode_encode_utf_8, UNICHR

from nolang.lexer import TOKENS, ParseError
from nolang import astnodes as ast


def sr(p):
    return (p[0].getsrcpos()[0], p[-1].getsrcpos()[1])


class ParsingState(object):
    def __init__(self, filename, input):
        self.input = input
        self.filename = filename


def errorhandler(state, lookahead):
    lines = state.input.splitlines()
    sourcepos = lookahead.getsourcepos()
    line = lines[sourcepos.lineno - 1]
    assert isinstance(lookahead, Token)
    raise ParseError('Parsing error', line, state.filename, sourcepos.lineno,
                     sourcepos.colno - 1,
                     len(lookahead.value) + sourcepos.colno - 1)


def hex_to_utf8(s):
    uchr = UNICHR(int(s, 16))
    return unicode_encode_utf_8(uchr, len(uchr), 'strict')


def get_parser():
    pg = rply.ParserGenerator(TOKENS, precedence=[
        ('left', ['AND']),
        ('left', ['OR']),
        ('left', ['EQ', 'LT']),
        ('left', ['PLUS', 'MINUS']),
        ('left', ['TRUEDIV', 'STAR']),
        ('left', ['DOT']),
        ('left', ['LEFT_PAREN']),
    ])
    pg.error(errorhandler)

    @pg.production('program : body')
    def program_body(state, p):
        element_list = p[0].get_element_list()
        return ast.Program(element_list, srcpos=sr(element_list))

    @pg.production('body :')
    def body_empty(state, p):
        return ast.FunctionBody(None, None)

    @pg.production('body : body body_element')
    def body_body_element(state, p):
        return ast.FunctionBody(p[1], p[0])

    @pg.production('body_element : function')
    def body_function(state, p):
        return p[0]

    @pg.production('body_element : class_definition')
    def body_element_class_definition(state, p):
        return p[0]

    @pg.production('body_element : SEMICOLON')
    def body_element_semicolon(state, p):
        return None

    @pg.production('body_element : IMPORT IDENTIFIER dot_identifier_list'
                   ' optional_import SEMICOLON')
    def body_element_import_statement(state, p):
        basename = p[1].getstr()
        if p[2] is None and p[3] is None:
            return ast.Import([basename], [], srcpos=sr(p))
        if p[3] is None:
            names = p[2].get_names()
            return ast.Import([basename] + names[:-1], [names[-1]], srcpos=sr(p))
        if p[2] is None:
            return ast.Import([basename], p[3].get_names(), srcpos=sr(p))
        return ast.Import([basename] + p[2].get_names(),
                          p[3].get_names(), srcpos=sr(p))

    @pg.production('optional_import :')
    def optional_import_empty(state, p):
        return None

    @pg.production('optional_import : '
                   'LEFT_CURLY_BRACE IDENTIFIER identifier_list '
                   'RIGHT_CURLY_BRACE')
    def optional_import_brace(state, p):
        return ast.IdentifierListPartial(p[1].getstr(), p[2])

    @pg.production('class_definition : CLASS IDENTIFIER LEFT_CURLY_BRACE body '
                   'RIGHT_CURLY_BRACE')
    def class_definition(state, p):
        return ast.ClassDefinition(p[1].getstr(), p[3], srcpos=sr(p))

    @pg.production('class_definition : CLASS IDENTIFIER LEFT_PAREN IDENTIFIER '
                   'RIGHT_PAREN LEFT_CURLY_BRACE body RIGHT_CURLY_BRACE')
    def class_definition_inheritance(state, p):
        return ast.ClassDefinition(p[1].getstr(), p[6], p[3].getstr(), srcpos=sr(p))

    @pg.production('function : DEF IDENTIFIER arglist LEFT_CURLY_BRACE'
                   ' function_body RIGHT_CURLY_BRACE')
    def function_function_body(state, p):
        lineno = p[0].getsourcepos().lineno
        return ast.Function(p[1].getstr(), p[2].get_names(),
                            p[4].get_element_list(), lineno, srcpos=sr(p))

    @pg.production('function_body :')
    def function_body_empty(state, p):
        return ast.FunctionBody(None, None)

    @pg.production('function_body : function_body statement')
    def function_body_statement(state, p):
        return ast.FunctionBody(p[1], p[0])

    @pg.production('statement : expression SEMICOLON')
    def statement_expression(state, p):
        return ast.Statement(p[0], srcpos=sr(p))

    @pg.production('statement : SEMICOLON')
    def staement_empty(state, p):
        return None

    @pg.production('statement : VAR IDENTIFIER var_decl SEMICOLON')
    def statement_var_decl(state, p):
        return ast.VarDeclaration([p[1].getstr()] + p[2].get_names(), srcpos=sr(p))

    @pg.production('var_decl : ')
    def var_decl_empty(state, p):
        return ast.VarDeclPartial([])

    @pg.production('var_decl : COMMA IDENTIFIER var_decl')
    def var_decl_identifier(state, p):
        return ast.VarDeclPartial([p[1].getstr()] + p[2].get_names())

    @pg.production('statement : IDENTIFIER ASSIGN expression SEMICOLON')
    def statement_identifier_assign_expr(state, p):
        return ast.Assignment(p[0].getstr(), p[2], srcpos=sr(p))

    @pg.production('statement : atom DOT IDENTIFIER ASSIGN expression SEMICOLON')
    def statement_setattr(state, p):
        return ast.Setattr(p[0], p[2].getstr(), p[4], srcpos=sr(p))

    @pg.production('statement : RETURN expression SEMICOLON')
    def statement_return(state, p):
        return ast.Return(p[1], srcpos=sr(p))

    @pg.production('statement : WHILE expression LEFT_CURLY_BRACE function_body'
                   ' RIGHT_CURLY_BRACE')
    def statement_while_loop(state, p):
        return ast.While(p[1], p[3].get_element_list(), srcpos=sr(p))

    @pg.production('statement : IF expression LEFT_CURLY_BRACE function_body'
                   ' RIGHT_CURLY_BRACE')
    def statement_if_block(state, p):
        return ast.If(p[1], p[3].get_element_list(), srcpos=sr(p))

    @pg.production('statement : RAISE expression SEMICOLON')
    def statement_raise(state, p):
        return ast.Raise(p[1], srcpos=sr(p))

    @pg.production('statement : TRY LEFT_CURLY_BRACE function_body '
                   'RIGHT_CURLY_BRACE except_finally_clauses')
    def statement_try_except(state, p):
        if p[4] is None:
            errorhandler(state, p[0])
        lst = p[4].gather_list()
        return ast.TryExcept(p[2].get_element_list(), lst, srcpos=sr([p[0], lst[-1]]))

    @pg.production('except_finally_clauses : ')
    def except_finally_clases_empty(state, p):
        return None

    @pg.production('except_finally_clauses : EXCEPT IDENTIFIER LEFT_CURLY_BRACE'
                   ' function_body RIGHT_CURLY_BRACE except_finally_clauses')
    def except_finally_clauses_except(state, p):
        # We want the position information for the clause, not the list.
        return ast.ExceptClauseList([p[1].getstr()], None,
                                    p[3].get_element_list(), p[5],
                                    srcpos=sr(p[:-1]))

    @pg.production('except_finally_clauses : EXCEPT IDENTIFIER AS IDENTIFIER '
                   'LEFT_CURLY_BRACE function_body RIGHT_CURLY_BRACE '
                   'except_finally_clauses')
    def except_finally_clauses_except_as_identifier(state, p):
        # We want the position information for the clause, not the list.
        return ast.ExceptClauseList([p[1].getstr()], p[3].getstr(),
                                    p[5].get_element_list(), p[7],
                                    srcpos=sr(p[:-1]))

    @pg.production('except_finally_clauses : FINALLY LEFT_CURLY_BRACE '
                   'function_body RIGHT_CURLY_BRACE')
    def except_finally_clauses_finally(state, p):
        return ast.FinallyClause(p[2].get_element_list(), srcpos=sr(p))

    @pg.production('identifier_list : COMMA IDENTIFIER identifier_list')
    def identifier_list_arglist(state, p):
        return ast.IdentifierListPartial(p[1].getstr(), p[2])

    @pg.production('identifier_list :')
    def rest_of_identifier_list_empty(state, p):
        return None

    @pg.production('dot_identifier_list : DOT IDENTIFIER dot_identifier_list')
    def dot_identifier_list_arglist(state, p):
        return ast.IdentifierListPartial(p[1].getstr(), p[2])

    @pg.production('dot_identifier_list :')
    def rest_of_dot_identifier_list_empty(state, p):
        return None

    @pg.production('arglist : LEFT_PAREN RIGHT_PAREN')
    def arglist(state, p):
        return ast.ArgList([], srcpos=sr(p))

    @pg.production('arglist : LEFT_PAREN IDENTIFIER var_decl RIGHT_PAREN')
    def arglist_non_empty(state, p):
        return ast.ArgList([p[1].getstr()] + p[2].get_names(), srcpos=sr(p))

    @pg.production('expression : INTEGER')
    def expression_number(state, p):
        return ast.Number(int(p[0].getstr()), srcpos=sr(p))

    @pg.production('expression : ST_STRING interpstr ST_ENDSTRING')
    def expression_string(state, p):
        strings = p[1].get_strings()
        if len(strings) == 1:
            return ast.String(strings[0], srcpos=sr(p))
        return ast.InterpString(strings, p[1].get_exprs(), srcpos=sr(p))

    @pg.production('expression : ST_RAW rawstringcontent ST_ENDRAW')
    def expression_rawstring(state, p):
        val = ''.join(p[1].get_strparts())
        str_decode_utf_8(val, len(val), 'strict', final=True)
        return ast.String(val, srcpos=sr(p))

    @pg.production('expression : LEFT_SQUARE_BRACKET expression_list RIGHT_SQUARE_BRACKET')
    def expression_list_literal(state, p):
        return ast.List(p[1].get_element_list(), srcpos=sr(p))

    @pg.production('expression : atom')
    def expression_atom(state, p):
        return p[0]

    @pg.production('expression : expression OR expression')
    def expression_or_expression(state, p):
        return ast.Or(p[0], p[2], srcpos=sr(p))

    @pg.production('expression : expression AND expression')
    def expression_and_expression(state, p):
        return ast.And(p[0], p[2], srcpos=sr(p))

    @pg.production('interpstr : stringcontent')
    def interpstr_start(state, p):
        val = ''.join(p[0].get_strparts())
        str_decode_utf_8(val, len(val), 'strict', final=True)
        return ast.InterpStringContents([val], [])

    @pg.production('interpstr : interpstr ST_INTERP expression RIGHT_CURLY_BRACE stringcontent')
    def interpstr_part(state, p):
        val = ''.join(p[4].get_strparts())
        str_decode_utf_8(val, len(val), 'strict', final=True)
        return ast.InterpStringContents(
            p[0].get_strings() + [val], p[0].get_exprs() + [p[2]])

    @pg.production('stringcontent : ')
    def string_empty(state, p):
        return ast.StringContent([])

    @pg.production('stringcontent : stringcontent ESC_QUOTE')
    def string_esc_quote(state, p):
        return ast.StringContent(p[0].get_strparts() + ['"'])

    @pg.production('stringcontent : stringcontent ESC_ESC')
    def string_esc_esc(state, p):
        return ast.StringContent(p[0].get_strparts() + ['\\'])

    @pg.production('stringcontent : stringcontent ESC_SIMPLE')
    def string_esc_simple(state, p):
        part = {
            'a': '\a',
            'b': '\b',
            'f': '\f',
            'n': '\n',
            'r': '\r',
            't': '\t',
            'v': '\v',
            '0': '\0',
            '$': '$',
        }[p[1].getstr()[1]]
        return ast.StringContent(p[0].get_strparts() + [part])

    @pg.production('stringcontent : stringcontent ESC_HEX_8')
    @pg.production('stringcontent : stringcontent ESC_HEX_16')
    def string_esc_hex_fixed(state, p):
        s = p[1].getstr()
        return ast.StringContent(p[0].get_strparts() + [hex_to_utf8(s[2:])])

    @pg.production('stringcontent : stringcontent ESC_HEX_ANY')
    def string_esc_hex_any(state, p):
        s = p[1].getstr()
        end = len(s) - 1
        assert end >= 0
        return ast.StringContent(p[0].get_strparts() + [hex_to_utf8(s[3:end])])

    @pg.production('stringcontent : stringcontent ESC_UNRECOGNISED')
    def string_esc_unrecognised(state, p):
        return ast.StringContent(p[0].get_strparts() + [p[1].getstr()])

    @pg.production('stringcontent : stringcontent CHAR')
    def string_char(state, p):
        return ast.StringContent(p[0].get_strparts() + [p[1].getstr()])

    @pg.production('rawstringcontent : ')
    def rawstring_empty(state, p):
        return ast.StringContent([])

    @pg.production('rawstringcontent : rawstringcontent RAW_ESC')
    @pg.production('rawstringcontent : rawstringcontent RAW_CHAR')
    def rawstring_char(state, p):
        return ast.StringContent(p[0].get_strparts() + [p[1].getstr()])

    @pg.production('atom : TRUE')
    def atom_true(state, p):
        return ast.TrueNode(srcpos=sr(p))

    @pg.production('atom : IDENTIFIER')
    def atom_identifier(state, p):
        return ast.Identifier(p[0].getstr(), srcpos=sr(p))

    @pg.production('atom : FALSE')
    def atom_false(state, p):
        return ast.FalseNode(srcpos=sr(p))

    @pg.production('atom : atom LEFT_PAREN expression_list '
                   'RIGHT_PAREN')
    def atom_call(state, p):
        return ast.Call(p[0], p[2].get_element_list(), srcpos=sr(p))

    @pg.production('atom : LEFT_PAREN expression RIGHT_PAREN')
    def atom_paren_expression_paren(state, p):
        return p[1]

    @pg.production('atom : atom DOT IDENTIFIER')
    def atom_dot_identifier(state, p):
        return ast.Getattr(p[0], p[2].getstr(), srcpos=sr(p))

    @pg.production('expression : expression PLUS expression')
    @pg.production('expression : expression MINUS expression')
    @pg.production('expression : expression STAR expression')
    @pg.production('expression : expression TRUEDIV expression')
    @pg.production('expression : expression LT expression')
    @pg.production('expression : expression EQ expression')
    def expression_lt_expression(state, p):
        return ast.BinOp(p[1].getstr(), p[0], p[2], sr([p[1]]), srcpos=sr(p))

    @pg.production('expression_list : ')
    def expression_list_empty(state, p):
        return ast.ExpressionListPartial([])

    @pg.production('expression_list : expression expression_sublist')
    def expression_list_expression(state, p):
        return ast.ExpressionListPartial([p[0]] + p[1].get_element_list())

    @pg.production('expression_sublist : ')
    def expression_sublist_empty(state, p):
        return ast.ExpressionListPartial([])

    @pg.production('expression_sublist : COMMA expression expression_sublist')
    def expression_sublist_expression(state, p):
        return ast.ExpressionListPartial([p[1]] + p[2].get_element_list())

    res = pg.build()
    if res.lr_table.sr_conflicts:
        raise Exception("shift reduce conflicts")
    return res
