import sqlglot


class parsed:
    """此类是将sql解释器转化为执行器易执行的工具类"""
    method = None
    object_column = []
    from_form = None
    where_condition=[]
    where_statement=None

    def __init__(self, sql_statement):
        par = sqlglot.parse_one(sql_statement)
        if isinstance(par, sqlglot.exp.Select):
            self.method = "SELECT"
        elif isinstance(par, sqlglot.exp.Insert):
            self.method = "INSERT"
        elif isinstance(par, sqlglot.exp.Update):
            self.method = "UPDATE"
        elif isinstance(par, sqlglot.exp.Delete):
            self.method = "DELETE"
        else:
            self.method = "UNKNOWN"
        # SELECT方法
        if self.method == "SELECT":
            # 提取列名
            select_expressions = par.selects
            for expr in select_expressions:
                if isinstance(expr, sqlglot.expressions.Star):
                    self.object_column.append('*')
                else:
                    self.object_column.append(expr.sql())
            # 提取所需表名
            self.from_form = par.args["from"].this.this.this
            # 提取where部分
            self.where_statement = par.args["where"]
            self.creat_where_condition(self.where_statement.this)
    def where_stack(self):
        return self.where_condition
    def mtd(self):
        return self.method
    def o_col(self):
        return self.object_column
    def form(self):
        return self.from_form
    def creat_where_condition(self,where_statement_part):
        condition=where_statement_part
        if isinstance(condition, sqlglot.expressions.EQ):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('=')
        elif isinstance(condition, sqlglot.expressions.GT):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('>')
        elif isinstance(condition, sqlglot.expressions.GTE):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('>=')
        elif isinstance(condition, sqlglot.expressions.LT):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('<')
        elif isinstance(condition, sqlglot.expressions.LTE):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('<=')
        elif isinstance(condition, sqlglot.expressions.NEQ):
            self.where_condition.append(condition.this.this.this)
            self.where_condition.append(condition.expression.this)
            self.where_condition.append('!=')
        elif isinstance(condition, sqlglot.expressions.And):
            self.creat_where_condition(condition.this)
            self.creat_where_condition(condition.expression)
            self.where_condition.append('and')
        elif isinstance(condition, sqlglot.expressions.Or):
            self.creat_where_condition(condition.this)
            self.creat_where_condition(condition.expression)
            self.where_condition.append('or')
        elif isinstance(condition, sqlglot.expressions.Not):
            self.creat_where_condition(condition.this)
            self.where_condition.append('not')
        elif isinstance(condition, sqlglot.expressions.Paren): #括号
            self.creat_where_condition(condition.this)
            if condition.expression:
                self.creat_where_condition(condition.expression)
        else:
            print(type(condition))
            self.where_condition.append('UNKNOWN')
        return
