#!/usr/bin/env python
class Banana:

    def eat(self):
        pass


class Person:

    def __init__(self):
        self.no_bananas()

    def no_bananas(self):
        self.bananas = []

    def add_banana(self, banana):
        self.bananas.append(banana)

    def eat_bananas(self):
        [banana.eat() for banana in self.bananas]
        self.no_bananas()


def main():
    person = Person()
    for a in range(10):
        person.add_banana(Banana())
    person.eat_bananas()

if __name__ == '__main__':
    # 在原来的调用逻辑前添加下面这五行
    from pycallgraph import PyCallGraph
    from pycallgraph.output import GraphvizOutput
    graphviz = GraphvizOutput()
    graphviz.output_file = 'basic.png'# 保存的文件名
    with PyCallGraph(output=graphviz):
        main() # 原来的主函数逻辑
