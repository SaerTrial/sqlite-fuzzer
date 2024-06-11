# Implement your grammar here.
# This file should **only** contain the grammar stored
# in the `grammar` variable.
#https://sqlite.org/forum/info/c7a0c2a23231a27f

from fuzzingbook.Grammars import is_valid_grammar,trim_grammar, opts
import string
from fuzzingbook.Grammars import srange, extend_grammar
from fuzzingbook.GeneratorGrammarFuzzer import GeneratorGrammarFuzzer
from typing import Callable, Set, List, Dict, Optional, Iterator, Any, Union, Tuple, cast
import random
import copy as copy

Literal = [
    '123.0', '-123.1','-1,2147483648','2147483647', '2147483649', '-2147483647', '-2147483648',
    "'The'", "'first'", "'experiments'", "'in'", "'hardware'", "'fault'", "'injection'",
    "x'deadbeef'"
]

raw_Literal = [
    "'The'", "'first'", "'experiments'", "'in'", "'hardware'", "'fault'", "'injection'",
    b"\xde\xad\xbe\xef", 56.1, -56.1, 123456789.1234567899
]

UnaryOp = ['+', '-', 'NOT', '~']

BinaryOp = ['=','!=','>=','<=','>','<']

data_type = ['integer', 'real', 'text', 'blob']

CONTROLLED_CAPACITY = 20
SICK_CONTROLLED_CAPACITY = 512
def get_one_literal():
    chosen = random.choice(Literal)
    if isinstance(chosen, str):
        return chosen
    
    return str(chosen)

def get_more_literal():
    return "(" + ",".join(random.sample(Literal, random.randint(1,len(Literal)))) + ")"

def get_specified_literal(num):
    if num < 2:
        num = 2
    if num > len(Literal):
        extended_Literal = []
        extended_Literal += Literal
        for _ in range(num - len(Literal)):
            extended_Literal.append(f"'{random.randint(1,100)}'")
        return "(" + ",".join(random.sample(extended_Literal, num)) + ")"

    return "(" + ",".join(random.sample(Literal, num)) + ")"


def get_one_UaryOp():
    return random.choice(UnaryOp)

def get_one_data_type(expr):
    if type(expr) == str:
        return 'text'
    if type(expr) == int:
        return 'integer'
    if type(expr) == float:
        return 'real'
    return 'blob'

def get_one_BinaryOp():
    return random.choice(BinaryOp)

# Table management
VALID_TABLE = dict()
def define_valid_table(table_name):
    if table_name not in VALID_TABLE:
        VALID_TABLE[table_name] = []

# return one or more table name spaced by ","
def return_valid_table():
    if len(VALID_TABLE) == 0:
        return False

    #count = random.randint(1,len(VALID_TABLE))

    # if count == 1:
    #     return random.choice(list(VALID_TABLE.keys()))

    return random.choice(list(VALID_TABLE.keys()))

    #return ",".join(random.sample(list(VALID_TABLE.keys()), count))

    # return random.choice(list(VALID_TABLE.keys()))

# OPTIONAL_TABLE = [f"table_{name}" for name in [*string.ascii_lowercase[:6]]]
OPTIONAL_TABLE = [f"table_{name}" for name in range(CONTROLLED_CAPACITY)]

# column management

# VALID_COLUMN = [*string.ascii_lowercase[:6]]
VALID_COLUMN = [f"column_{name}" for name in range(CONTROLLED_CAPACITY)]

def result_column(at_least_one = False):
    count = random.randint(0,6)

    if not at_least_one:
        if count == 0:
            return "*"
    else:
        while count == 0:
            count = random.randint(0,6)

    return ",".join(random.sample(VALID_COLUMN, count))

def cast_handler(*args):
    chosen = random.choice(raw_Literal)

    if type(chosen) == int:
        return [str(chosen), 'integer']
    if type(chosen) == float:
        return [str(chosen), 'real']
    if type(chosen) == bytes:
        return ["x'deadbeef'", 'blob']
    if type(chosen) == str:
        return [chosen, 'text']
    
    return [None, None]




def table_constraint_handler(table_name, columns, constrains):

    define_valid_table(table_name)

    columns = result_column(True).split(",")
    column_dict = {}

    count = len(columns)
    index_primary_key = random.randint(1, count)
    count = 0

    # prepare a valid table to populate a pair of every single coumln and its type
    VALID_TABLE[table_name] = []

    for column in columns:

        # column name
        column_dict[column] = [column]
        count += 1

        # primary key
        if count == index_primary_key:
            column_dict[column].append("PRIMARY KEY")

        # type
        versatile_data_type = data_type.copy() + ["CHAR(50)"]
        column_dict[column].insert(1, random.choice(data_type))
        
        VALID_TABLE[table_name].append( (column,  column_dict[column][1]))

        if column_dict[column][-1] == 'real':
            column_dict[column].append(f"CHECK ({column} > 0)") 
        else:
            column_dict[column].append("NOT NULL")
    
    # sort the tuple of primary key in the first position in the associated list
    primary_key_val = VALID_TABLE[table_name][index_primary_key-1]
    del VALID_TABLE[table_name][index_primary_key-1]
    VALID_TABLE[table_name].insert(0, primary_key_val)


    final_expr = f"{table_name} ("
    for _, mix in column_dict.items():
        final_expr += (" ".join(mix) + " ,")
    final_expr = final_expr[:-1] + ")"
    return final_expr
    
def get_one_literal_val_by_type(column_type):
        if column_type == 'real':
            return random.choice(["-456,1", "456,0", "56.1", "-56.1", "123456789.1234567899", str(random.uniform(1.5, 1.9))])
        if column_type == 'integer':
            return random.choice(["-456", "456", "56", "-56", "123456789", "-123456789", str(random.randint(0,CONTROLLED_CAPACITY))])
        if column_type == 'text':
            return random.choice(["'The'", "'first'", "datetime('now')"])
        if column_type == 'blob':
            return "\xde\xad\xbe\xef"    
        return random.choice(Literal)   

def insert_handler(ignore_1, table_name, columns, values):
    if len(VALID_TABLE) == 0:
        return [None, random.choice(OPTIONAL_TABLE), ",".join(VALID_COLUMN), ",".join(Literal)]

    table_name = random.choice(list(VALID_TABLE.keys()))

    values = []
    columns = []
    for column, column_type in VALID_TABLE[table_name]:
        columns.append(column)
        values.append(get_one_literal_val_by_type(column_type))

        # if column_type == 'real':
        #     values.append(get_one_literal_val_by_type(column_type))
        # if column_type == 'integer':
        #     values.append(random.choice(["-456", "456", "56", "-56", "123456789", "-123456789"]))
        # if column_type == 'text':
        #     values.append(random.choice(["'The'", "'first'", "'experiments'", "'in'", "'hardware'", "'fault'", "'injection'"]))
        # if column_type == 'blob':
        #     values.append("\xde\xad\xbe\xef")          

    return [None, table_name, ",".join(columns), ",".join(values)]

def select_order_by_handler(ignore_1, columns, table_name, order_by):
    columns = []
    order_by = random.choice(['ASC', 'DESC', ''])
    
    if len(VALID_TABLE) == 0:
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), random.choice(OPTIONAL_TABLE), None, ",".join(VALID_COLUMN) + " " + order_by]

    sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))
    order_by_columns = random.sample(sub_columns, random.randint(1, len(sub_columns)))

    front_columns = []
    for column, _ in sub_columns: 
        front_columns.append(column)
    for column, _ in order_by_columns:
        columns.append(column)

    return [None, random.choice([",".join(front_columns), "*"]), table_name, None, ",".join(columns) + " " + order_by]

def select_where_in_handler(ignore_1, columns, table_name, column, expr_not, literal, limit):
    if len(VALID_TABLE) == 0:
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), random.choice(OPTIONAL_TABLE), random.choice(VALID_COLUMN), None, '(' + ','.join(random.choice(Literal)) + ')', None]
    
    sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))

    front_columns = []
    for column, _ in sub_columns: 
        front_columns.append(column)       
    
    column, col_type = random.choice(sub_columns)
    count = random.randint(1, 5)
    vals = []
    while count:
        vals.append(get_one_literal_val_by_type(col_type))
        count -= 1
    return [None, random.choice([",".join(front_columns), "*"]), table_name, column, None, '(' + ','.join(vals) + ')', None]

def select_where_binop_handler(ignore_1, columns, table_name, column, binOp, literal, limit):
    if len(VALID_TABLE) > 0:
        sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))
        front_columns = []
        for column, _ in sub_columns: 
            front_columns.append(column)       
        
        column, col_type = random.choice(sub_columns)
        literal = get_one_literal_val_by_type(col_type)
        return [None, random.choice([",".join(front_columns), "*"]), table_name, column, None, literal, None]
    else:
        table_name = random.choice(OPTIONAL_TABLE)
        column = random.sample(VALID_COLUMN, random.randint(1, len(VALID_COLUMN)))
        literal = get_one_literal_val_by_type(random.choice(data_type))
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), table_name, column, None, literal, None]


def select_where_is_null_handler(ignore_1, columns, table_name, column, is_null, limit):
    if len(VALID_TABLE) == 0:
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), random.choice(OPTIONAL_TABLE), random.choice(Literal), None, None]

    sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))
    front_columns = []
    for column, _ in sub_columns: 
        front_columns.append(column)   
    
    column, col_type = random.choice(sub_columns)

    return [None, random.choice([",".join(front_columns), "*"]), table_name, column, None, None]


def select_where_between_and_handler(ignore_1, columns, table_name, column, binOp, literal_1, literal_2, limit):
    if len(VALID_TABLE) == 0:
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), random.choice(OPTIONAL_TABLE), random.choice(VALID_COLUMN), None, random.choice(Literal), random.choice(Literal), None]

    sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))

    front_columns = []
    for column, _ in sub_columns: 
        front_columns.append(column)

    column, col_type = random.choice(sub_columns)

    literal_1 = get_one_literal_val_by_type(col_type)
    literal_2 = get_one_literal_val_by_type(col_type)

    return [None, random.choice([",".join(front_columns), "*"]), table_name, column, None, literal_1, literal_2, None]


def select_where_like_handler(ignore_1, columns, table_name, column, literal, limit):
    if len(VALID_TABLE) == 0:
        return [None, random.choice([",".join(VALID_COLUMN), "*"]), random.choice(OPTIONAL_TABLE), random.choice(VALID_COLUMN), None, random.choice(["'i%'", "'f%'", "'%'"]), None]
    
    sub_columns = random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name])))

    front_columns = []
    for column, _ in sub_columns: 
        front_columns.append(column)

    for column, col_type in sub_columns:
        if col_type == 'text':
            return [None, random.choice([",".join(front_columns), "*"]), table_name, column, None, random.choice(["'i%'", "'f%'", "'%'"]), None]


    column, col_type = random.choice(sub_columns)

    return [None, random.choice([",".join(front_columns), "*"]), table_name, "'A'", None, random.choice(["'a'", "'c'"]), None]
 

def select_multi_columns_handler():
    if len(VALID_TABLE) == 0:
        table_name = random.choice(OPTIONAL_TABLE)
        sub_columns = random.sample(VALID_COLUMN, 2)
    else:
        table_name = random.choice(list(VALID_TABLE.keys()))
        sub_columns = []
        for column, _ in  random.sample(VALID_TABLE[table_name], random.randint(1, len(VALID_TABLE[table_name]))):
            sub_columns.append(column)

        if len(sub_columns) < 2:
            sub_columns.append(random.choice(VALID_COLUMN))
    

    expr = """ || " " || """.join(sub_columns)   
    return f"SELECT {expr} as expr1 FROM {table_name}"   


def nested_handler(option, table_name):
    
    if option == 'like':
        res = select_where_like_handler(None, None, table_name, None, None, None)[-4:]
        like_expr = random.choice(['LIKE', 'NOT LIKE'])
        return f"{res[0]} {like_expr} {res[2]}"
    if option == 'in':
        res = select_where_in_handler(None, None, table_name, None, None, None, None)[-4:]
        return f"{res[0]} IN {res[2]}"
    if option == 'between':
        res = select_where_between_and_handler(None, None, table_name, None, None, None, None, None)[-5:]
        return random.choice([f"{res[0]} BETWEEN {res[2]} AND  {res[3]}", " 1.4 BETWEEN '1.3' AND 1.5"])
    if option == 'is_null':
        res = select_where_is_null_handler(None, None, table_name, None, None, None)[-3]
        return f"{res} IS NULL"
    if option == 'binop':
        res = select_where_binop_handler(None, None, table_name, None, None, None, None)[-4:]
        binOp = random.choice(BinaryOp)
        return f"{res[0]} {binOp} {res[2]}"

    

def select_where_expr(table_name):
    candidate_options = ['like', 'in', 'between', 'is_null', 'binop']
    chosen_candidates = random.sample(candidate_options, random.randint(2,len(candidate_options)))

    if len(VALID_TABLE) == 0:
        return [None, ','.join(VALID_COLUMN), random.choice(OPTIONAL_TABLE), '', None]


    columns = []
    for column, _ in VALID_TABLE[table_name]:
        columns.append(column)


    logicOp = ['AND', 'OR']
    # first one
    
    expr_list = []
    logicOp_list = [ random.choice(logicOp) for _ in range(len(chosen_candidates)-1)]
    
    for chosen_candidate in chosen_candidates:
        expr_list.append("( " + nested_handler(chosen_candidate, table_name) + ")")
        if len(logicOp_list) != 0:
            expr_list.append(logicOp_list.pop(0))

    nested_logic = random.choice([False, True])
    if nested_logic:
        expr_list.insert(0, '(')
        expr_list.insert(4, ')')

    return [None, ','.join(columns), table_name, ' '.join(expr_list), None]
    

def update_handler_1(table_name):
    if len(VALID_TABLE) > 0:
        name = random.choice(list(VALID_TABLE.keys()))
        columns = VALID_TABLE[name]
    else:
        name = random.choice(OPTIONAL_TABLE)
        columns = VALID_COLUMN
    c = random.choice(columns)
    return [None , name , c[0], None, None]

def update_handler_2(table_name):
    if len(VALID_TABLE) > 0:
        name = random.choice(list(VALID_TABLE.keys()))
        column = VALID_TABLE[name]
    else:
        name = random.choice(OPTIONAL_TABLE)
        column = random.choice(VALID_COLUMN)
        return [None , name , column, None, column, None, None]


    if len(column )== 1:
        c = column
        return [None , name , c[0][0], None, c[0][0],None,None]
    else:
        c = random.sample(column,2)
        return [None , name , c[0][0], None, c[1][0],None,None]

def alter_handler_1():
    if len(VALID_TABLE) > 0:
        name = random.choice(list(VALID_TABLE.keys()))
    else:
        name = random.choice(OPTIONAL_TABLE)
        new_name = name + '1'
        OPTIONAL_TABLE.append(new_name)
        return [name,new_name]

    new_name = name + '1'
    OPTIONAL_TABLE.append(new_name)
    VALID_TABLE[new_name] = VALID_TABLE.pop(name)
    return [name,new_name]

def alter_handler_2():
    if len(VALID_TABLE) > 0:
        name = random.choice(list(VALID_TABLE.keys()))
        c = VALID_TABLE[name]
    else:
        return [random.choice(OPTIONAL_TABLE), random.choice(VALID_COLUMN), random.choice(VALID_COLUMN)]

    item = random.choice(c)
    if isinstance(item, tuple):
        c_name, t = item 
    else:
        c_name = item 

    VALID_COLUMN.append(c_name + '1')
    c = list(map(lambda n: (c_name+'1', t) if n[0] == c_name else n, c))
    VALID_TABLE[name] = c
    return [name,c_name,c_name + '1']

def alter_handler_3():
    if len(VALID_TABLE) == 0:
        name = random.choice(OPTIONAL_TABLE)
        return [name, 'column_alter_' +random.choice(VALID_COLUMN)]
    name = random.choice(list(VALID_TABLE.keys()))
    index = random.randint(1,20)
    new_name = 'column_alter_' + str(index)
    VALID_COLUMN.append(new_name)
    VALID_TABLE[name].append((new_name, None))
    return [name,new_name]


def alter_handler_4():
    if len(VALID_TABLE) == 0:
        return [random.choice(OPTIONAL_TABLE), random.choice(VALID_COLUMN)]


    name = random.choice(list(VALID_TABLE.keys()))
    if len(VALID_TABLE[name]) == 1:
        return 
    
    item = random.choice(VALID_TABLE[name])
        
    
    if isinstance(item, tuple):
        c_name, t = item 
        if c_name in VALID_COLUMN:
            VALID_COLUMN.remove(c_name)
        VALID_TABLE[name].remove(item)

        # else:
        #     c_name = item 
        #     VALID_COLUMN.remove(c_name)
        #     VALID_TABLE[name].remove(c_name)
   


    return [name,c_name]


def create_trigger_handler(col_or_stmt, table_name):

    if len(VALID_TABLE) == 0:
        return [None, random.choice(OPTIONAL_TABLE), None, "WHERE 'A' LIKE 'a' "]  
    table_name = random.choice(list(VALID_TABLE.keys()))        

    sub_columns  = []
    for column, _ in VALID_TABLE[table_name]:
        sub_columns.append(column)



    count = random.choice([1, 2])

    final_expr = ' '
    while count:
        option = random.choice(['update',
        'insert',
        'delete',
        'select',
        'update'])

        if option == 'update':
            res = update_handler_1(table_name)
            value = random.choice(Literal)
            final_expr += f"UPDATE {res[1]} SET {res[2]} = {value} WHERE 'A' like 'a' ;"
        if option == 'insert':
            # random choice of a valid table, maybe buggy
            res = insert_handler(None, table_name, None, None)
            final_expr += f"INSERT INTO {res[1]} ({res[2]}) VALUES ({res[3]});"
        if option == 'select':
            res = select_where_expr(table_name)
            limit_option = random.choice(['LIMIT 1', ''])
            final_expr += f"SELECT {res[1]} from {table_name} WHERE {res[3]} {limit_option} ;"
        if option == 'delete':
            res = select_where_expr(table_name)
            final_expr += random.choice([f"DELETE FROM {table_name};", f"DELETE FROM {table_name} WHERE {res[3]} ;"])
        count -= 1
    
    if col_or_stmt:
        return [','.join(random.sample(sub_columns, random.randint(1, len(sub_columns)))), table_name, None, final_expr]
    else:
        return [None, table_name, None, final_expr]     
    

VALID_TRIGGER = []

OPTIONAL_TRIGGER = [f"trigger_{name}" for name in range(CONTROLLED_CAPACITY)]

def create_trigger_name():
    chosen = random.choice(OPTIONAL_TRIGGER)
    if chosen not in VALID_TRIGGER:
        VALID_TRIGGER.append(chosen)

    return chosen

def delete_trigger_handler():
    if len(VALID_TRIGGER) > 0:
        chosen = random.choice(VALID_TRIGGER)
    else:
        chosen = random.choice(OPTIONAL_TRIGGER)
    return chosen


VALID_VIEW = []

OPTIONAL_VIEW = [f"view_{name}" for name in range(CONTROLLED_CAPACITY)] 

def create_view_name():
    chosen = random.choice(OPTIONAL_VIEW)
    if chosen not in VALID_VIEW:
        VALID_VIEW.append(chosen)

    return chosen

def delete_view_handler():
    if len(VALID_VIEW) > 0:
        chosen = random.choice(VALID_VIEW)
    else:
        chosen = random.choice(OPTIONAL_VIEW)
    return chosen


VALID_INDEX = []

OPTIONAL_INDEX = [f"index_{name}" for name in range(CONTROLLED_CAPACITY)] 

def create_index_handler():
    if len(VALID_TABLE) > 0:
        table_name = random.choice(list(VALID_TABLE.keys()))
        sub_columns = [column for column, _ in VALID_TABLE[table_name]]
        res = select_where_expr(table_name)
        final_expr = f"SELECT {res[1]} from {table_name} WHERE {res[3]}  ;"
    else:
        table_name = random.choice(OPTIONAL_TABLE)
        sub_columns = VALID_COLUMN.copy()
        final_expr = ""
    chosen_index = random.choice(OPTIONAL_INDEX)
    if chosen_index not in VALID_INDEX:
        VALID_INDEX.append(chosen_index)
    else:
        chosen_index = random.choice(OPTIONAL_INDEX + [f"index_{name}" for name in [*string.digits]] )

    return [None, None, chosen_index, table_name, ','.join(sub_columns), final_expr]    

def drop_index_handler():
    if len(VALID_INDEX) > 0:
        chosen = random.choice(VALID_INDEX)
    else:
        chosen = random.choice(OPTIONAL_INDEX)
    return [None, chosen]
    
def drop_table_handler():
        if len(VALID_TABLE) == 0:
            return 'DROP TABLE IF EXISTS ' + random.choice(OPTIONAL_TABLE) 
        name = random.choice(list(VALID_TABLE.keys()))
        del VALID_TABLE[name]
        if random.choice([True, False]):
            return 'DROP TABLE ' + name
        else:
            return 'DROP TABLE IF EXISTS ' + name 

def delete_table_handler():
        if len(VALID_TABLE) > 0:
            name = random.choice(list(VALID_TABLE.keys()))
            # del VALID_TABLE[name]
        else:
            name = random.choice(OPTIONAL_TABLE)
            
        return [None, name]
         
def delete_table_handler2():
        if len(VALID_TABLE) > 0:
            table_name = random.choice(list(VALID_TABLE.keys()))
            sub_columns = [column for column, _ in VALID_TABLE[table_name]]
            #res = select_where_expr(table_name)
        else:
            table_name = random.choice(OPTIONAL_TABLE)
            sub_columns = VALID_COLUMN.copy()
            res = ['', '', '', "WHERE 'A' like 'a' "]

        return [None, table_name, random.choice(['()' + ','.join(sub_columns) + ')', '']), None, None, table_name, None]

OPTIONAL_SICK_COULMN = [f"sick_column_{name}" for name in range(SICK_CONTROLLED_CAPACITY)]
OPTIONAL_SICK_TABLE = [f"sick_table_{name}" for name in range(SICK_CONTROLLED_CAPACITY)]
OPTIONAL_SICK_INDEX = [f"sick_index_{name}" for name in range(SICK_CONTROLLED_CAPACITY)] 

def create_sick_table_handler():
    columns = ",".join(OPTIONAL_SICK_COULMN)
   
    table_name = random.choice(OPTIONAL_SICK_TABLE)
         
    # case one: create one table with a buntch of columns
    option = random.choice([True, False])
    if not option:
        return f"CREATE TABLE {table_name} ({columns})"
    
    # case two: create a buntch of table
    final_expr = ""
    column = random.choice(OPTIONAL_SICK_COULMN)
    for sick_table_name in OPTIONAL_SICK_TABLE:
        final_expr += f"CREATE TABLE {sick_table_name}({column}); "
    return final_expr

def create_sick_index_handler():
    if len(VALID_TABLE) > 0:
            table_name = random.choice(list(VALID_TABLE.keys()))
            columns = [column for column, _ in VALID_TABLE[table_name]]
    else:
            table_name = random.choice(OPTIONAL_TABLE)
            columns = VALID_COLUMN.copy()
    
    
    # case one: one index pointing to a buntch of columns
    option = random.choice([True, False])
    if not option:

        index = random.choice(OPTIONAL_INDEX)
        all_cols = ",".join(columns)
        return f"CREATE INDEX {index} ON {table_name}({all_cols})"

    # case two: a buntch of indexs for a column
    final_expr = ""
    column = random.choice(columns)
    for index in OPTIONAL_SICK_INDEX:
        final_expr += f"CREATE INDEX {index} ON {table_name}({column}); "
    return final_expr

# create a sick table then insert sick values
def create_sick_insert_and_order_by_handler():
    columns = ",".join(OPTIONAL_SICK_COULMN)
    values = []
    for _ in range(SICK_CONTROLLED_CAPACITY):
        values.append(random.choice(Literal))

    values = ",".join(values)
    sick_table_name = random.choice(OPTIONAL_SICK_TABLE)
    final_expr = ""
    final_expr += f"CREATE TABLE {sick_table_name}({columns}); "
    final_expr += f"INSERT INTO {sick_table_name}({columns}) VALUES ({values}); "
    final_expr += f"SELECT {columns} FROM {sick_table_name} ORDER BY {columns}; "
    return final_expr

OPTIONAL_DATABASE = [f"database_{name}" for name in range(5)]
OPTIONAL_SICK_DATABASE = [f"sick_database_{name}" for name in range(SICK_CONTROLLED_CAPACITY)]

def create_sick_database_handler():

    final_expr = ""
    for db in OPTIONAL_SICK_DATABASE:
        final_expr += f"CREATE DATABASE {db} ;"
    
    return final_expr

def select_cross_join_handler():
    table_name = 'cross_join_' + random.choice(OPTIONAL_TABLE)
    table_name_2 = 'cross_join2_' + random.choice(OPTIONAL_TABLE)
    initial_state = f"CREATE TABLE {table_name}(ID, NAME, AGE, ADDRESS, SALARY); CREATE TABLE {table_name_2} (ID INT PRIMARY KEY NOT NULL,DEPT CHAR(50) NOT NULL, EMP_ID INT NOT NULL);"
    populate_state = f"""
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (1, 'Paul', 32, 'California', 20000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (2, 'Allen', 25, 'Texas', 15000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (3, 'Allen3', 25, 'Norway', 20000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (4, 'Allen4', 25, 'Rich-Mond', 65000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (5, 'Allen5', 40, 'Texas', 85000.0);
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (1, 'IT Billing', 1 );
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (2, 'Engineering', 2 );
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (3, 'Finance', 7 );
    SELECT EMP_ID, NAME, DEPT FROM {table_name} CROSS JOIN {table_name_2};
    """
    return initial_state + populate_state

def select_outer_join_handler():
    join_type = random.choice(['LEFT', 'RIGHT', 'FULL'])
    table_name = 'outer_join_' + random.choice(OPTIONAL_TABLE)
    table_name_2 = 'outer_join2_' + random.choice(OPTIONAL_TABLE)
    initial_state = f"CREATE TABLE {table_name}(ID, NAME, AGE, ADDRESS, SALARY); CREATE TABLE {table_name_2} (ID INT PRIMARY KEY NOT NULL,DEPT CHAR(50) NOT NULL, EMP_ID INT NOT NULL);"
    populate_state = f"""
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (1, 'Paul', 32, 'California', 20000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (2, 'Allen', 25, 'Texas', 15000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (3, 'Allen3', 25, 'Norway', 20000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (4, 'Allen4', 25, 'Rich-Mond', 65000.0);
    INSERT INTO {table_name}(ID, NAME, AGE, ADDRESS, SALARY) VALUES (5, 'Allen5', 40, 'Texas', 85000.0);
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (1, 'IT Billing', 1 );
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (2, 'Engineering', 2 );
    INSERT INTO {table_name_2} (ID, DEPT, EMP_ID) VALUES (3, 'Finance', 7 );
    SELECT EMP_ID, NAME, DEPT FROM {table_name} {join_type} OUTER JOIN {table_name_2} ON {table_name}.ID = {table_name_2}.EMP_ID;
    """
    return initial_state + populate_state

def insert_returning_clause_handler():
        if len(VALID_TABLE) > 0:
            table_name = random.choice(list(VALID_TABLE.keys()))
            sub_columns = [column for column, _ in VALID_TABLE[table_name]]
        else:
            table_name = random.choice(OPTIONAL_TABLE)
            sub_columns = random.sample(VALID_COLUMN, random.randint(1, len(VALID_COLUMN)))
    
        values = []
        for _ in range(len(sub_columns)):
            values.append("random()")
        sub_columns = ",".join(sub_columns)
        values = ",".join(values)
        return f"INSERT INTO {table_name}({sub_columns}) VALUES ({values}) RETURNING *"

def select_collate_handler():
    table_name = 'collate_' + random.choice(OPTIONAL_TABLE)
    initial_state = f"""
CREATE TABLE {table_name}(
coln INTEGER PRIMARY KEY,
cola,              
colb COLLATE BINARY, 
colc COLLATE RTRIM,   
cold COLLATE NOCASE);
"""
    collating_function = random.choice(['BINARY', 'NOCASE', 'RTRIM'])
    select_stmt = ''
    if collating_function == 'RTRIM':
        select_stmt = f"SELECT coln FROM {table_name} WHERE cola = colb COLLATE rtrim ORDER BY coln;"
    if collating_function == 'NOCASE':
        select_stmt = f"SELECT coln FROM {table_name} ORDER BY colc COLLATE NOCASE, coln;"
    if collating_function == 'BINARY':
        select_stmt = f"SELECT coln FROM {table_name} WHERE cola = colb ORDER BY coln;"

    return initial_state + select_stmt

def cte_stmt_handler_with():
    table_name = 'cte_' + random.choice(OPTIONAL_TABLE)
    return [table_name, None, None, None, None, None, None, table_name]

def cte_stmt_handler_with2():
    table_name = 'cte_' + random.choice(OPTIONAL_TABLE)
    return [table_name,None, None, None, table_name]

def cte_stmt_handler_with3():
    table_name = 'cte_' + random.choice(OPTIONAL_TABLE)
    return [table_name, table_name, table_name, table_name, table_name, table_name]

def cte_stmt_update_or_delete():
    if len(VALID_TABLE) > 0:
        table_name = random.choice(list(VALID_TABLE.keys()))
        sub_columns = [column for column, _ in VALID_TABLE[table_name]]
    else:
        table_name = random.choice(OPTIONAL_TABLE)
        sub_columns = random.sample(VALID_COLUMN, random.randint(1, len(VALID_COLUMN)))
    
    cte_table_name = 'cte_' + table_name
    columns = ','.join(sub_columns)
    one_col = random.choice(sub_columns)
    values = get_specified_literal(len(sub_columns))
    values2 = get_specified_literal(len(sub_columns))
    update_stmt = f"""
UPDATE {table_name}
SET ({columns}) = (
    SELECT {columns}
    FROM {cte_table_name} WHERE {table_name}.id = {cte_table_name}.{one_col}
)
WHERE {one_col} IN (SELECT {one_col} FROM {cte_table_name});
"""
    delete_stmt = f"""
DELETE FROM {table_name}
WHERE {one_col} IN (SELECT {one_col} FROM {cte_table_name});
"""
    cte_stmt = f"WITH {cte_table_name}({columns}) AS ( VALUES {values} {values2} ) "
    
    if random.choice([True, False]):
        return cte_stmt + update_stmt
    else:
        return cte_stmt + delete_stmt

def create_indexed_by_handler():
    table_name = "indexed_by_" + random.choice(OPTIONAL_TABLE)
    if random.choice([True, False]):
        return [table_name,table_name,table_name,table_name, f'idx_Price_{table_name}',table_name, table_name,f'idx_Price_{table_name}']
    else:
        return [table_name,table_name,table_name,table_name,f'idx_Price_{table_name}',table_name, table_name,f'idx_PriceError_{table_name}']
 

grammar  = {
"<start>": ["<create_table_stmt>", "<select_core>", "<insert_stmt>",
               "<update_stmt>", 
                "<alter_table_stmt>",
                "<create_trigger_stmt>",
                "<drop_trigger_stmt>",
                "<drop_view_stmt>",
                "<create_view_stmt>",
                "<create_index_stmt>",
                "<drop_index_stmt>",
                "<drop_table_stmt>",
                "<pragma_stmt>",
                "<delete_stmt>",
                "<reindex_stmt>",
                "<vacuum_stmt>",
                "<savepoint_stmt>",
                "<release_stmt>",
                "<analyze_stmt>",
                "<create_virtual_table_stmt>",
                "<explain_stmt>",
                "<maybe_crash_stmt>",
                "<json_stmt>",
                "<create_database>",
                "<attach_stmt>",
                "<detach_stmt>",
                "<cte_stmt>"],

'<create_database>':[
    (' ', opts(pre=lambda: "CREATE DATABASE " + random.choice(OPTIONAL_DATABASE) + ";")),
],

'<attach_stmt>': [
    "ATTACH DATABASE '' AS aux2", 
    "ATTACH DATABASE 'file::memory:?cache=shared' AS aux1;"
],

'<detach_stmt>':[
      (' ', opts(pre=lambda: "DETACH DATABASE " + random.choice(OPTIONAL_DATABASE) + ";")),
],

"<expr>": [
    "<literal_value> <literal_value> <literal_value>",
    ("<expr> IS NULL", opts(pre=lambda: random.choice(VALID_COLUMN) + random.choice([" IS NULL", " IS NOT NULL"]))),
    "<unary_operator> <expr>",
    "<expr> <binary_operator> <expr>",
    ("CAST ( <expr> AS <type_name> )", opts(post=cast_handler)),
    ("<expr> <expr_not> IN <expr>", opts(post=lambda column, not_flag, values: [random.choice(VALID_COLUMN), None, get_more_literal()])),
    ("<expr>", opts(post=lambda expr: abs(expr) if isinstance(expr, int) or isinstance(expr, float) else False)),
    ("<expr>", opts(post=lambda expr: hex(expr) if isinstance(expr, int) or isinstance(expr, float) else False)),
    ("<expr>", opts(post=lambda expr: len(expr) if isinstance(expr, str) else False)),
    ("<expr>", opts(post=lambda expr: str.lower(expr) if isinstance(expr, str) else False)),
    ("<expr>", opts(post=lambda expr: str.upper(expr) if isinstance(expr, str) else False)),
    ("<expr>", opts(post=lambda expr: str.upper(expr) if isinstance(expr, str) else False)),
    ("<expr>", opts(post=lambda expr: get_one_data_type(expr))),
    "CASE WHEN <expr> THEN <expr> ELSE <expr> END", 
    ("<expr> <expr_not> BETWEEN <expr> AND <expr>", opts(post=lambda column, not_flag, literal, literal_2: [random.choice(VALID_COLUMN), None, get_one_literal(), get_one_literal()])), 
    

],

"<unary_operator>":[
    ("", opts(pre=lambda: random.choice(UnaryOp)))
],

"<binary_operator>":[
    ("", opts(pre= lambda: random.choice(BinaryOp)))
],

"<type_name>":[
   ("", opts(pre=lambda: random.choice(data_type))) 
],

"<literal_value>":[
("literal_value>", opts(pre=get_one_literal)),
],

"<expr_not>":[
    "", 
    "NOT"
],

'<cte_stmt>':[
    ("WITH <table_name>(c1, c2, c3) AS (VALUES (<literal_value>, <literal_value>, <literal_value>), (<literal_value>, <literal_value>, <literal_value>)) select * from <table_name>", opts(post=lambda t1, t2, t3, t4, t5, t6, t7, t8: cte_stmt_handler_with())),
    ("WITH <table_name>(c1, c2, c3) AS (SELECT <literal_value>, <literal_value>, <literal_value>) select * from <table_name>", opts(post=lambda t1, t2, t3, t4, t5: cte_stmt_handler_with2())),
    ("CREATE TABLE <table_name> ( bar INTEGER ); INSERT INTO <table_name> VALUES(1); INSERT INTO <table_name> VALUES(2); WITH <table_name>CTE AS (SELECT * FROM <table_name>) SELECT * FROM <table_name>CTE;", opts(post=lambda t1, t2, t3, t4, t5, t6: cte_stmt_handler_with3())),
    ('cte delete or update', opts(pre=cte_stmt_update_or_delete)),
],


'<select_core>':[
    '<select_core_where>'
    '<select_core_order_by> <select_core_limit>',
    'SELECT <select_core_1> <select_core_result_column> <select_core_from> <select_core_group_by> <select_core_limit>',
    'SELECT <select_core_1> * <select_core_from> <select_core_limit>',
    '<select_core> UNION <select_core>',
    '<select_core_avg_sum>',
    '<select_core_having>',
    '<select_multi_columns>',
    '<select_join>',
    '<select_collate>',
],

'<select_collate>':[
    ('', opts(pre=select_collate_handler)),
],

'<select_join>':[
    ('cross join', opts(pre=select_cross_join_handler)),
    ('outer join', opts(pre=select_outer_join_handler)),
    '<select_core_inner_join>',
],

'<select_multi_columns>':[
    ('', opts(pre=select_multi_columns_handler)),
],

'<select_core_avg_sum>':[
    "CREATE TABLE test_avg(trackid INTEGER PRIMARY KEY, name TEXT, albumid INTEGER, milliseconds REAL); INSERT INTO test_avg(trackid, name, albumid, milliseconds) VALUES(1, 'test1', 4, 20.65); INSERT INTO test_avg(trackid, name, albumid, milliseconds) VALUES(2, 'test2', 5, 30.22); SELECT round(avg(test),1) FROM (SELECT SUM(milliseconds) as test FROM test_avg GROUP BY albumid ) ;",
],

'<select_core_inner_join>':[
    """
CREATE TABLE t1(ProductID INTEGER PRIMARY KEY, ProductName TEXT, CategoryID INTEGER, Price REAL); 
INSERT INTO t1(ProductID, ProductName, CategoryID, Price) VALUES(1, 'Chais', 1, 20.65); 
INSERT INTO t1(ProductID, ProductName, CategoryID, Price) VALUES(2, 'Chang', 1, 19.20); 
INSERT INTO t1(ProductID, ProductName, CategoryID, Price) VALUES(3, 'Aniseed Syrup', 2, 6.87); 
CREATE TABLE t2(CategoryID INTEGER PRIMARY KEY, CategoryName TEXT, Description TEXT); 
INSERT INTO t2(CategoryID, CategoryName, Description) VALUES(1, 'Chais123', '123'); 
INSERT INTO t2(CategoryID, CategoryName, Description) VALUES(2, 'Chais456', '456'); 
INSERT INTO t2(CategoryID, CategoryName, Description) VALUES(3, 'Chais789', '789'); 
SELECT ProductID, ProductName, CategoryName FROM t1 INNER JOIN t2 ON t1.CategoryID = t2.CategoryID;
""",
"""
CREATE TABLE t3(ProductID INTEGER PRIMARY KEY, ProductName TEXT, CategoryID INTEGER, Price REAL); 
INSERT INTO t3(ProductID, ProductName, CategoryID, Price) VALUES(1, 'Chais', 1, 20.65); 
INSERT INTO t3(ProductID, ProductName, CategoryID, Price) VALUES(2, 'Chang', 1, 19.20); 
INSERT INTO t3(ProductID, ProductName, CategoryID, Price) VALUES(3, 'Aniseed Syrup', 2, 6.87); 
CREATE TABLE t4(CategoryID INTEGER PRIMARY KEY, CategoryName TEXT, Description TEXT); 
INSERT INTO t4(CategoryID, CategoryName, Description) VALUES(1, 'Chais123', '123'); 
INSERT INTO t4(CategoryID, CategoryName, Description) VALUES(2, 'Chais456', '456'); 
INSERT INTO t4(CategoryID, CategoryName, Description) VALUES(3, 'Chais789', '789'); 
SELECT ProductID, ProductName, CategoryName FROM t3 INNER JOIN t4 USING (CategoryID);
""",

],

'<select_core_having>':[
    """
    CREATE TABLE test_having(ProductID INTEGER PRIMARY KEY, ProductName TEXT, CategoryID INTEGER, Price REAL); 
    INSERT INTO test_having(ProductID, ProductName, CategoryID, Price) VALUES(1, 'Chais', 1, 20.65); 
    INSERT INTO test_having(ProductID, ProductName, CategoryID, Price) VALUES(2, 'Chang', 1, 19.20); 
    INSERT INTO test_having(ProductID, ProductName, CategoryID, Price) VALUES(3, 'Aniseed Syrup', 2, 6.87); 
    SELECT 
        ProductID,
        SUM(Price) AS Price
    FROM test_having
    GROUP BY Price
    HAVING SUM(Price) > 10;
    """
],

'<select_core_limit>':[
    'LIMIT 1',
    ''
],

'<select_core_1>':[
    '',
    'DISTINCT',
    'ALL'
],

'<select_core_result_column>':[
    ('', opts(pre=result_column))
],


'<select_core_from>':[
    'from <select_core_from_table>'
],

'<select_core_from_table>':[
    ('', opts(pre=return_valid_table)),
],

'<select_core_where>':[
    ('SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <nested_expr> <select_core_limit>', 
    opts(post=lambda ignore_1, columns, table_name, nested_expr, limit: select_where_expr(table_name))),
    ('SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <literal_value> <expr_not> LIKE <literal_value> <select_core_limit>', 
    opts(post=lambda ignore_1, columns, table_name, column, expr_not, literal, limit: select_where_like_handler(ignore_1, None, table_name, column, literal, limit))),
    ('SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <literal_value> <binary_operator> <literal_value> <select_core_limit>', 
    opts(post=lambda ignore_1, columns, table_name, column, binOp, literal, limit: select_where_binop_handler(ignore_1, columns, table_name, column, binOp, literal, limit))),
    ('SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <literal_value> <expr_not> IN <literal_value> <select_core_limit>', 
    opts(post=lambda ignore_1, columns, table_name, column, expr_not, literal, limit: select_where_in_handler(ignore_1, columns, table_name, column, expr_not, literal, limit))),
    ('SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <literal_value> <select_core_is_null> <select_core_limit>',
    opts(post=lambda ignore_1, columns, table_name, column, is_null, limit: select_where_is_null_handler(ignore_1, columns, table_name, column, is_null, limit))),
    ("SELECT <select_core_1> <column_def_list> from <select_core_from_table> WHERE <expr> <expr_not> BETWEEN <expr> AND <expr> <select_core_limit>", 
    opts(post=lambda ignore_1, columns, table_name, column, expr_not, literal_1, literal_2, limit: select_where_between_and_handler(ignore_1, columns, table_name, column, expr_not, literal_1, literal_2, limit))),
],

'<select_core_is_null>':[
  'IS NULL',
  'IS NOT NULL'
  ''
],

'<nested_expr>':
[
    ''
],

 '<select_core_group_by>':[
   '',
  ('GROUP BY <select_core_group_by_expr>')
],

 '<select_core_group_by_expr>':[
     ('', opts(pre=result_column))
 ],

'<select_core_order_by>':[
     ('SELECT <select_core_1> <select_core_result_column> FROM <select_core_from_table> <select_core_order_by_where> ORDER BY <select_core_order_by_idle>', opts(post=lambda ignore_1, columns, table_name, where, order_by: select_order_by_handler(ignore_1, columns, table_name, order_by))),
],

'<select_core_order_by_where>':[
    ' ',
    'WHERE 1 IN (random(), random(), random())'
],

'<select_core_order_by_idle>':[
    ''
],


'<create_table_stmt>':[
    'CREATE <create_table_stmt_1> TABLE <create_table_stmt_2> <create_table_stmt_3>  <create_table_stmt_4>',
    # complex creation
    "CREATE TABLE contact_groups(contact_id INTEGER, group_id INTEGER, PRIMARY KEY (contact_id, group_id), FOREIGN KEY (contact_id) REFERENCES contacts (contact_id) ON DELETE CASCADE ON UPDATE NO ACTION, FOREIGN KEY (group_id) REFERENCES groups (group_id) ON DELETE CASCADE ON UPDATE NO ACTION);",
    "<create_table_col_dependent_expr>",
    # 'CREATE <create_table_stmt_1> TABLE <create_table_stmt_2> <table_name> <create_table_stmt_3>'
],

'<create_table_col_dependent_expr>':["""
CREATE TABLE col_dependent_expr_<table_name>( 
  buy_id INTEGER NOT NULL, 
  stock_id INTEGER DEFAULT 1, 
  investor_id INTEGER DEFAULT 1, 
  broker_id INTEGER DEFAULT 1, 
  unit INTEGER, 
  price REAL DEFAULT 100.2, 
  date TEXT, 
  cost REAL GENERATED ALWAYS AS (unit*price), 
  brokage REAL GENERATED ALWAYS AS (CASE broker_id WHEN 1 THEN 9 WHEN 3 THEN 28 END),
  PRIMARY KEY (buy_id, stock_id, investor_id, broker_id), 
  FOREIGN KEY (stock_id) REFERENCES stock(stock_id) ON DELETE CASCADE ON UPDATE NO ACTION, 
  FOREIGN KEY (investor_id) REFERENCES stock(investor_id) ON DELETE CASCADE ON UPDATE NO ACTION 
  FOREIGN KEY (broker_id) REFERENCES stock(broker_id) ON DELETE CASCADE ON UPDATE NO ACTION
);
"""
],


'<create_table_stmt_1>':[
    '',
    'TEMP',
    'TEMPORARY'
],

'<create_table_stmt_2>':[
    '',
    'IF NOT EXISTS'
],


'<create_table_stmt_3>':[
    #'AS <select_stmt>',
    (' <table_name>  ( <column_def_list> <table_constraint_list> )', opts(post=lambda table_name, columns, constraints: table_constraint_handler(table_name, columns, constraints)))
],

'<column_def_list>':[
    ''
],


'<table_constraint_list>':[
    ''
],

'<create_table_stmt_4>':[
    '',
    'WITHOUT ROWID'
],

'<table_name>':[
    '<table_name_candidate>'
],

'<table_name_candidate>':[
    ('', opts(pre=lambda:random.choice( list( set(OPTIONAL_TABLE) - set(VALID_TABLE.keys()) ))  if set(OPTIONAL_TABLE) != set(VALID_TABLE.keys()) and set(VALID_TABLE.keys()).issubset(set(OPTIONAL_TABLE)) else random.choice(OPTIONAL_SICK_TABLE) )),
],


'<insert_stmt>':[
    '<create_table_stmt>',
    ('<insert_stmt_1> <table_name> ( <insert_stmt_column> ) VALUES <insert_stmt_values>', opts(post=lambda stmt1, table, columns, values: insert_handler(stmt1, table, columns, values)))
],

'<insert_stmt_1>':[
    'REPLACE INTO',
    'INSERT <insert_stmt_patch>',
    '<insert_returning_stmt>',
],

'<insert_returning_stmt>':[
    ('insert returning', opts(pre=insert_returning_clause_handler)),
],


'<insert_stmt_patch>':[
    ' INTO',
    ' OR ABORT INTO',
    ' OR FAIL INTO',
    ' OR IGNORE INTO',
    ' OR REPLACE INTO',
    ' OR ROLLBACK INTO',

],

'<insert_stmt_column>':[
    ''
],

'<insert_stmt_values>':[
    ''
],


"<update_stmt>": [("UPDATE <update_stmt_or> <table_name> SET <column_name> = <expr> <update_stmt_where>", opts(post=lambda update_or,table_name,c,e,w:update_handler_1(table_name))),
                  ("UPDATE <update_stmt_or> <table_name> SET <column_name> = <expr>, <column_name> = <expr> <update_stmt_where>", opts(post=lambda o, table_name,c1,e1,c2,e2,w:update_handler_2(table_name)))
                  ],

"<column_name>": [""],
"<update_stmt_or>": [ "", "OR ROLLBACK" , "OR ABORT" , "OR REPLACE" , "OR FAIL" , "OR IGNORE"],
"<update_stmt_where>" : ["", "WHERE <expr>" ],


'<alter_table_stmt>':[
    ('ALTER TABLE <table_name> RENAME TO <new_table_name>', opts(post=lambda table_name, new_name: alter_handler_1())), 
    ('ALTER TABLE <table_name> RENAME <column_name> TO <new_column_name>',opts(post=lambda table_name, c1, c2: alter_handler_2())), 
    ('ALTER TABLE <table_name> RENAME COLUMN <column_name> TO <new_column_name>', opts(post=lambda table_name, c1, c2: alter_handler_2())),
    ('ALTER TABLE <table_name> ADD <column_def>', opts(post=lambda name,d:alter_handler_3())),
    ('ALTER TABLE <table_name> ADD COLUMN <column_def>',opts(post=lambda name,d:alter_handler_3())),
    ('ALTER TABLE <table_name> DROP <column_def>', opts(post=lambda name, c:alter_handler_4())),
    ('ALTER TABLE <table_name> DROP COLUMN <column_def>',opts(post=lambda name, c:alter_handler_4())),
],


'<drop_table_stmt>':[
    'DROP TABLE <table_name>', 
    'DROP TABLE IF EXISTS <table_name>', 
    ('DROP TABLE <table_name>', opts(pre = drop_table_handler) ),
    ('DROP TABLE IF EXISTS <table_name>', opts(pre = drop_table_handler) )
],

'<pragma_stmt>':[
    "PRAGMA journal_mode=WAL"
    "PRAGMA journal_mode=WAL",
    "PRAGMA journal_mode=DELETE",
],


'<create_trigger_stmt>':[
    'CREATE <trigger_stmt_tmp> TRIGGER <trigger_stmt_if_not_exist> <trigger_name> <trigger_stmt_list_1> <create_trigger_statefulness>',
],

'<trigger_name>':[
    ('', opts(pre=lambda: create_trigger_name()))
],

'<trigger_stmt_tmp>':
[
    '',
    'TEMP',
    'TEMPORARY'
],

'<trigger_stmt_list_5>':[
    '',
    ('WHEN <expr>', opts(pre=lambda: random.choice(["WHEN 'A' LIKE 'a'", "WHEN column_a IN (1,2,3)"]))),
    'FOR EACH ROW',
    ('FOR EACH ROW WHEN <expr>', opts(pre=lambda: random.choice(["FOR EACH ROW WHEN 'A' LIKE 'a'", "FOR EACH ROW WHEN column_a IN (1,2,3)"]))),
],


'<trigger_stmt_if_not_exist>':[
    '',
    'IF NOT EXISTS',
],


'<trigger_stmt_list_2>':[
    'DELETE',
    'INSERT',
    'UPDATE',
    #'UPDATE OF <column_name_list>' # decouple it
],

'<trigger_stmt_list_1>':[
    '',
    'BEFORE',
    'AFTER',
    'INSTEAD OF'
],

'<create_trigger_statefulness>':[
    ('<trigger_stmt_list_2> ON <table_name> <trigger_stmt_list_5> BEGIN <trigger_stmt_list> END', opts(post=lambda stmt, table_name, stmt_5, trigger_stmt: create_trigger_handler(False, table_name))),
    ('UPDATE OF <column_name_list> ON <table_name> <trigger_stmt_list_5> BEGIN <trigger_stmt_list> END', opts(post=lambda stmt, table_name, stmt_5, trigger_stmt: create_trigger_handler(True, table_name))),
],


'<trigger_stmt_list>':[
    ''
],


'<drop_trigger_name>':[
    ('', opts(pre=lambda: delete_trigger_handler())),
],

'<drop_trigger_stmt>':[
    'DROP TRIGGER <drop_trigger_stmt_1> <drop_trigger_name>'
],

'<drop_trigger_stmt_1>':[
    '',
    'IF EXISTS'
],




'<create_view_stmt>':[
    'CREATE <create_view_stmt_1> VIEW <create_view_stmt_2> <view_name> <create_view_stmt_3> AS <select_core>',
],

'<view_name>':[
    ('', opts(pre=lambda: create_view_name())),
],

'<create_view_stmt_3>':[
    ('(<column_name_list>)', opts(pre=lambda: ",".join(random.sample(VALID_COLUMN, random.randint(1, len(VALID_COLUMN)))))),
    ''
],

'<create_view_stmt_1>':[
    'TEMP',
    'TEMPORARY',
    ''
],

'<create_view_stmt_2>':[
    'IF NOT EXISTS',
    ''
],

'<drop_view_stmt>':[
    'DROP TRIGGER <drop_view_stmt_1> <drop_view_name>'
],

'<drop_view_name>':[
    ('', opts(pre=lambda: delete_view_handler())),
],

'<drop_view_stmt_1>':[
    '',
    'IF EXISTS'
],

'<create_index_stmt>':[
('CREATE <create_index_stmt_1> INDEX <create_index_stmt_2> <index_name> ON <table_name> <indexed_column_list> <create_index_stmt_5>', opts(post=lambda stmt1, stmt2, index_name, table_name, columns, expr: create_index_handler())),
'<create_indexed_by>',
],


'<create_indexed_by>':[
("""
CREATE TABLE <table_name>(ProductID INTEGER PRIMARY KEY, ProductName TEXT, CategoryID INTEGER, Price REAL); 
INSERT INTO <table_name>(ProductID, ProductName, CategoryID, Price) VALUES(random(), 'Chais', 1, 20.65); 
INSERT INTO <table_name>(ProductID, ProductName, CategoryID, Price) VALUES(random(), 'Chang', 1, 19.20); 
INSERT INTO <table_name>(ProductID, ProductName, CategoryID, Price) VALUES(random(), 'Aniseed Syrup', 2, 6.87); 
CREATE INDEX <index_name> ON <table_name>(Price);
SELECT * FROM <table_name> INDEXED BY <index_name> WHERE Price > 10;
""", opts(post=lambda t1,t2,t3,t4,t5,t6,t7,t8:create_indexed_by_handler())),
],

'<create_index_stmt_1>':[
    '',
    'UNIQUE'
],

'<create_index_stmt_2>':[
    '',
    'IF NOT EXISTS'
],


'<create_index_stmt_5>':[
    '',
    'WHERE <expr>'
],


'<drop_index_stmt>':[
    ('DROP INDEX <drop_index_stmt_1> <index_name>', opts(post=lambda stmt1, stmt2: drop_index_handler())),
],

'<drop_index_stmt_1>':[
    '',
    'IF EXISTS'
],

'<delete_stmt>':[
    ('DELETE FROM <qualified_table_name> <delete_stmt_2>', opts(post=lambda table_name, expr: delete_table_handler())),
    ('DELETE FROM <qualified_table_name> <delete_stmt_2> RETURNING *', opts(post=lambda table_name, expr: delete_table_handler())),
    (' <delete_stmt_1>  <table_name> <column_name_list> <common_table_expression_middle> <select_core> DELETE FROM <qualified_table_name> <delete_stmt_2>', opts(post=lambda delete_stmt_1, table_name, columns, middle, select_core, qualified_table_name, expr: delete_table_handler2())),
    (' <delete_stmt_1>  <table_name> <column_name_list> <common_table_expression_middle> <select_core> DELETE FROM <qualified_table_name> <delete_stmt_2> RETURNING *', opts(post=lambda delete_stmt_1, table_name, columns, middle, select_core, qualified_table_name, expr: delete_table_handler2())),
],

'<delete_stmt_1>':[
    'WITH ',
    'WITH RECURSIVE'
],

'<delete_stmt_2>':[
    '',
    "WHERE 'A' like 'a' ",
],

# '<common_table_expression>':[
#     '<table_name> AS ( <select_core> )',
#     '<table_name> ( <column_name_list> )AS ( <select_core> )',
#     '<table_name> ( <column_name_list> )AS NOT MATERIALIZED ( <select_core> )'
# ],

'<common_table_expression_middle>':[
    'AS',
    'AS NOT MATERIALIZED'
],


'<reindex_stmt>':[
    'REINDEX ',
    'REINDEX <reindex_stmt_1> ',
    'REINDEX <reindex_stmt_1> '
],

'<reindex_stmt_1>':[
    ('<table_name>', opts(pre=lambda: random.choice(list(VALID_TABLE.keys())  if len(list(VALID_TABLE.keys())) !=0 else  random.choice(OPTIONAL_TABLE)   ))),
    ('<index_name>', opts(pre=lambda: random.choice(OPTIONAL_INDEX) if len(VALID_INDEX) == 0 else random.choice(VALID_INDEX)))
],

'<vacuum_stmt>':[
    'VACUUM <vacuum_stmt_2>'
],

'<vacuum_stmt_2>':[
    '',
    ('INTO <filename>', opts(post=lambda filename: ''.join([random.choice(string.ascii_letters) for _ in range(random.randint(1, 20))])))
],

'<create_virtual_table_stmt>':[
    "CREATE VIRTUAL TABLE mail USING fts5(sender, title, body, tokenize = 'porter ascii');"
],

# '<rollback_stmt>': [
# 'ROLLBACK',
# 'ROLLBACK TRANSACTION',
# 'ROLLBACK TRANSACTION TO <savepoint_name>',
# 'ROLLBACK TRANSACTION TO SAVEPOINT <savepoint_name>',
# 'ROLLBACK TO SAVEPOINT <savepoint_name>',
# 'ROLLBACK TO <savepoint_name>'
# ],

'<savepoint_stmt>':[
    'SAVEPOINT <savepoint_name>'
],


'<release_stmt>':[
    'RELEASE <savepoint_name>',
    'RELEASE SAVEPOINT <savepoint_name>',
],

'<savepoint_name>':[
    *string.ascii_lowercase[:6],
],

'<explain_stmt>':[
    'EXPLAIN <select_core>',
    'EXPLAIN  QUERY PLAN <select_core>'
],

'<analyze_stmt>': [
    'ANALYZE',
    ('ANALYZE <table_name>', opts(post=lambda table_name: [random.choice(OPTIONAL_TABLE) if len(list(VALID_TABLE.keys())) ==0 else random.choice(list(VALID_TABLE.keys()))])),
    ('ANALYZE <index_name>', opts(post=lambda index_name: [random.choice(OPTIONAL_INDEX) if len(VALID_INDEX) ==0 else random.choice(VALID_INDEX)])),
],

'<maybe_crash_stmt>':[
    ('', opts(pre=create_sick_table_handler)), # create a table with 8192 columns
    ('',opts(pre=create_sick_index_handler)), # one index for a buntch of cols or a buntch of index
    ('',opts(pre=create_sick_insert_and_order_by_handler)), # insert a buntch of value and select order by
    ('',opts(pre=create_sick_database_handler)), # create a buntch of database
    "PRAGMA synchronous=OFF", # https://www.sqlite.org/howtocorrupt.html
    "PRAGMA user_version = integer", # change version may go crashed
    "BEGIN TRANSACTION; CREATE TABLE t_journal(a,b,c); INSERT INTO t_journal(a,b,c) VALUES(1,2,3); PRAGMA journal_mode=MEMORY; COMMIT;", # don't change journel mode in the middle of write transaction
    "BEGIN TRANSACTION; CREATE TABLE t_journal2(a,b,c); INSERT INTO t_journal2(a,b,c) VALUES(1,2,3); PRAGMA journal_mode=OFF; COMMIT;" # don't change journel mode in the middle of write transaction

],

'<json_stmt>':[
    "CREATE TABLE user(name,phone); SELECT DISTINCT user.name FROM user, json_each(user.phone) WHERE json_each.value LIKE '704-%';",
    "CREATE TABLE user1(name,phone); SELECT name FROM user1 WHERE phone LIKE '704-%' UNION SELECT user1.name FROM user1, json_each(user1.phone) WHERE json_valid(user1.phone) AND json_each.value LIKE '704-%';",
    "CREATE TABLE big(json JSON); SELECT big.rowid, fullkey, value FROM big, json_tree(big.json) WHERE json_tree.type NOT IN ('object','array');",
    "CREATE TABLE big1(json JSON); SELECT DISTINCT json_extract(big1.json,'$.id') FROM big1, json_tree(big1.json, '$.partlist') WHERE json_tree.key='uuid' AND json_tree.value='6fa5181e-5721-11e5-a04e-57f3d7b32808';",
    """CREATE TABLE users (id INTEGER PRIMARY KEY, data JSON);  INSERT INTO users (id, data) VALUES (1, json_encode({"name": "Alice","age": 25,"email": "alice@example.com"}));""",
    "SELECT json_array ( 1, 2, 3 ) AS user;",
    """SELECT json_type ( '{"ID":1,"Name":"Forgotten in the Planet","Year":1970}', '$.Year' ) AS property_type;""",
    """SELECT json_array_length ( '{"Genre":["Comedy","Crime"],"Cast":["Adrian Gratianna","Tani O''Hara","Tessie Delisle"]}', '$.Cast' ) AS array_length;""",
    """SELECT json_object ( 'ID', 1, 'Name', 'Forgotten in the Planet' ) AS result;""",
    """SELECT json_insert ( '{"ID":1,"Name":"Forgotten in the Planet","Year":1970}', '$.Director', 'Henrie Randell Githens' ) AS insert_movie;""",
    """SELECT json_remove ( '{"ID":1,"Name":"Forgotten in the Planet","Year":1970,"Director":"Henrie Randell Githens"}', '$.Director' ) AS result_of_remove;""",
    """SELECT json_remove ('{"x":25,"y":42}','$') AS result_of_remove;""",
    """SELECT json_replace ( '{"ID":1,"Name":"Forgotten in the Planet","Year":1970,"Director":"Henrie Randell Githens"}', '$.Year', 1971 ) AS result_of_replace;""",
    """SELECT json_valid ( '{"ID":1,"Name":"Forgotten in the Planet","Year":1970,"Director":"Henrie Randell Githens"}' ) AS result_of_valid;""",
    """CREATE TABLE movies ( data TEXT );""",
    """UPDATE movies SET data = json_set('{"a":2,"c":4}', '$.a', 99);""",
    """UPDATE movies SET data = json_patch('{"a":[1,2],"b":2}','{"a":9}');""",
    """UPDATE movies SET data = json_valid('{"x":35') → 0; UPDATE movies SET data = json_quote('verdant') → '"verdant"'; """,
    """UPDATE movies SET data = json_replace ( data, '$.Name', 'Found in the Universe' ) WHERE json_extract ( data, '$.ID' ) = 1; UPDATE movies SET data = json_insert ( data, '$.Country', 'USA' ) WHERE json_extract ( data, '$.ID' ) = 1; UPDATE movies SET data = json_remove ( data, '$.Runtime' ) WHERE json_extract ( data, '$.ID' ) = 1; SELECT json_extract ( data, '$.Name' ) FROM movies WHERE json_extract ( data, '$.ID' ) = 1;""",
],



"<filename>":[""],
"<qualified_table_name>":[""],
"<index_name>":[""],
"<indexed_column_list>":[""],
"<column_name_list>": [""],
'<column_def>':[""],
"<new_table_name>":[""],
"<new_column_name>":[""],

}



# grammar = extend_grammar(grammar, {
#     "<assignment>": [("<identifier>=<expr>",
#                       opts(post=lambda id, expr: define_id(id)))]
# })


#grammar = trim_grammar(grammar)
assert is_valid_grammar(grammar)
# cur_fuzzer = GeneratorGrammarFuzzer(grammar, start_symbol="<start>")
# for _ in range(1000000):
#     print(cur_fuzzer.fuzz())

# for table, values in VALID_TABLE.items():
#     print(table, values)
# Considerations:
# statefullness, a valid command may be rejected because of database state