import math
#start time - 9:46 PM
class MinSegmentTree:
    def __init__(self,inputArr):
        self.n=len(inputArr)
        self.treeHeight=math.ceil(self.n/2)
        self.numOfNodes=pow(2,self.treeHeight+1)-1
        self.tree=[0 for i in range(self.numOfNodes+1)]
        print("num of nodes",self.numOfNodes)
        self.inputArr=inputArr
        self.buildTree(0,self.n-1,0)
        print("Tree:",self.tree)
        pass

    def buildTree(self,startInd,endInd,treeInd):
        print(startInd,endInd,treeInd)
        if startInd >= endInd:
            self.tree[treeInd]=self.inputArr[startInd]
            return self.inputArr[startInd]
        middleInd=(endInd-startInd)//2
        leftMin=self.buildTree(startInd,(startInd+middleInd),2*treeInd+1)
        rightMin=self.buildTree((startInd+middleInd+1),endInd,2*treeInd+2)
        self.tree[treeInd]=leftMin if leftMin<rightMin else rightMin
        return self.tree[treeInd]
    
    def updateInputArr(self,newVal,updateInd,startInd,endInd,currentNode):
        if((updateInd<startInd)or(updateInd>endInd)or(startInd>endInd)):
            return 999999
        if(startInd==updateInd and endInd==updateInd):
            self.inputArr[updateInd]=newVal
            newMin=self.tree[currentNode] if self.tree[currentNode] < newVal else newVal
            self.tree[currentNode]=newMin
            return newMin
        middleInd=(endInd-startInd)/2
        if((startInd<=updateInd)and(updateInd<=middleInd)):
            retVal=self.updateInputArr(newVal,updateInd,startInd,(startInd+middleInd),2*currentNode+1)
        else:
            retVal=self.updateInputArr(newVal,updateInd,(startInd+middleInd+1),endInd,2*currentNode+2)            
        newMin=self.tree[currentNode] if self.tree[currentNode] < retVal else retVal
        self.tree[currentNode]=newMin
        return newMin
    
    def traverseTree(self,queryStartInd,queryEndInd,startInd,endInd,currentNode):
        print("Querying",startInd,endInd)
        if(queryStartInd==startInd and queryEndInd==endInd):
            self.queryAns= self.tree[currentNode]
        elif(startInd>=queryStartInd and endInd <= queryEndInd):
            self.queryAns=self.queryAns if self.queryAns < self.tree[currentNode] else self.tree[currentNode]
        elif(startInd<endInd):
            middleInd=(endInd-startInd)//2
            self.traverseTree(queryStartInd,queryEndInd,startInd,(startInd+middleInd),2*currentNode+1)
            self.traverseTree(queryStartInd,queryEndInd,(startInd+middleInd+1),endInd,2*currentNode+2)
        
    def queryTree(self,queryStartInd,queryEndInd):
        self.queryAns=99999
        self.traverseTree(queryStartInd,queryEndInd,0,self.n-1,0)
        return self.queryAns


#input to Segment Tree is an array
arr=[7,2,5,1,5,6,7]
sTree=MinSegmentTree(arr)
sTree.updateInputArr(0,0,0,len(arr)-1,0)
print(sTree.queryTree(4,6))