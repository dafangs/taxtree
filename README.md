# TaxTree: Python library for NCBI taxonomy database

Supported features:


1. download data from NCBI automatically.
2. use SQLite and SQLAlchemy to persist data.
3. retrieve ancestor taxonomy in any rank.
4. retrieve lineage for a given NCBI taxonomy ID.

## installation

```
pip install taxtree
```

## usage

### initialize database

Just run:

```
taxtree
```

TaxTree assume the current directory as cache, if this directory
has a file named `taxdmp.zip`, TaxTree will omit downloading. You
can change cache directory:

```
taxtree -c /path/to/taxdump/
```

`TaxTree` default create `SQLite` data file under current directory,
if you want to change:

```
export TAX_TREE_DBFILE = 'my_taxtree.db'
taxtree
```

Note that if you change `SQLite` data file may be either current directory
or `TAX_TREE_DBFILE`.

### search taxonomy

```python
from taxtree import get_session, Tax


with get_session() as session:
    tax = session.query(Tax).filter_by(tax_id='9606').first()
```


### get ancestor

```python
from taxtree import get_session, Tax, KINGDOM, PHYLUM


with get_session() as session:
    tax = session.query(Tax).filter_by(tax_id='9606').first()
    kingdom_tax = tax.get_ancestor(KINGDOM)
    phylum_tax = tax.get_ancestor(PHYLUM)
```

### get lineage


```python
from taxtree import get_session, Tax


with get_session() as session:
    tax = session.query(Tax).filter_by(tax_id='9606').first()
    lineage = tax.get_lineage()
    print(lineage)
```
