-- Canonical ontology-backed entity storage
create table if not exists ontology_entities (
    entity_id text primary key,
    entity_type text not null,
    mission_id text not null,
    confidence numeric(5,4) not null,
    classification text not null,
    releasability text not null,
    compartment_tags text[] not null,
    valid_from timestamptz not null,
    valid_to timestamptz,
    lineage_id text not null,
    source_refs jsonb not null,
    created_at timestamptz not null default now()
);

create table if not exists ontology_relationships (
    rel_id text primary key,
    src_entity_id text not null,
    dst_entity_id text not null,
    rel_type text not null,
    confidence numeric(5,4) not null,
    mission_id text not null,
    valid_from timestamptz not null,
    valid_to timestamptz,
    lineage_id text not null,
    constraint fk_src foreign key (src_entity_id) references ontology_entities(entity_id),
    constraint fk_dst foreign key (dst_entity_id) references ontology_entities(entity_id)
);
