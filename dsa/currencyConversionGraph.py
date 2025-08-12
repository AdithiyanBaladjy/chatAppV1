
def getParentInd(ind):
    if parentArr[ind]==ind:
        return ind
    else:
        return getParentInd(parentArr[i])

inp=[["Jp","Au",0.25],["Au","Us",0.15],["Us","Gbr",0.35],["Ger","Arg",0.65],["Arg","Jp",0.9]]
query=["Jp","Ger"]
currMap={}
mapInd=0

for i in range(len(inp)):
    currInd=currMap.get(inp[i][0])
    if (currInd == None):
        currMap[currMap.get(inp[i][0])]=mapInd
        mapInd+=1
    currInd=currMap.get(inp[i][1])
    if (currInd ==None):
        currMap[currMap.get(inp[i][1])]=mapInd
        mapInd+=1
graph=[[0 for i in range(mapInd)] for j in range(mapInd)]
parentArr=list(range(mapInd))

for i in range(len(inp)):
    fromCurr=inp[i][0]
    toCurr=inp[i][1]
    convRatio=inp[i][2]
    fromInd=currMap.get(fromCurr)
    toInd=currMap.get(toCurr)
    graph[fromInd][toInd]=convRatio
    parent[toCurr]=
