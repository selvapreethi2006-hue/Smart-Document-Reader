"""Build a clean contact card from extracted info."""

from modules.info_extractor import extract_info


def build_contacts(text):
    info = extract_info(text)
    names = info.get("names", [])
    emails = info.get("emails", [])
    phones = info.get("phones", [])
    addresses = info.get("addresses", [])

    if not (names or emails or phones):
        return []

    if names and len(names) == len(emails) == len(phones):
        return [
            {"name": names[i], "email": emails[i], "phone": phones[i],
             "address": addresses[i] if i < len(addresses) else ""}
            for i in range(len(names))
        ]

    return [{
        "name": ", ".join(names) if names else "",
        "email": ", ".join(emails) if emails else "",
        "phone": ", ".join(phones) if phones else "",
        "address": ", ".join(addresses) if addresses else "",
    }]


def card_to_vcard(contact):
    name = contact.get("name", "").strip()
    parts = name.split()
    first = parts[0] if parts else ""
    last = " ".join(parts[1:]) if len(parts) > 1 else ""

    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{last};{first};;;",
        f"FN:{name}",
    ]
    if contact.get("email"):
        lines.append(f"EMAIL:{contact['email']}")
    if contact.get("phone"):
        lines.append(f"TEL:{contact['phone']}")
    if contact.get("address"):
        lines.append(f"ADR:;;{contact['address']};;;;")
    lines.append("END:VCARD")
    return "\r\n".join(lines)
