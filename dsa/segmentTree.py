import math

#start time: 6:18 AM
#end time: 7:15 AM

"""
Segment tree data structure to efficiently store range data. 
The Segment tree is going to store the Server-requests arr range.

So two methods needed:
1. buildTree - divides and stores the server with the min requests at every node. root node represents the min function over the total range.
2. queryTree - 
3. updateAtIndex - 
"""
class minSegmentTree():
    def __init__(self,serverArr):
        self.nServers=len(serverArr)
        self.treeHeight=math.ceil(self.nServers/2)
        self.nNodes=pow(2,self.treeHeight+1)
        self.serverArr=serverArr
        self.tree=[0 for i in range(self.nNodes)]
        print(self.tree)
        self.buildTree(0,0,self.nServers-1)
    
    def buildTree(self,currentNode,startInd,endInd):
        print("building tree: ",startInd,endInd,currentNode)
        if((startInd>=endInd)and(startInd<self.nServers)):
            self.tree[currentNode]=self.serverArr[startInd]
            return self.tree[currentNode]
        midInd=(endInd-startInd)//2
        leftMin=self.buildTree(2*currentNode+1,startInd,(startInd+midInd))
        rightMin=self.buildTree(2*currentNode+2,(startInd+midInd+1),endInd)
        currentMin=leftMin if leftMin <= rightMin else rightMin
        self.tree[currentNode]=currentMin
        return currentMin

    def queryTree(self,startRange,endRange):
        self.queryAns=serverNode(999999,-1)
        self.traverseTree(startRange,endRange,0,self.nServers-1,0) 
        return self.queryAns   
    
    def traverseTree(self,startRange,endRange,startInd,endInd,currentNode):
        if(startRange==startInd and endRange == endInd):
            self.queryAns = self.tree[currentNode]
        elif(startRange<=startInd and endRange >= endInd):
            self.queryAns = self.queryAns if self.queryAns < self.tree[currentNode] else self.tree[currentNode]
        elif(startInd>=endInd):
            return
        else:
            midInd=(endInd-startInd)//2
            if(startRange>=startInd or endRange <= (startInd+midInd)):
                self.traverseTree(startRange,endRange,startInd,(startInd+midInd),2*currentNode+1)
            if(startRange>=(startInd+midInd+1) or endRange <= endInd):
                self.traverseTree(startRange,endRange,(startInd+midInd+1),endInd,2*currentNode+2)

    def updateAtIndex(self,index,val):
        self.traverseUpdate(index,val,0,self.nServers-1,0)

    def traverseUpdate(self,index,val,startInd,endInd,currentNode):
        if(index==startInd and index==endInd):
            self.tree[currentNode]=val
            return self.tree[currentNode]
        elif(index>=startInd and index<=endInd):
            midInd=(endInd-startInd)//2
            leftMin=self.traverseUpdate(index,val,startInd,(startInd+midInd),2*currentNode+1)
            rightMin=self.traverseUpdate(index,val,(startInd+midInd+1),endInd,2*currentNode+2)
            self.tree[currentNode]=leftMin if leftMin <= rightMin else rightMin
            return self.tree[currentNode]
        else:
            return self.tree[currentNode]

class serverNode():
    def __init__(self,nodeVal,nodeInd):
        self.ind=nodeInd
        self.val=nodeVal
    def __lt__(self,newVal):
        print(self.val,newVal)
        return self.val < newVal.val
    def __le__(self,newVal):
        return self.val <= newVal.val
    def incrementReq(self):
        self.val+=1
    def __str__(self):
        return "{'Index':"+str(self.ind)+", 'value':"+str(self.val)+"}"
    def __repr__(self):
        return "{'Index':"+str(self.ind)+", 'value':"+str(self.val)+"}"

nServers=4
inputQuery=[1,2,2,2]
serverArr=[serverNode(0,i) for i in range(nServers)]
print(serverArr)
segTree=minSegmentTree(serverArr)
outputArr=[]
for i in range(len(inputQuery)):
    minObj=segTree.queryTree(0,inputQuery[i])
    if minObj is not None:
        outputArr.append(minObj.ind)
        minObj.incrementReq()
        segTree.updateAtIndex(minObj.ind,minObj)
print(outputArr)
#output - [0,1,2,3]