#!/usr/bin/env python3
"""
Parse SDN_ENHANCED.xml and extract structured records.
"""

import xml.etree.ElementTree as ET
import json
from datetime import datetime

def parse_sdn_enhanced(xml_path: str, output_path: str):
    """Parse SDN_ENHANCED.xml and write records to JSON."""

    # Define namespace
    ns = {'sdn': 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/ENHANCED_XML'}

    print(f"Parsing {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Get snapshot date from publicationInfo
    data_as_of = root.find('.//sdn:publicationInfo/sdn:dataAsOf', ns)
    snapshot_date = None
    if data_as_of is not None and data_as_of.text:
        # Parse ISO format date and convert to YYYY-MM-DD
        dt = datetime.fromisoformat(data_as_of.text.replace('Z', '+00:00'))
        snapshot_date = dt.strftime('%Y-%m-%d')

    print(f"Snapshot date: {snapshot_date}")

    records = []
    entities = root.findall('.//sdn:entities/sdn:entity', ns)
    total = len(entities)
    print(f"Found {total} entities")

    for i, entity in enumerate(entities):
        if (i + 1) % 5000 == 0:
            print(f"Processing entity {i + 1}/{total}...")

        # Get UID from entity id attribute
        uid = entity.get('id', '')

        # Get entity type
        entity_type_elem = entity.find('.//sdn:generalInfo/sdn:entityType', ns)
        entity_type = entity_type_elem.text if entity_type_elem is not None else ''

        # Get remarks
        remarks_elem = entity.find('.//sdn:generalInfo/sdn:remarks', ns)
        remarks = remarks_elem.text if remarks_elem is not None else ''

        # Get programs
        programs = []
        for prog in entity.findall('.//sdn:sanctionsPrograms/sdn:sanctionsProgram', ns):
            if prog.text:
                programs.append(prog.text)

        # Get names
        primary_name = ''
        aka_names = []

        for name in entity.findall('.//sdn:names/sdn:name', ns):
            is_primary_elem = name.find('sdn:isPrimary', ns)
            is_primary = is_primary_elem is not None and is_primary_elem.text == 'true'

            # Get formatted full name from translation
            full_name_elem = name.find('.//sdn:translation/sdn:formattedFullName', ns)
            full_name = full_name_elem.text if full_name_elem is not None else ''

            if is_primary:
                primary_name = full_name
            else:
                if full_name:
                    aka_names.append(full_name)

        record = {
            'uid': uid,
            'primary_name': primary_name,
            'aka_names': aka_names,
            'programs': programs,
            'entity_type': entity_type,
            'remarks': remarks or '',
            'source_list': 'SDN_ENHANCED',
            'snapshot_date': snapshot_date
        }
        records.append(record)

    print(f"Writing {len(records)} records to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print("Done!")
    return records

if __name__ == '__main__':
    records = parse_sdn_enhanced('SDN_ENHANCED.xml', 'sdn_enhanced_records.json')

    # Print sample records
    print("\n--- Sample records ---")
    for rec in records[:3]:
        print(json.dumps(rec, indent=2, ensure_ascii=False))
