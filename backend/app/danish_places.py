"""Danish place-name gazetteer + text lookup — pulled out of app/routers/news.py
since it's pure reference data (not routing/fetching logic) and had grown to
dwarf the rest of that file.

Used to pin a news headline/article on the map when it names a real place —
the feeds themselves carry no geodata, so this is always a "which town"
approximation, never the actual crime scene.
"""
import re

# Approximate city/town centers. Covers the ~70 largest Danish towns, city
# districts for the 4 largest cities, and the remaining Danish municipalities
# (of 98) not covered by a town above.
DANISH_PLACES = {
    "københavn": (55.6761, 12.5683),
    "copenhagen": (55.6761, 12.5683),
    "frederiksberg": (55.6786, 12.5306),
    "aarhus": (56.1629, 10.2039),
    "århus": (56.1629, 10.2039),
    "odense": (55.4038, 10.4024),
    "aalborg": (57.0488, 9.9217),
    "esbjerg": (55.4765, 8.4594),
    "randers": (56.4607, 10.0369),
    "kolding": (55.4904, 9.4721),
    "horsens": (55.8607, 9.8503),
    "vejle": (55.7091, 9.5357),
    "roskilde": (55.6415, 12.0803),
    "herning": (56.1362, 8.9761),
    "silkeborg": (56.1697, 9.5459),
    "næstved": (55.2299, 11.7607),
    "fredericia": (55.5654, 9.7526),
    "viborg": (56.4530, 9.4020),
    "køge": (55.4578, 12.1817),
    "holstebro": (56.3606, 8.6153),
    "taastrup": (55.6500, 12.3000),
    "slagelse": (55.4055, 11.3547),
    "hillerød": (55.9268, 12.3072),
    "sønderborg": (54.9092, 9.7906),
    "svendborg": (55.0577, 10.6106),
    "hjørring": (57.4649, 9.9799),
    "holbæk": (55.7178, 11.7095),
    "frederikshavn": (57.4407, 10.5372),
    "nørresundby": (57.0693, 9.9217),
    "ringsted": (55.4419, 11.7909),
    "skive": (56.5661, 9.0287),
    "haderslev": (55.2500, 9.4900),
    "nykøbing falster": (54.9667, 11.8750),
    "nykøbing mors": (56.7929, 8.8517),
    "helsingør": (56.0361, 12.6136),
    "aabenraa": (55.0442, 9.4197),
    "ballerup": (55.7308, 12.3608),
    "ishøj": (55.6167, 12.3500),
    "brøndby": (55.6500, 12.4167),
    "glostrup": (55.6667, 12.4000),
    "gladsaxe": (55.7333, 12.4667),
    "lyngby": (55.7700, 12.5000),
    "hvidovre": (55.6500, 12.4833),
    "rødovre": (55.6833, 12.4500),
    "greve": (55.5833, 12.3000),
    "solrød": (55.5333, 12.1833),
    "vallensbæk": (55.6167, 12.3667),
    "albertslund": (55.6600, 12.3600),
    "farum": (55.8100, 12.3600),
    "værløse": (55.7833, 12.3500),
    "birkerød": (55.8400, 12.4300),
    "hørsholm": (55.8833, 12.4833),
    "rungsted": (55.9000, 12.5500),
    "kalundborg": (55.6797, 11.0894),
    "korsør": (55.3300, 11.1400),
    "nykøbing sjælland": (55.9167, 11.6667),
    "nakskov": (54.8300, 11.1400),
    "maribo": (54.7719, 11.5083),
    "faaborg": (55.1017, 10.2417),
    "middelfart": (55.5061, 9.7367),
    "assens": (55.2700, 9.9000),
    "nyborg": (55.3128, 10.7889),
    "ringe": (55.2333, 10.4833),
    "grenaa": (56.4133, 10.8794),
    "ebeltoft": (56.1958, 10.6817),
    "hobro": (56.6389, 9.7972),
    "skagen": (57.7208, 10.5836),
    "brønderslev": (57.2667, 9.9500),
    "thisted": (56.9553, 8.6939),
    "struer": (56.4894, 8.6011),
    "lemvig": (56.5461, 8.3050),
    "ikast": (56.1394, 9.1553),
    "brande": (55.9333, 9.1333),
    "tønder": (54.9358, 8.8619),
    "ribe": (55.3306, 8.7647),
    "varde": (55.6211, 8.4814),
    "rønne": (55.1000, 14.7000),

    # City districts/neighborhoods for the 4 largest cities — without these,
    # almost every Copenhagen/Aarhus story only matches the city-center
    # coordinate above and all stack on one point. Matching the actual
    # district named in the headline (e.g. "Nørrebro", "Amager") gets each
    # story its own, meaningfully different pin instead of one big cluster.
    "nørrebro": (55.6969, 12.5535),
    "østerbro": (55.7058, 12.5776),
    "vesterbro": (55.6699, 12.5510),
    "amager": (55.6580, 12.6040),
    "valby": (55.6600, 12.5060),
    "vanløse": (55.6870, 12.4780),
    "brønshøj": (55.7050, 12.4930),
    "sydhavn": (55.6570, 12.5460),
    "christianshavn": (55.6740, 12.5940),
    "indre by": (55.6790, 12.5780),
    "gentofte": (55.7500, 12.5500),
    "risskov": (56.1900, 10.2280),
    "åbyhøj": (56.1550, 10.1590),
    "viby": (56.1280, 10.1830),
    "brabrand": (56.1520, 10.1150),
    "skejby": (56.2040, 10.1730),
    "tilst": (56.1900, 10.1000),
    "hasle": (56.1730, 10.1610),
    "trøjborg": (56.1660, 10.2050),
    "vollsmose": (55.4230, 10.4370),

    # Remaining Danish municipalities (of 98) not already covered by a town
    # above — mostly smaller kommuner where the news would more likely name
    # the kommune itself than its (often tiny) seat town.
    "skanderborg": (56.0397, 9.9310),
    "hinnerup": (56.3667, 10.0333),
    "favrskov": (56.3667, 10.0333),
    "rebild": (56.8333, 9.8833),
    "aars": (56.8039, 9.5187),
    "vesthimmerland": (56.8039, 9.5187),
    "vesthimmerlands": (56.8039, 9.5187),
    "aabybro": (57.1667, 9.7333),
    "jammerbugt": (57.1667, 9.7333),
    "ringkøbing": (56.0900, 8.2400),
    "ringkøbing skjern": (56.0900, 8.2400),
    "fanø": (55.4333, 8.4000),
    "vejen": (55.4833, 9.1333),
    "billund": (55.7333, 9.1000),
    "hedensted": (55.7667, 9.7000),
    "odder": (55.9667, 10.1500),
    "samsø": (55.8333, 10.5833),
    "norddjurs": (56.4133, 10.8794),
    "syddjurs": (56.1958, 10.6817),
    "mariagerfjord": (56.6389, 9.7972),
    "stevns": (55.3333, 12.4167),
    "faxe": (55.2500, 12.1167),
    "sorø": (55.4333, 11.5500),
    "lejre": (55.6000, 11.8500),
    "vordingborg": (55.0086, 11.9083),
    "dragør": (55.5928, 12.6716),
    "tårnby": (55.6294, 12.6033),
    "herlev": (55.7333, 12.4333),
    "allerød": (55.8700, 12.3200),
    "fredensborg": (55.9667, 12.4000),
    "halsnæs": (55.9667, 12.0167),
    "frederiksværk": (55.9667, 12.0167),
    "gribskov": (56.0167, 12.2000),
    "helsinge": (56.0167, 12.2000),
    "frederikssund": (55.8394, 12.0664),
    "egedal": (55.7667, 12.1500),
    "rudersdal": (55.8300, 12.4500),
    "furesø": (55.7833, 12.3500),
}

# word-boundary regex per place name (compiled once), longest name first so
# a specific district (e.g. "nørrebro") wins over the broader city it sits
# inside ("københavn") when a headline names both.
_PLACE_PATTERNS = sorted(
    ((name, coords, re.compile(rf"\b{re.escape(name)}\b")) for name, coords in DANISH_PLACES.items()),
    key=lambda entry: len(entry[0]),
    reverse=True,
)


def find_location(*texts: str) -> tuple[float | None, float | None]:
    combined = " ".join(t for t in texts if t).lower()
    for _name, coords, pattern in _PLACE_PATTERNS:
        if pattern.search(combined):
            return coords
    return None, None
