import sqlglot


class parsed:
    """此类是将sql解释器转化为执行器易执行的工具类"""
    """目前可支持SELECT中的涉及大小关系判断及与或非关系符联结的where语句"""
    """目前可支持INSERT中的涉及多行插入的语句"""
    """目前可支持UPDATE中的多列值更新及where语句条件限制的语句"""
    """目前可支持DELETE中的where语句条件限制的语句"""
    def __init__(self, sql_statement):
        self.method = None
        self.object_column = []
        self.form_name = None
        self.where_condition=[]
        self.where_statement=None
        self.values_list = []
        par = sqlglot.parse_one(sql_statement)
        print(repr(par))
        if isinstance(par, sqlglot.exp.Select):
            self.method = "SELECT"
        elif isinstance(par, sqlglot.exp.Insert):
            self.method = "INSERT"
        elif isinstance(par, sqlglot.exp.Update):
            self.method = "UPDATE"
        elif isinstance(par, sqlglot.exp.Delete):
            self.method = "DELETE"
        elif isinstance(par,sqlglot.exp.Create):
            self.method = "CREATE"
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
            if(par.find(sqlglot.exp.From)!=None):
                self.form_name = par.args["from"].this.this.this
            # 提取where部分
            if (par.find(sqlglot.exp.Where)!=None):
                self.where_statement = par.args["where"]
                self.creat_where_condition(self.where_statement.this)
        if self.method == "INSERT":
            # 提取表名
            self.form_name = par.this.this.this.name
            # 提取列名列表
            self.object_column = [identifier.name for identifier in par.this.expressions]
            # 提取多行值的二维列表
            for tuple_exp in par.expression.expressions:
                row_values = [literal.this for literal in tuple_exp.expressions]
                self.values_list.append(row_values)
        if self.method == "UPDATE":
            #提取表名
            self.form_name = par.this.this.name
            #提取列名和对应更新值
            for eq_exp in par.expressions:
                column_name = eq_exp.this.this.name
                value = eq_exp.expression.this
                self.object_column.append(column_name)
                self.values_list.append(value)
            if (par.find(sqlglot.exp.Where)!=None):
                self.where_statement = par.args["where"]
                self.creat_where_condition(self.where_statement.this)
        if self.method == "DELETE":
            # 提取表名
            self.form_name = par.this.this.name
            if (par.find(sqlglot.exp.Where)!=None):
                self.where_statement = par.args["where"]
                self.creat_where_condition(self.where_statement.this)
        if self.method == "CREATE":
             return
    def where_stack(self):
        return self.where_condition
    def mtd(self):
        return self.method
    def o_col(self):
        return self.object_column
    def form(self):
        return self.form_name
    def value(self):
        return self.values_list
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
