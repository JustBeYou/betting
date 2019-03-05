Sure betting interface
===
* Class/procedural module
* Take a match as input with its corresponding odds
```python
match_obj = {
  "id": 123, # match id
  "odds": [
    ...
  ]
}

odd_obj = {
  "id": 123,          # odd event id
  "type_id": 2,       # odd type
  "period_id": 0,     # period type (first half, last half, whole match bet)
  "bookmaker_id": 55, # bookmaker id
  "price": 1.56       # the price
}
```
* It should also take as input the types of the distinct odds (possible period_ids)
* The best bet should be returned:
```python
best_obj = {
  period_id1: odd_obj1,

  period_id2: odd_obj2,

  period_id3: odd_obj3,
  
  ...
}
```
* You can only pair odds that have the same period_id
* Example
```python
best = Calculator(
  ['1', 'X', '2'], # type_ids
  { ... }    # match object
)

print (best)
```
```python
{
  '1': { ... }, # best bet for type 1
  'X': { ... }, # best bet for type 2
  '2': { ... }  # best bet for type 3
}
```
