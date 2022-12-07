"""
Key reference details supporting census data acquisition, such
as geographical hierarchy order resolution support. This allows
census data to be requested for specific geographies without needing
to be dogmatic about the order in which the geography specification
is listed.
"""
# %% STATES
SFIPS_DICT = {
    "state": [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "DC",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "AS",
        "MP",
        "GU",
        "MP",
        "PR",
        "VI",
    ],
    "fips": [
        "01",
        "02",
        "04",
        "05",
        "06",
        "08",
        "09",
        "10",
        "11",
        "12",
        "13",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
        "51",
        "53",
        "54",
        "55",
        "56",
        "60",
        "66",
        "66",
        "69",
        "72",
        "78",
    ],
}


def get_state_by_abbr(ST):
    """
    Get a state's FIPS code based on its two-letter postal abbreviation.

    Parameters
        ST: string - two-letter postal abbreviation

    Returns
        FIPS: string - two-digit FIPS code
    """
    idx = SFIPS_DICT["state"].index(ST)
    return SFIPS_DICT["fips"][idx]


# %% SUMMARY LEVELS
class SummaryLevel:
    """
    Simple class storing details on census summary levels, as shown here:
    https://jtleider.github.io/censusdata/geographies.html
    """

    def __init__(self, level, code):
        self.level = level
        self.code = code

    def get_hierarchy(self):
        """
        Generates a list of strings indicating geography names in order
        of resolution.
        """
        return [s.strip() for s in self.level.split(">")]

    def check_geo(self, geo_list):
        """
        Checks if a list of geographies could refer to this summary level.

        Returns boolean.
        """
        validates = True
        h = self.get_hierarchy()
        for geo in geo_list:
            if geo not in h:
                validates = False
        return validates

    def percent_match(self, geo_list):
        """
        Calculates what portion of geographies in a list is included
        in this summary level and how many items in this summary area
        are not specified in `geo_list`.

        Returns
            percent, unspecified, length, self: tuple
                - `percent` is the share of items in `geo_list` that are
                part of the definition of this summary level.
                - `unspecified` is the count of items defining this
                summary level that are not specified in `geo_list`.
                - `length` is the total count of items defining this
                summary level.
                - 'self' is this summary level object
        """
        total_geos = len(geo_list)
        geos_here = 0
        h = self.get_hierarchy()
        for geo in geo_list:
            if geo in h:
                geos_here += 1
        return geos_here / total_geos, total_geos - geos_here, len(h), self


# TODO: add aliases to support keyword args (no spaces, strokes,etc.)
SUMMARY_LEVELS = [
    SummaryLevel("us", "010"),
    SummaryLevel("region", "020"),
    SummaryLevel("division", "030"),
    SummaryLevel("state", "040"),
    SummaryLevel("state> county", "050"),
    SummaryLevel("state> county> county subdivision", "060"),
    SummaryLevel("state> county> county subdivision> subminor civil division", "067"),
    SummaryLevel("state> county> county subdivision> place/remainder (or part)", "070"),
    SummaryLevel("state> county> county subdivision> place> tract (or part)", "080"),
    SummaryLevel("state> county> tract> block", "101"),
    SummaryLevel("state> county> tract", "140"),
    SummaryLevel("state> county> tract> block group", "150"),
    SummaryLevel("state> place> county (or part)", "155"),
    SummaryLevel("state> place", "160"),
    SummaryLevel("state> consolidated city", "170"),
    SummaryLevel("state> consolidated city> place (or part)", "172"),
    SummaryLevel("state> alaska native regional corporation", "230"),
    SummaryLevel("american indian area/alaska native area/hawaiian home land", "250"),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal subdivision/remainder",
        "251",
    ),
    SummaryLevel(
        "american indian area/alaska native area (reservation or statistical entity only)",
        "252",
    ),
    SummaryLevel(
        "american indian area (off-reservation trust land only)/hawaiian home land",
        "254",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract",
        "256",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract> tribal block group",
        "258",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> state", "260"
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> state> place/remainder",
        "269",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> state> county",
        "270",
    ),
    SummaryLevel(
        "state> american indian area/alaska native area/hawaiian home land (or part)",
        "280",
    ),
    SummaryLevel(
        "state> american indian area> tribal subdivision/remainder (or part)", "281"
    ),
    SummaryLevel(
        "state> american indian area/alaska native area (reservation or statistical entity only) (or part)",
        "283",
    ),
    SummaryLevel(
        "state> american indian area (off-reservation trust land only)/hawaiian home land (or part)",
        "286",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal subdivision/remainder> state",
        "290",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract (or part) within aia (reservation only)",
        "291",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract (or part) within aia (trust land only)",
        "292",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract> tribal block group (or part) within tribal census tract within aia (reservation only)",
        "293",
    ),
    SummaryLevel(
        "american indian area/alaska native area/hawaiian home land> tribal census tract> tribal block group (or part) within tribal census tract within aia (trust land only)",
        "294",
    ),
    SummaryLevel("metropolitan statistical area/micropolitan statistical area", "310"),
    SummaryLevel(
        "metropolitan statistical area/micropolitan statistical area> state (or part)",
        "311",
    ),
    SummaryLevel(
        "metropolitan statistical area/micropolitan statistical area> state> principal city",
        "312",
    ),
    SummaryLevel(
        "metropolitan statistical area/micropolitan statistical area> metropolitan division",
        "314",
    ),
    SummaryLevel("metropolitan statistical area> metropolitan division> state", "315"),
    SummaryLevel(
        "state> metropolitan statistical area/micropolitan statistical area (or part)",
        "320",
    ),
    SummaryLevel(
        "state> metropolitan statistical area/micropolitan statistical area> principal city (or part)",
        "321",
    ),
    SummaryLevel(
        "state> metropolitan statistical area/micropolitan statistical area> county",
        "322",
    ),
    SummaryLevel(
        "state> metropolitan statistical area/micropolitan statistical area> metropolitan division (or part)",
        "323",
    ),
    SummaryLevel(
        "state> metropolitan statistical area/micropolitan statistical area> metropolitan division> county",
        "324",
    ),
    SummaryLevel("combined statistical area", "330"),
    SummaryLevel("combined statistical area> state", "331"),
    SummaryLevel("combined statistical area> micropolitan statistical area", "332"),
    SummaryLevel(
        "combined statistical area> metropolitan statistical area/micropolitan statistical area> state",
        "333",
    ),
    SummaryLevel("combined new england city and town area", "335"),
    SummaryLevel("combined new england city and town area> state", "336"),
    SummaryLevel(
        "combined new england city and town area> new england city and town area", "337"
    ),
    SummaryLevel(
        "combined new england city and town area> new england city and town area> state",
        "338",
    ),
    SummaryLevel("state> combined statistical area (or part)", "340"),
    SummaryLevel(
        "state> combined statistical area> metropolitan statistical area/micropolitan statistical area (or part)",
        "341",
    ),
    SummaryLevel("state> combined new england city and town area (or part)", "345"),
    SummaryLevel(
        "state> combined new england city and town area> new england city and town area (or part)",
        "346",
    ),
    SummaryLevel("new england city and town area", "350"),
    SummaryLevel("new england city and town area> state", "351"),
    SummaryLevel("new england city and town area> state> principal city", "352"),
    SummaryLevel("new england city and town area> necta division", "355"),
    SummaryLevel("new england city and town area> necta division> state", "356"),
    SummaryLevel("state> new england city and town area (or part)", "360"),
    SummaryLevel("state> new england city and town area> place", "361"),
    SummaryLevel("state> new england city and town area> county (or part)", "362"),
    SummaryLevel(
        "state> new england city and town area> county> county subdivision", "363"
    ),
    SummaryLevel(
        "state> new england city and town area> necta division (or part)", "364"
    ),
    SummaryLevel(
        "state> new england city and town area> necta division> county (or part)", "365"
    ),
    SummaryLevel(
        "state> new england city and town area> necta division> county> county subdivision",
        "366",
    ),
    SummaryLevel("urban area", "400"),
    SummaryLevel("urban area> state", "410"),
    SummaryLevel("urban area> state> county", "430"),
    SummaryLevel("state> congressional district", "500"),
    SummaryLevel("state> congressional district> county", "510"),
    SummaryLevel("state> congressional district> county> tract", "511"),
    SummaryLevel("state> congressional district> county> county subdivision", "521"),
    SummaryLevel("state> congressional district> place", "531"),
    SummaryLevel(
        "state> congressional district> american indian area/alaska native area/hawaiian home land",
        "550",
    ),
    SummaryLevel(
        "state> congressional district> alaska native regional corporation", "560"
    ),
    SummaryLevel("state> state legislative district (upper chamber)", "610"),
    SummaryLevel("state> state legislative district (upper chamber)> county", "612"),
    SummaryLevel("state> state legislative district (lower chamber)", "620"),
    SummaryLevel(
        "state> state legislative district (lower chamber)> county (or part)", "622"
    ),
    SummaryLevel("state> public use microdata area", "795"),
    SummaryLevel("zip code tabulation area", "860"),
    SummaryLevel("state> zip code tabulation area (or part)", "871"),
    SummaryLevel("state> school district (elementary)", "950"),
    SummaryLevel("state> school district (secondary)", "960"),
    SummaryLevel("state> school district (unified)", "970"),
]


def get_summary_level_by_name(name):
    """
    Return the summary level object with this name
    """
    for sl in SUMMARY_LEVELS:
        if sl.level == name:
            return sl


def get_summary_level_by_code(code):
    """
    Return the summary level object with this code
    """
    for sl in SUMMARY_LEVELS:
        if sl.code == code:
            return sl


def surmise_summary_level(geo_list):
    """
    For a list of geographies requested, surmise which summary level is
    intended. The surmised summary level must have a 100 percent match
    with the spcification defined in `geo_list`. If multiple matches
    are found, the intended summary level is surmised based on (in
    order of priorty):

        - the match with fewest unspecified items
        - the match with the shortest (number of elements in the)summary
        level definition
        - the match with the lowest summary level `code` value

    Returns
        sl: SummaryLevel
            A summary level object that defines the expected summary area
            assumed to be intended by `geo_list`
    """
    match_stats = [sl.percent_match(geo_list) for sl in SUMMARY_LEVELS]
    candidates = [tup for tup in match_stats if tup[0] == 1.0]
    if candidates:
        # The candidate with fewest unspecified geographies is preferred
        min_unspec = min([tup[1] for tup in candidates])
        candidates = [tup for tup in candidates if tup[1] == min_unspec]
        if len(candidates) == 1:
            return candidates[0][-1]
        # If further disambiguation is needed, the simplest definition
        # of summary level is assumed
        min_length = min([tup[2] for tup in candidates])
        candidates = [tup for tup in candidates if tup[2] == min_length]
        if len(candidates) == 1:
            return candidates[0][-1]
        # If further disambiguation is nededed, the lowest summary level
        # code is assumed
        min_code = min([tup[-1].code for tup in candidates])
        candidates = [tup for tup in candidates if tup[-1].code == min_code]
        return candidates[0][-1]
    else:
        raise ValueError(
            f"No summary levels include the definitions listed in {geo_list}"
        )
