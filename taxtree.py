# -*- coding: utf-8 -*-
import sys
from os import makedirs
from zipfile import ZipFile
from contextlib import contextmanager
from os.path import join, exists, expanduser

import click
import requests
import humanize
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker
)
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    create_engine,
)


__all__ = [
    'KINGDOM', 'PHYLUM', 'CLASS', 'ORDER',
    'FAMILY', 'GENUS', 'SPECIES', 'get_taxtree_dir',
    'get_dbfile', 'get_engine', 'get_session',
    'get_scoped_session', 'Lineage', 'Tax'
]


KINGDOM = 'kingdom'
PHYLUM = 'phylum'
CLASS = 'class'
ORDER = 'order'
FAMILY = 'family'
GENUS = 'genus'
SPECIES = 'species'
FIELD_TERMINATOR = '\t|\t'
LINE_TERMINATOR = '\t|\n'
SCIENTIFIC_NAME = 'scientific name'
DBFILE = 'taxtree.db'


def get_taxtree_dir():
    taxtree_dir = expanduser('~/.taxtree')
    if not exists(taxtree_dir):
        makedirs(taxtree_dir)
    return taxtree_dir


def get_dbfile():
    return join(get_taxtree_dir(), DBFILE)


def get_engine():
    return create_engine(
        'sqlite:///%s' % get_dbfile()
    )


def get_session():
    return sessionmaker(bind=get_engine())()


@contextmanager
def get_scoped_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


Base = declarative_base()


class Lineage(object):
    def __init__(
            self, kingdom=None, phylum=None, class_=None,
            order=None, family=None, genus=None, species=None
    ):
        self.kingdom = kingdom
        self.phylum = phylum
        self.class_ = class_
        self.order = order
        self.family = family
        self.genus = genus
        self.species = species

    def __repr__(self):
        return 'Lineage<kingdom=%s, phylum=%s, class=%s, order=%s, family=%s, genus=%s, species=%s>' % (
            self.kingdom if self.kingdom else '',
            self.phylum if self.phylum else '',
            self.class_ if self.class_ else '',
            self.order if self.order else '',
            self.family if self.family else '',
            self.genus if self.genus else '',
            self.species if self.species else '',
        )


class Tax(Base):
    __tablename__ = 'tax'

    id = Column(Integer, primary_key=True)
    tax_id = Column(String(20), unique=True)
    parent_tax_id = Column(String(20), index=True, nullable=True)
    parent_id = Column(Integer, ForeignKey('tax.id'), index=True)
    rank = Column(String(100), index=True)
    name = Column(String(100), index=True)
    parent = relationship('Tax', remote_side=[id])

    def __repr__(self):
        return f'Tax<{self.name}>'

    def __eq__(self, other):
        if not isinstance(other, Tax):
            raise NotImplementedError(
                f'Compare between Tax and {other.__class__.__name__} not supported.'
            )
        return self.id == other.id

    def __hash__(self):
        return hash(self.tax_id)

    def fix_parent(self, taxes):
        if self.parent_tax_id is None:
            return None
        else:
            self.parent = taxes[self.parent_tax_id]

    def fix_name(self, names):
        if self.name is None:
            self.name = names[self.tax_id]

    def get_ancestor(self, rank):
        if self.rank == rank:
            return self
        if self.parent is None:
            return None
        return self.parent.get_ancestor(rank)

    def get_lineage(self):
        return Lineage(
            kingdom=self.get_ancestor(KINGDOM),
            phylum=self.get_ancestor(PHYLUM),
            class_=self.get_ancestor(CLASS),
            order=self.get_ancestor(ORDER),
            family=self.get_ancestor(FAMILY),
            genus=self.get_ancestor(GENUS),
            species=self.get_ancestor(SPECIES)
        )


def dl_taxdmp_zip(outfile):
    url = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdmp.zip'
    response = requests.get(url, stream=True)
    downloaded = 0
    total = int(response.headers['Content-Length'])
    with open(outfile, 'wb') as fp:
        for chunk in response.iter_content(1024):
            downloaded += len(chunk)
            fp.write(chunk)
            sys.stdout.write('\rDownloading taxdmp.zip %s/%s' % (
                humanize.naturalsize(downloaded),
                humanize.naturalsize(total)
            ))
            sys.stdout.flush()


def read_names_dmp(fp):
    names = {}
    for line in fp:
        row = line.decode('utf-8').rstrip(LINE_TERMINATOR).split(FIELD_TERMINATOR)
        if row[3] == SCIENTIFIC_NAME:
            names[row[0]] = row[1]
    return names


def read_nodes_dmp(fp):
    taxes = {}
    for line in fp:
        row = line.decode('utf-8').rstrip(LINE_TERMINATOR).split(FIELD_TERMINATOR)
        if row[0] == '1':
            taxes[row[0]] = Tax(tax_id=row[0], rank=row[2])
        else:
            taxes[row[0]] = Tax(tax_id=row[0], parent_tax_id=row[1], rank=row[2])
    return taxes


@click.command()
def taxtree():
    """TaxTree initialize database"""
    # download taxdmp.zip
    taxdmp_zip = join(get_taxtree_dir(), 'taxdmp.zip')
    if not exists(taxdmp_zip):
        dl_taxdmp_zip(taxdmp_zip)

    # read names.dmp and nodes.dmp
    with ZipFile(taxdmp_zip) as zipfile:
        print('Reading names.dmp...')
        with zipfile.open('names.dmp') as fp:
            names = read_names_dmp(fp)

        print('Reading nodes.dmp...')
        with zipfile.open('nodes.dmp') as fp:
            taxes = read_nodes_dmp(fp)

    # fix name
    for tax in taxes.values():
        tax.fix_name(names)

    Base.metadata.create_all(get_engine())
    # save
    with get_scoped_session() as session:
        saved = 0
        total = len(taxes)
        for tax in taxes.values():
            session.add(tax)
            saved += 1
            sys.stdout.write('\rSaving %d/%d' % (saved, total))
            sys.stdout.flush()
        session.commit()

        # update parent taxonomy
        updated = 0
        for tax in taxes.values():
            tax.fix_parent(taxes)
            session.add(tax)
            updated += 1
            sys.stdout.write('\rUpdating %d/%d' % (updated, total))
            sys.stdout.flush()
        session.commit()

    print(f'{total} taxonomies saved.')


if __name__ == '__main__':
    taxtree()
