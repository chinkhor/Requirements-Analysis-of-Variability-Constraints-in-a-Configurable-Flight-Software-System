import pandas as pd
import numpy as np
import re

class RTWToFM:
    
    def __init__(self):
        self.elements = {}
        self.XML = ""
        self.generateTemplateElement()
        self.struct = ""
        self.constraint = ""
        self.root = None
        self.data = None
    
    def reset(self):
        self.elements = {}
        self.XML = ""
        self.generateTemplateElement()
        self.struct = ""
        self.constraint = ""
        self.root = None
        
    def update(self, showTag):
        self.reset()
        self.processInput(self.data, showTag)

    def processInput(self, table, showTag):
        self.data = table
        for index, row in self.data.iterrows():
            if row['valid'] == 0:
                continue
                
            placeholder = {}
            count = 1
            logic = row['logic']
            
            for feature in row['abstract'] + row['concrete']:
                if not self.isPresent(feature):
                    element = Element(name=feature)
                    element.valid = 1
                    element.setId(row['id'])
                    self.elements[feature] = element
   
                placeholder[str(count)] = feature
                logic = self.replace_matches(logic, feature, str(count))
                count += 1
                
            if row['rule'] == 'R1' and logic.lower() == 'root':
                root = self.getElementByName(feature)
                self.root = root
                root.setTagName("and")
                root.setMandatory()
                continue   
            
            if row['rule'] == 'R7':
                self.generateXMLConstraint(row['id'], logic, placeholder, showTag)
                continue
    
            self.processLogic(logic, row['rule'], placeholder)
            
            for feature in row['abstract'] + row['concrete']:
                element = self.getElementByName(feature)
                if not element.hasChild() and feature in row['concrete']:
                    element.setTagName("feature")
                    element.setVoid()
                if element.hasChild():
                    element.unVoid()
                if feature in row['abstract']:
                    element.setAbstract()
                
        
    def isPresent(self, name):
        return True if self.getElementByName(name) else False
        
    def processLogic(self, logic, rule, placeholder):
        if rule == 'R2':
            logic = logic.split('IFF')
            parent = self.getElementByName(placeholder.get(logic[0].strip()))
            parent.setTagName("and")
            child = self.getElementByName(placeholder.get(logic[1].strip()))
            child.setMandatory()
            parent.addChild(child)
            child.setParent(parent)
            
        elif rule == 'R3':
            logic = logic.split('IMPLY')
            parent = self.getElementByName(placeholder.get(logic[1].strip()))
            parent.setTagName("and")
            child = self.getElementByName(placeholder.get(logic[0].strip()))
            parent.addChild(child)
            child.setParent(parent)
            
        elif rule == 'R4':
            logic = logic.split("IFF")
            var1 = logic.pop(self.findParentIndex(logic)).strip()
            parent = self.getElementByName(placeholder.get(var1))
            parent.setTagName("alt")
            logic = logic[0].split("OR")
            var_arr = re.findall(r'\d+', logic[0])
            for var in var_arr:
                child = self.getElementByName(placeholder.get(var))
                parent.addChild(child)
                child.setParent(parent)
            
        elif rule == 'R5':
            logic = logic.split("IFF")
            var1 = logic.pop(self.findParentIndex(logic)).strip()
            parent = self.getElementByName(placeholder.get(var1))
            parent.setTagName("or")
            var_arr = re.findall(r'\d+', logic[0])
            for var in var_arr:
                child = self.getElementByName(placeholder.get(var))
                parent.addChild(child)
                child.setParent(parent)
            
        elif rule == 'R6':
            if logic.find("IFF") < logic.find("IMPLY"):
                split_index = logic.rfind('AND')
                front = "IFF"
                back = "IMPLY"
            else:
                split_index = logic.find('AND')
                front = "IMPLY"
                back = "IFF"
                
            clause1 = logic[:split_index].strip()
            clause2 = logic[split_index + 3:].strip()
            clause1 = clause1.rstrip(")").lstrip("(").split(front)
            clause2 = clause2.rstrip(")").lstrip("(").split(back)
            
            var1 = clause1.pop(self.findParentIndex(clause1)).strip()
            var2 = clause2.pop(self.findParentIndex(clause2)).strip()
            
            parent1 = self.getElementByName(placeholder.get(var1))
            parent1.setTagName("and")
            parent2 = self.getElementByName(placeholder.get(var2))
            parent2.setTagName("and")
            var_arr1 = re.findall(r'\d+', clause1[0])
            var_arr2 = re.findall(r'\d+', clause2[0])
            for var in var_arr1:
                child = self.getElementByName(placeholder.get(var))
                parent1.addChild(child)
                child.setParent(parent1)
                if front == "IFF":
                    child.setMandatory()
                
            for var in var_arr2:
                child = self.getElementByName(placeholder.get(var))
                parent2.addChild(child)
                child.setParent(parent2)
                if back == "IFF":
                    child.setMandatory()
    
    def replace_matches(self, string, target, sub):
        pattern = r"\b" + re.escape(target) + r"\b"
        matches = re.finditer(pattern, string) 
        new_string = string
        reduce = 0
        for match in matches:
            new_string = new_string[0:match.span()[0]-reduce] + sub + new_string[match.span()[1]-reduce:]
            reduce += (len(target) - 1)
            
        return new_string
            
            
    def generateXMLStruct(self, root):
        children = root.getChildren()

        self.struct += root.generateStartTag() + "\n"
        for child in children:
            self.generateXMLStruct(root=child)
        
        self.struct += root.generateEndTag() + "\n"
       
    def generateXMLConstraint(self, ID, logic, placeholder, showTag):
        self.constraint += "<rule> \n"
        
        if not showTag:
            tagContent = ""
        else:
            tagContent = "Constraint Requirement ID: " + ID
            
        self.constraint += "<tags>" + tagContent + "</tags> \n"
        self.constraint += "<imp> \n"
        logic = logic.split("IMPLY")
        
        var1 = logic.pop(0).strip()
        
        self.constraint += "<var>" + placeholder.get(var1) + "</var>\n"
        if self.isCNF(logic[0]):
            self.constraint += "<conj>\n"
            logic = logic[0].split("AND")
            
            for clause in logic:
                if "OR" in clause:
                    self.handleDisjunction(clause, placeholder)
                else:
                    self.constraint += "<var>" + placeholder.get(clause.strip()) + "</var>\n"
                    
            self.constraint += "</conj>\n"
            
        elif self.isDNF(logic[0]):
            self.constraint += "<disj>\n"
            
            logic = logic[0].split("OR")
            
            for clause in logic:
                if "AND" in clause:
                    self.handleConjunction(clause, placeholder)
                else:
                    self.constraint += "<var>" + placeholder.get(clause.strip()) + "</var>\n"
                    
            self.constraint += "</conj>\n"
            
        else:
            clause = logic[0].strip()
            if "AND" in clause:
                self.handleConjunction(clause, placeholder)
                
            elif "OR" in clause:
                self.handleDisjunction(clause, placeholder)
            else:
                self.constraint += "<var>" + placeholder.get(clause) + "</var>\n"
                
        self.constraint += "</imp> \n" 
        self.constraint += "</rule> \n"
        
    def handleConjunction(self, clause, placeholder):
        clause = clause.split("AND")
        self.constraint += "<conj>\n"
        for var in clause:
            literal = re.search(r'\d+', var).group()
            if "NOT" in var:
                self.constraint += "<not>\n"
                self.constraint += "<var>" + placeholder.get(literal) + "</var>\n"
                self.constraint += "</not>\n"
            else:
                self.constraint += "<var>" + placeholder.get(literal) + "</var>\n"
                            
        self.constraint += "</conj>\n"
        
    def handleDisjunction(self, clause, placeholder):
        clause = re.findall(r'\d+', clause)
        self.constraint += "<disj>\n"
        for var in clause:
            self.constraint += "<var>" + placeholder.get(var) + "</var>\n"
        self.constraint += "</disj>\n"
    
    def isCNF(self, logic):
        if '(' in logic:
            while '(' in logic and ')' in logic:
                left = logic.find("(")
                right = logic.find(")")
                logic = logic[:left] + "a" + logic[right+1:]
                
        return "AND" in logic
        
    def isDNF(self, logic):
        if '(' in logic:
            while '(' in logic and ')' in logic:
                left = logic.find("(")
                right = logic.find(")")
                logic = logic[:left] + "a" + logic[right+1:]
                
        return "OR" in logic
    
    def findParentIndex(self, var_arr: list):
        min_len_index = 0
        var_num = float('inf')
        for i in range(len(var_arr)):
            count = len(re.findall(r'\d+', var_arr[i]))
            if count < var_num:
                min_len_index = i
                var_num = count
        return min_len_index
    
    def getElementByName(self, name):        
        if name in self.elements:
            return self.elements.get(name)
        return None
    
    def generateTemplateElement(self):
        template = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n\
                    <featureModel>\n\
                    \t<properties>\n\
                    \t\t<graphics key="autolayoutconstraints" value="false"/> \n\
                    \t\t<graphics key="legendposition" value="1223,200"/> \n\
                    \t\t<graphics key="legendautolayout" value="false"/> \n\
                    \t\t<graphics key="showconstraints" value="true"/> \n\
                    \t\t<graphics key="showshortnames" value="false"/> \n\
                    \t\t<graphics key="layout" value="horizontal"/> \n\
                    \t\t<graphics key="showcollapsedconstraints" value="true"/> \n\
                    \t\t<graphics key="legendhidden" value="false"/> \n\
                    \t\t<graphics key="layoutalgorithm" value="1"/> \n\
                    \t</properties> \n\
                    \t<struct> </struct> \n\
                    \t<constraints> </constraints> \n\
                    </featureModel>'
        
        self.XML += template
        
    def generateXMLFile(self, fileName):        
        self.generateXMLStruct(self.root)
        insert_struct_index = self.XML.find("<struct>") + 8
        self.XML = self.XML[:insert_struct_index] + "\n" + self.struct + self.XML[insert_struct_index:]
        
        insert_constraint_index = self.XML.find("<constraints>") + 13
        self.XML = self.XML[:insert_constraint_index] + "\n" + self.constraint + self.XML[insert_constraint_index:]

        with open(fileName, 'w') as f:
            f.write(self.XML)
    

    def analysisBFS(self, showTag):
        priorityQ = []
        priorityQ.append(self.root)	
        while len(priorityQ) > 0:
            node = priorityQ.pop(0)
            node.setVisited(True);
            if node.hasChild():
                children = node.getChildren()
                for n in children:
                    if not n.getVisited():
                        priorityQ.append(n)
        flag = 0	
        for element in self.elements:
            node = self.elements.get(element)
            if not node.getVisited():
                flag = 1
                if node.abstract:
                    print("Abstract Feature: " + node.name + " in ID: " + node.id + " is not defined")
                else:
                    print("Concrete Feature: " + node.name + " in ID: " + node.id + " is not defined")
        
                index = self.data[self.data['id'] == node.id].index
                self.data.loc[index,'valid'] = 0
        if flag:
            self.update(showTag)

    # Debugging Purposes
    def display(self):
        print(self.XML)
    
class RTW:
    
    global rules
    rules = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
    
    global logic_operators
    logic_operators = ['AND', 'OR', 'IFF', 'IMPLY', 'NOT']
    
    def __init__(self):
        data = {
            'id':[],
            'valid':[],
            'abstract':[],
            'concrete':[], 
            'logic':[],
            'rule':[],
        }
        self.data = pd.DataFrame(data)
      
    
    def getDataFromFile(self, fileName):
        with open(fileName, 'r') as f:
            ID = ""
            valid = 0
            abstract_features = []
            concrete_features = []
            logic = ""
            rule = ""
            partition = '-->'
            count = 0
            line_count = 0
            
            for line in f:
                line_count += 1
                
                if line.strip().startswith('ID'):
                    ID = line[line.find(partition) + len(partition):].strip()
                   
                elif line.strip().startswith('Valid'):
                    valid = int(line[line.find(partition) + len(partition):].strip())
                    
                elif line.strip().startswith('Abstract'):
                    abstract = line[line.find(partition) + len(partition):].strip()
                    abstract = abstract.split(",")
                    
                    for feature in abstract:
                        if feature.strip() == 'none':
                            break
                        abstract_features.append(feature.strip())
                        
                elif line.strip().startswith('Concrete'):
                    concrete = line[line.find(partition) + len(partition):].strip()
                    concrete = concrete.split(",")
                    
                    for feature in concrete:
                        if feature.strip() == 'none':
                            break
                        concrete_features.append(feature.strip())
                        
                elif line.strip().startswith('Logic'):
                    logic = line[line.find(partition) + len(partition):].strip()
                    if not self.parenthesisMatch(logic):
                        raise Exception("There is a logic with unbalanced parenthesis in line " + str(line_count))
                    
                elif line.strip().startswith('Rule'):
                    rule = line[line.find(partition) + len(partition):].strip()
                
                count += 1
                
                if count == 6:
                    self.data.loc[len(self.data.index)] = np.array([ID, valid, abstract_features, concrete_features, logic, rule], dtype=object)
                    continue
                
                if line.strip() == "":
                    ID = ""
                    valid = 0
                    abstract_features = []
                    concrete_features = []
                    logic = ""
                    rule = ""
                    count = 0
                    continue
            
            
    def convertToXML(self, outputFile, showTag=True):
        output = RTWToFM()
        output.processInput(self.data, showTag)
        output.analysisBFS(showTag)
        output.generateXMLFile(outputFile)
        
    def parenthesisMatch(self, string):
        stack = []
        front = ['{', '[', '(']
        end = ['}', ']', ')']
        for i in range(len(string)):
            char = string[i]
            if char in front:
                stack.append(char)
            elif char in end:
                if len(stack) == 0:
                    return False
                char2 = stack.pop()
                if front.index(char2) != end.index(char):
                    return False
        if len(stack) > 0:
            return False
        return True
    
    def display(self):
        display(self.data)
                
        
    
class Element:
    
    def __init__(self, tagName=None, name=None, abstract=False, mandatory=False, void=False):
        self.tagName = tagName
        self.name = name
        self.abstract = abstract
        self.mandatory = mandatory
        self.void = void
        self.parent = None
        self.children = []
        self.id = None
        self.visited = False

    def setVisited(self, flag):
        self.visited = flag

    def getVisited(self):
        return self.visited
        
    def setTagName(self, tagName: str):
        self.tagName = tagName
        
    def setName(self, name: str):
        self.name = name
        
    def setId(self, id: str):
        self.id = id
        
    def setAbstract(self):
        self.abstract = True
        
    def setMandatory(self):
        self.mandatory = True
        
    def setVoid(self):
        self.void = True
        
    def unVoid(self):
        self.void = False
        
    def setParent(self, parent):
        self.parent = parent
        
    def getChildren(self):
        return self.children
    
    def getChildNames(self):
        a = []
        for e in self.children:
            a.append(e.name)
            
        return a
    
    def addChild(self, child):
        self.children.append(child)
        
    def hasChild(self):
        return len(self.children) > 0
    
    def generateStartTag(self):
        XML = ""
        XML += "<" + self.tagName + " "
        if self.abstract:
            XML += 'abstract="true" '
            
        if self.mandatory:
            XML += 'mandatory="true" '
        
        XML += 'name="' + self.name + '"'
        
        if not self.void:
            XML += ">"
        
        elif self.void:
            XML += "/>"
            
        return XML
    
    def generateEndTag(self):
        XML = ""
        if not self.void:
            XML += "</" + self.tagName + ">"
        
        return XML

    
b = RTW()
b.getDataFromFile("RTW.txt")
b.convertToXML("model.xml", showTag=True)
