# CQS : Command Query Separation


## Définition

- En français : séparation commande-requête

- Principe de programmation qui vise à séparer les objets/fonctions en 2 catégories
    - Les "requêtes" : 
        - retournent un résultat 
        - ne modifient pas l'état du système 
        - pas de "side effect" possible

    - Les "commandes" :
        - modifient l'état du système
        - ne renvoient pas de résultat
        - synonymes : "modifiers", "mutators"

- Exemple :

```python
from typing import List


# Non CQS
class MyFruitsList:
    fruits : List['str'] = None
    _curent_element_position = None
    
    def next(self):
        if self._curent_element_position is None:
            self._curent_element_position = 0
        else: 
            self._curent_element_position += 1
        return self.fruits[self._curent_element_position]

my_fruits = MyFruitsList(fruits=["pomme", "fraise", "orange"])
pomme = my_fruits.next()
fraise = my_fruits.next()
orange = my_fruits.next()


# CQS
class MyFruitsList:
    fruits : List['str'] = None
    _curent_element_position = 0
    
    # Commande
    def move_forward(self) -> None:
        self._curent_element_position += 1
    
    # requête 
    def current_element(self) -> str:
        return self.fruits[self._curent_element_position]


my_fruits = MyFruitsList(fruits=["pomme", "fraise", "orange"])
pomme = my_fruits.current_element()

my_fruits.move_forward()
fraise = my_fruits.current_element()

my_fruits.move_forward()
orange = my_fruits.current_element()

```


## CQS : Avantages

- Visibilité claire sur le code qui modifie l'état du système du code qui le consulte

- Facilité de maintenance en cas de problème de performance (souvent, en lecture)



## CQS : Notre implémentation

- Application services read / write
- Cf. [interface DDD](https://github.com/uclouvain/osis-common/blob/e9496bc8bc4b586a8ba2dafa5292992ae2f6c09b/ddd/interface.py)
