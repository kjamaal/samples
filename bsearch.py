import sys

#requires sorted list l
def bsearch(l, term):
  first = 0
  last = len(l)-1
  while first <= last:
    mid = (first+last)//2
    if l[mid] == term:
      return l[mid]
    else:
      if term < l[mid]:
        last = mid-1
      else:
        first = mid+1

print(bsearch(sys.argv[1].split(','), sys.argv[2]))
