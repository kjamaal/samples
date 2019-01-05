import sys

#requires sorted list l
def bsearch(l, term):
  first = 0
  last = len(l)-1
  found = False
  while first <= last and not found:
    mid = (first+last)//2
    if l[mid] == term:
      found = True
    else:
      if term < l[mid]:
        last = mid-1
      else:
        first = mid+1
  return found

print(bsearch(sys.argv[1].split(','), sys.argv[2]))
