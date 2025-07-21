import sqlglot


class Parsed:
    """此类是将sql解释器转化为执行器易执行的工具类"""
    """目前可支持SELECT中的涉及大小关系判断及与或非关系符联结的where语句"""
    """目前可支持INSERT中的涉及多行插入的语句"""
    """目前可支持UPDATE中的多列值更新及where语句条件限制的语句"""
    """目前可支持DELETE中的where语句条件限制的语句"""

    def __init__(self, sql_statement):
        self.method = None
        self.object_column = []
        self.form_name = None
        self.where_condition = []
        self.where_statement = None
        self.values_list = []
        self.join_tables = []  # 存储所有join的表
        self.column_methods = []  # 存储列操作方法（如sum、groupby等）
        self.column_table_index = []  # 存储列所属的表的索引
        self.join_methods = []  # 存储列操作方法（如natural join等）
        self._parse_sql(sql_statement)

    def _parse_sql(self, sql_statement):
        par = sqlglot.parse_one(sql_statement)
        #print(repr(par))
        if isinstance(par, sqlglot.exp.Select):
            self.method = "SELECT"
        elif isinstance(par, sqlglot.exp.Insert):
            self.method = "INSERT"
        elif isinstance(par, sqlglot.exp.Update):
            self.method = "UPDATE"
        elif isinstance(par, sqlglot.exp.Delete):
            self.method = "DELETE"
        elif isinstance(par, sqlglot.exp.Create):
            self.method = "CREATE"
        else:
            self.method = "UNKNOWN"

        # 解析SELECT语句
        if self.method == "SELECT":
            self._parse_select(par)

        # 解析INSERT语句
        if self.method == "INSERT":
            self._parse_insert(par)

        # 解析UPDATE语句
        if self.method == "UPDATE":
            self._parse_update(par)

        # 解析DELETE语句
        if self.method == "DELETE":
            self._parse_delete(par)


    def _parse_insert(self, par):
        # 提取表名
        self.form_name = par.this.this.this.name

        # 提取列名列表
        self.object_column = [identifier.name for identifier in par.this.expressions]

        # 提取多行值的二维列表
        for tuple_exp in par.expression.expressions:
            row_values = [literal.this for literal in tuple_exp.expressions]
            self.values_list.append(row_values)

    def _parse_update(self, par):
        # 提取表名
        self.form_name = par.this.this.name

        # 提取列名和对应更新值
        for eq_exp in par.expressions:
            column_name = eq_exp.this.this.name
            value = eq_exp.expression.this
            self.object_column.append(column_name)
            self.values_list.append(value)

        # 提取WHERE部分
        if par.find(sqlglot.exp.Where) is not None:
            self.where_statement = par.args["where"]
            self.creat_where_condition(self.where_statement.this)

    def _parse_delete(self, par):
        # 提取表名
        self.form_name = par.this.this.name

        # 提取WHERE部分
        if par.find(sqlglot.exp.Where) is not None:
            self.where_statement = par.args["where"]
            self.creat_where_condition(self.where_statement.this)

    def _parse_joins(self, joins):
        if joins:  # 确保joins不为空
            if isinstance(joins, list):  # 如果joins是一个列表，进行迭代
                for join in joins:
                    # 记录JOIN表
                    self.join_tables.append(join.this.this.this)

                    # 记录JOIN类型（如natural、inner等）
                    join_type = join.method
                    # 只在列操作方法中记录聚合操作，不记录JOIN方法
                    self.join_methods.append(join_type)
            else:
                # 如果不是列表，尝试处理其他类型
                print(f"Unexpected join structure: {joins}")
        else:
            print("No valid joins found.")

    def _get_table_index(self, table_name):
        # 返回表在表列表中的索引
        if table_name in self.join_tables:
            return self.join_tables.index(table_name) + 1  # JOIN表的索引从1开始
        elif table_name == self.form_name:
            return 0  # FROM表的索引为0
        else:
            return -1  # 如果找不到该表，返回-1

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

    def join_tables_list(self):
        """返回所有参与JOIN的表"""
        return self.join_tables

    def column_methods_list(self):
        """返回列对应的操作方法列表"""
        return self.column_methods

    def join_methods_list(self):
        """返回列对应的操作方法列表"""
        return self.join_methods

    def column_table_index_list(self):
        """返回列所属的表的索引列表"""
        return self.column_table_index

    def creat_where_condition(self, where_statement_part):
        condition = where_statement_part
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
        elif isinstance(condition, sqlglot.expressions.Paren):  # 括号
            self.creat_where_condition(condition.this)
            if condition.expression:
                self.creat_where_condition(condition.expression)
        else:
            print(type(condition))
            self.where_condition.append('UNKNOWN')
        return
    
    def _parse_select(self, par):
        # 提取列名和操作方法（例如SUM）
        select_expressions = par.selects
        for expr in select_expressions:
            if isinstance(expr, sqlglot.expressions.Star):
                self.object_column.append('*')
                self.column_methods.append(None)
            else:
                # 判断列是否有聚合方法
                if isinstance(expr, sqlglot.expressions.Func):
                    if isinstance(expr, sqlglot.expressions.Sum):
                        self.column_methods.append("sum")
                    elif isinstance(expr, sqlglot.expressions.Avg):
                        self.column_methods.append("average")
                    elif isinstance(expr, sqlglot.expressions.Max):
                        self.column_methods.append("max")
                    elif isinstance(expr, sqlglot.expressions.Min):
                        self.column_methods.append("min")
                    elif isinstance(expr, sqlglot.expressions.Count):
                        self.column_methods.append("count")
                    else:
                        self.column_methods.append(None)
                    column_name = expr.this.this.this
                    self.object_column.append(column_name)
                else:
                    column_name = expr.this.this
                    self.object_column.append(column_name)
                    self.column_methods.append(None)
         # 提取表名
        if par.find(sqlglot.exp.From) is not None:
            self.form_name = par.args["from"].this.this.this

        # 提取JOIN信息
        if par.find(sqlglot.exp.Join) is not None:
            self._parse_joins(par.args["joins"])
        
        # 解析GROUP BY部分
        if par.find(sqlglot.exp.Group) is not None:
            groupby_columns = par.args["group"].expressions
            self._parse_groupby(groupby_columns)

        # 提取WHERE部分
        if par.find(sqlglot.exp.Where) is not None:
            self.where_statement = par.args["where"]
            self.creat_where_condition(self.where_statement.this)

        # ...existing code...

    def _parse_groupby(self, groupby_columns):
        """解析GROUP BY列"""
        for column in groupby_columns:
            if isinstance(column, sqlglot.expressions.Column):
                groupby_column_name = column.sql()
                self.object_column.append(groupby_column_name)
                self.column_methods.append("groupby")  # 统一用小写


# 示例SQL语句（可以根据需要修改）
#sql_statement = """
#SELECT SUM(A), B FROM data natural join data1 GROUP BY C,D WHERE B < 4 
"""
print(sql_statement)
# 初始化Parsed对象并解析SQL语句
parsed_obj = Parsed(sql_statement)

# 获取列名
print("列名：", parsed_obj.o_col())

# 获取列对应的操作方法（例如：SUM，GROUP BY等）
print("列操作方法：", parsed_obj.column_methods_list())

# 获取表名
print("FROM表名：", parsed_obj.form())

# 获取JOIN表列表
print("JOIN表列表：", parsed_obj.join_tables_list())

print("join操作方法：", parsed_obj.join_methods_list())
# 获取WHERE条件
print("WHERE条件：", parsed_obj.where_stack())

# 获取列所属的表的索引列表
print("列所属表的索引：", parsed_obj.column_table_index_list())
"""
