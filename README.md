# TaxTree: Python library for NCBI taxonomy database

Supported features:


1. download data from NCBI automatically.
2. use SQLite and SQLAlchemy to persist data.
3. retrieve ancestor taxonomy in any rank.

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

1. All data were saved to `~/.taxtree`
2. Downloaded `taxdmp.zip` path: `~/.taxtree/taxdmp.zip`
3. Persistent data file path: `~/.taxtree/taxtree.db`

### search taxonomy

```python
from taxtree import get_scoped_session, Tax

with get_scoped_session() as session:
    tax = session.query(Tax).filter_by(tax_id='9606').first()
```


### get ancestor

```python
from taxtree import get_scoped_session, Tax, KINGDOM, PHYLUM

with get_scoped_session() as session:
    tax = session.query(Tax).filter_by(tax_id='9606').first()
    kingdom_tax = tax.get_ancestor(KINGDOM)
    phylum_tax = tax.get_ancestor(PHYLUM)
```
