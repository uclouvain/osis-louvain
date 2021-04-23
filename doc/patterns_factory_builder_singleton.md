# Design patterns "Builder" et "Factory"

## Design pattern "Factory"

### Définition

https://refactoring.guru/fr/design-patterns/factory-method

- Le pattern **Factory** est un patron de conception de création qui définit une interface 
pour créer des objets dans une classe mère, mais délègue le choix des types d’objets à créer aux sous-classes.


<br/><br/><br/><br/><br/><br/><br/><br/>



### Problème

- Gestion d'un programme de formation (ProgramTree) qui contient des enfants appelés "groupements" (Node)
- Ces groupements peuvent être de plusieurs natures
    - une unité d'enseignement
    - une classe
    - un groupement
- Ces groupements ont des logiques à la fois communes et spécifiques à leurs natures


<br/><br/><br/><br/><br/><br/><br/><br/>



### Solution

- Utiliser une **Factory**, capable de créer un groupement en fonction des attributs
```python
from osis_common.ddd import interface


class Node(interface.Entity):
    """Classe comportant les logiques communes"""
    pass

class NodeGroupYear(Node):
    """Classe comportant les logiques spécifiques aux groupements"""
    pass

class NodeLearningUnitYear(Node):
    """Classe comportant les logiques spécifiques aux Unités d'Enseignement"""
    pass

class NodeLearningClassYear(Node):
    """Classe comportant les logiques spécifiques aux classes"""
    pass


class NodeFactory:
    def get_node(self, type: NodeType, **node_attrs) -> 'Node':
        if type == GROUP:
            return NodeGroupYear(**node_attrs)
        if type == LEARNING_UNIT:
            return NodeLearningUnitYear(**node_attrs)
        if type == LEARNING_CLASS:
            return NodeLearningClassYear(**node_attrs)
        raise Exception("Unknown type")


# Utilisation
learning_unit_node = NodeFactory().get_node(
    type=LEARNING_UNIT,
    code='LDROI1001',
    year=2021,
    # ... 
)


``` 


<br/><br/><br/><br/><br/><br/><br/><br/>



### Avantages et inconvénients

- (+) Complexité de création (constructeurs complexes) masquée et encapsulée dans une classe dédiée
- (+) Principe de responsabilité unique : code de création d'un Node à un seul et même endroit, découplé de la logique métier (maintenance +++)
- (+) Flexibilité : permet d'ajouter de nouveaux types de Node sans endommager l'existant

- (-) Démultiplication des sous-classes (maintenance ---) 



<br/><br/><br/><br/><br/><br/><br/><br/>



## Design pattern "Builder"

### Définition

https://refactoring.guru/fr/design-patterns/builder

- Le pattern **Builder** est un patron de conception de création qui permet de construire des objets complexes 
étape par étape. Il permet de produire différentes variations ou représentations d’un objet 
en utilisant le même code de construction.


<br/><br/><br/><br/><br/><br/><br/><br/>



### Problème

- Gestion d'un programme de formation (ProgramTree) qui contient des enfants appelés "groupements" (Node)
- La création d'un programme de formation nécessite la création de groupements, sous-groupements, sous-sous-groupements... de types différents
- En fonction du type groupement racine du programme de formation, la création de son contenu change
- Je peux créer un programme de formation sur une année 2021 sur base de ce même programme en 2020

Constat : la création d'un programme de formations est complexe, avec beaucoup de champs et objets imbriqués


<br/><br/><br/><br/><br/><br/><br/><br/>



### Solution

- Utiliser un **builder**, capable de créer un programme de formations en fonction des attributs

```python
from osis_common.ddd import interface


class ProgramTree(interface.RootEntity):
    pass


class ProgramTreeBuilder:

    def create_from_other_tree(self, other_tree: 'ProgramTree') -> 'ProgramTree':
        root = self._duplicate_root(other_tree)
        mandatory_children_types = self._get_mandatory_children_types(other_tree, root)
        children = self._duplicate_children(other_tree)
        new_authorized_relationships = self._get_authorized_relationships(other_tree)
        
        # ... 
        # autres manipulations compliquées
        # ...
        
        return ProgramTree(
            entity_identity=ProgramTreeIdentity(code=root.code, year=root.year),
            root_node=root,
            authorized_relationships=new_authorized_relationships
        )

    def create(self, **program_tree_attrs) -> 'ProgramTree':
        node_attrs = self._extract_root_node_attrs(program_tree_attrs)
        root_node = node_factory.get_node(node_attrs)
        children = self._create_children(root_node, **program_tree_attrs)
        
        # ... 
        # autres manipulations compliquées
        # ...
        
        return ProgramTree(
            entity_identity=ProgramTreeIdentity(code=root.code, year=root.year),
            root_node=root,
            authorized_relationships=new_authorized_relationships
        )
```


<br/><br/><br/><br/><br/><br/><br/><br/>



### Avantages et inconvénients

- (+) Découplage du code : construire les objets étape par étape et les déléguer ou les exécuter récursivement.
- (+) Réutilisation du code : même code pour plusieurs représentations des ProgramTrees
- (+) Principe de responsabilité unique : code complexe de la construction séparé de la logique métier du ProgramTree

- (-) Démultiplication des classes (maintenance ---)




<br/><br/><br/><br/><br/><br/><br/><br/>



## Design pattern "Singleton"

### Définition

https://refactoring.guru/fr/design-patterns/singleton

- Le pattern **Singleton** est un patron de conception de création qui garantit que l’instance d’une classe 
n’existe qu’en un seul exemplaire, tout en fournissant un point d’accès global à cette instance.

### Avantages et inconvénients

- cf. https://refactoring.guru/fr/design-patterns/singleton

### Questions

- Comment implémenter le Singleton pour le ProgramTreeBuilder ?
- Comment implémenter le Singleton pour le NodeFactory ?
- Devrait-on implémenter le Singleton pour les Factories et Builders ? 
